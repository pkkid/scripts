#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command line interface for testing internet bandwidth using speedtest.net.

This script tests internet connection speed by measuring download and upload
speeds using the speedtest.net infrastructure. It can output results in
various formats and supports server selection.

Examples:
  ./speedtest.py
  ./speedtest.py --simple
  ./speedtest.py --list
  ./speedtest.py --server 1234

Options:
  --simple         Show simplified output
  --list           Display available speedtest.net servers
  --server <id>    Specify a server ID to test against
  --share          Generate and provide a URL to a speedtest.net share result
  --json           Output results in JSON format
  --csv            Output results in CSV format
  --version        Show version number

Copyright 2012-2015 Matt Martz
Licensed under the Apache License, Version 2.0
"""
import os, re, sys, math
import signal, socket, timeit
import platform, threading
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request, HTTPError, URLError
from http.client import HTTPConnection, HTTPSConnection
from queue import Queue
from urllib.parse import urlparse, parse_qs
from hashlib import md5
from argparse import ArgumentParser as ArgParser

__version__ = '0.3.4'

# Global configuration
user_agent = None           # User-Agent string for HTTP requests
source = None               # Source IP address to bind to
shutdown_event = None       # Threading event for graceful shutdown
scheme = 'http'             # HTTP or HTTPS protocol
socket_socket = socket.socket  # Original socket function for bound_interface
print_ = print              # Alias for print function


class SpeedtestCliServerListError(Exception):
    """ Internal exception to signal moving to next server list URL """
    pass


def bound_socket(*args, **kwargs):
    """ Bind socket to a specified source IP address """
    global source
    sock = socket_socket(*args, **kwargs)
    sock.bind((source, 0))
    return sock


def distance(origin, destination):
    """ Calculate distance between two geographic coordinates using Haversine formula
        Args:
            origin: Tuple of (latitude, longitude)
            destination: Tuple of (latitude, longitude)
        Returns distance in kilometers
    """
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # Earth's radius in km
    # Convert to radians and calculate deltas
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    # Haversine formula
    a = (math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def build_user_agent():
    """ Build a Mozilla/5.0 compatible User-Agent string. """
    global user_agent
    # Return cached value if already built
    if user_agent:
        return user_agent
    # Build user agent from system information
    ua_tuple = (
        'Mozilla/5.0',
        '(%s; U; %s; en-us)' % (platform.system(), platform.architecture()[0]),
        'Python/%s' % platform.python_version(),
        '(KHTML, like Gecko)',
        'speedtest-cli/%s' % __version__
    )
    user_agent = ' '.join(ua_tuple)
    return user_agent


def build_request(url, data=None, headers={}):
    """ Build a urllib request object with automatic User-Agent header
        Args:
            url: URL string (may start with ':' for relative URLs)
            data: Optional POST data
            headers: Optional additional headers
        Returns request object ready for urlopen()
    """
    # Add scheme if URL is relative (starts with ':')
    if url[0] == ':':
        schemed_url = '%s%s' % (scheme, url)
    else:
        schemed_url = url
    headers['User-Agent'] = user_agent
    return Request(schemed_url, data=data, headers=headers)


def catch_request(request):
    """ Execute HTTP request and catch common connection exceptions
        Args:
            request: Request object
        Returns Tuple of (response_handle, error) where error is False on success
    """
    try:
        uh = urlopen(request)
        return uh, False
    except (HTTPError, URLError, socket.error):
        e = sys.exc_info()[1]
        return None, e


class FileGetter(threading.Thread):
    """ Thread class for downloading data from a URL for speed testing """

    def __init__(self, url, start):
        self.url = url
        self.result = None
        self.starttime = start
        threading.Thread.__init__(self)

    def run(self):
        """ Download data in 10KB chunks for 10 seconds """
        self.result = [0]
        try:
            # Only run for 10 seconds
            if (timeit.default_timer() - self.starttime) <= 10:
                request = build_request(self.url)
                f = urlopen(request)
                # Read in 10KB chunks until done or shutdown
                while not shutdown_event.is_set():
                    chunk_size = len(f.read(10240))
                    self.result.append(chunk_size)
                    if chunk_size == 0:
                        break
                f.close()
        except IOError:
            pass


def downloadSpeed(files, quiet=False):
    """ Launch multiple download threads and calculate total download speed
        Args:
            files: List of URLs to download
            quiet: If True, suppress progress dots
        Returns download speed in bytes per second
    """
    start = timeit.default_timer()
    finished = []

    def producer(q, files):
        """Create and queue download threads"""
        for file in files:
            thread = FileGetter(file, start)
            thread.start()
            q.put(thread, True)
            if not quiet and not shutdown_event.is_set():
                sys.stdout.write('.')
                sys.stdout.flush()

    def consumer(q, total_files):
        """ Wait for threads to complete and collect results """
        while len(finished) < total_files:
            thread = q.get(True)
            # Wait for thread to finish with timeout
            while thread.is_alive():
                thread.join(timeout=0.1)
            # Sum up all downloaded bytes from this thread
            finished.append(sum(thread.result))
            del thread
    # Create queue with max 6 concurrent threads
    q = Queue(6)
    prod_thread = threading.Thread(target=producer, args=(q, files))
    cons_thread = threading.Thread(target=consumer, args=(q, len(files)))
    # Start timing and launch threads
    start = timeit.default_timer()
    prod_thread.start()
    cons_thread.start()
    # Wait for both threads to complete
    while prod_thread.is_alive():
        prod_thread.join(timeout=0.1)
    while cons_thread.is_alive():
        cons_thread.join(timeout=0.1)
    # Calculate bytes per second
    return sum(finished) / (timeit.default_timer() - start)


class FilePutter(threading.Thread):
    """ Thread class for uploading data to a URL for speed testing """

    def __init__(self, url, start, size):
        self.url = url
        # Generate dummy data to upload
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        data = chars * (int(round(int(size) / 36.0)))
        # Format as form data with exact size
        self.data = ('content1=%s' % data[0:int(size) - 9]).encode()
        del data
        self.result = None
        self.starttime = start
        threading.Thread.__init__(self)

    def run(self):
        """ Upload data within 10 second window """
        try:
            # Only upload if within 10 second test window
            if ((timeit.default_timer() - self.starttime) <= 10
              and not shutdown_event.is_set()):
                request = build_request(self.url, data=self.data)
                f = urlopen(request)
                f.read(11)  # Read response
                f.close()
                self.result = len(self.data)
            else:
                self.result = 0
        except IOError:
            self.result = 0


def uploadSpeed(url, sizes, quiet=False):
    """ Function to launch FilePutter threads and calculate upload speeds """
    start = timeit.default_timer()
    finished = []

    def producer(q, sizes):
        for size in sizes:
            thread = FilePutter(url, start, size)
            thread.start()
            q.put(thread, True)
            if not quiet and not shutdown_event.is_set():
                sys.stdout.write('.')
                sys.stdout.flush()

    def consumer(q, total_sizes):
        while len(finished) < total_sizes:
            thread = q.get(True)
            while thread.is_alive():
                thread.join(timeout=0.1)
            finished.append(thread.result)
            del thread

    q = Queue(6)
    prod_thread = threading.Thread(target=producer, args=(q, sizes))
    cons_thread = threading.Thread(target=consumer, args=(q, len(sizes)))
    start = timeit.default_timer()
    prod_thread.start()
    cons_thread.start()
    while prod_thread.is_alive():
        prod_thread.join(timeout=0.1)
    while cons_thread.is_alive():
        cons_thread.join(timeout=0.1)
    return (sum(finished) / (timeit.default_timer() - start))


def getConfig():
    """ Download speedtest.net configuration containing client info and test parameters
        Returns: Dictionary with 'client', 'times', 'download', and 'upload' configuration
    """
    # Fetch configuration XML from speedtest.net
    request = build_request('://www.speedtest.net/speedtest-config.php')
    uh, e = catch_request(request)
    if e:
        print_('Could not retrieve speedtest.net configuration: %s' % e)
        sys.exit(1)
    # Read response in chunks
    configxml = []
    while True:
        configxml.append(uh.read(10240))
        if len(configxml[-1]) == 0:
            break
    if int(uh.code) != 200:
        return None
    uh.close()
    # Parse XML and extract configuration
    try:
        root = ET.fromstring(''.encode().join(configxml))
        config = {
            'client': root.find('client').attrib,
            'times': root.find('times').attrib,
            'download': root.find('download').attrib,
            'upload': root.find('upload').attrib
        }
    except SyntaxError:
        print_('Failed to parse speedtest.net configuration')
        sys.exit(1)
    del root
    del configxml
    return config


def closestServers(client, all=False):
    """ Find closest speedtest.net servers based on geographic distance
        Args:
            client: Client configuration dictionary with 'lat' and 'lon'
            all: If True, return all servers; if False, return only 5 closest
        Returns List of server dictionaries sorted by distance
    """
    # Try multiple URLs for server list (fallback if one fails)
    urls = [
        '://www.speedtest.net/speedtest-servers-static.php',
        '://c.speedtest.net/speedtest-servers-static.php',
        '://www.speedtest.net/speedtest-servers.php',
        '://c.speedtest.net/speedtest-servers.php',
    ]
    errors = []
    servers = {}  # Dictionary keyed by distance
    for url in urls:
        try:
            request = build_request(url)
            uh, e = catch_request(request)
            if e:
                errors.append('%s' % e)
                raise SpeedtestCliServerListError
            serversxml = []
            while 1:
                serversxml.append(uh.read(10240))
                if len(serversxml[-1]) == 0:
                    break
            if int(uh.code) != 200:
                uh.close()
                raise SpeedtestCliServerListError
            uh.close()
            # Parse XML server list
            try:
                root = ET.fromstring(''.encode().join(serversxml))
                elements = root.iter('server')
            except SyntaxError:
                raise SpeedtestCliServerListError
            # Calculate distance to each server
            for server in elements:
                attrib = server.attrib
                d = distance([float(client['lat']), float(client['lon'])],
                             [float(attrib.get('lat')), float(attrib.get('lon'))])
                attrib['d'] = d
                # Group servers by distance
                if d not in servers:
                    servers[d] = [attrib]
                else:
                    servers[d].append(attrib)
            del root
            del serversxml
            del elements
        except SpeedtestCliServerListError:
            continue
        # We were able to fetch and parse the list of speedtest.net servers
        if servers:
            break
    if not servers:
        print_('Failed to retrieve list of speedtest.net servers:\n\n %s' %
               '\n'.join(errors))
        sys.exit(1)
    closest = []
    for d in sorted(servers.keys()):
        for s in servers[d]:
            closest.append(s)
            if len(closest) == 5 and not all:
                break
        else:
            continue
        break
    del servers
    return closest


def getBestServer(servers):
    """ Test latency to multiple servers and return the fastest one
        Args:
            servers: List of server dictionaries to test
        Returns server dictionary with lowest latency (includes 'latency' key)
    """
    results = {}
    # Test latency to each server
    for server in servers:
        cum = []  # Cumulative latency measurements
        url = '%s/latency.txt' % os.path.dirname(server['url'])
        urlparts = urlparse(url)
        # Perform 3 latency tests per server
        for i in range(0, 3):
            try:
                if urlparts[0] == 'https':
                    h = HTTPSConnection(urlparts[1])
                else:
                    h = HTTPConnection(urlparts[1])
                headers = {'User-Agent': user_agent}
                start = timeit.default_timer()
                h.request("GET", urlparts[2], headers=headers)
                r = h.getresponse()
                total = (timeit.default_timer() - start)
            except (HTTPError, URLError, socket.error):
                cum.append(3600)
                continue
            text = r.read(9)
            # Verify valid response
            if int(r.status) == 200 and text == 'test=test'.encode():
                cum.append(total)
            else:
                cum.append(3600)  # Penalty for failed test
            h.close()
        # Calculate average latency in milliseconds
        avg = round((sum(cum) / 6) * 1000, 3)
        results[avg] = server
    # Find server with lowest latency
    fastest = sorted(results.keys())[0]
    best = results[fastest]
    best['latency'] = fastest

    return best


def ctrl_c(signum, frame):
    """ Handle Ctrl-C by setting shutdown event for graceful thread termination """
    global shutdown_event
    shutdown_event.set()
    raise SystemExit('\nCancelling...')


def version():
    """ Print version and exit """
    raise SystemExit(__version__)


def speedtest(args):
    """Run the complete speedtest.net bandwidth test"""
    global shutdown_event, source, scheme
    shutdown_event = threading.Event()
    signal.signal(signal.SIGINT, ctrl_c)
    # Configure socket timeout
    socket.setdefaulttimeout(args.timeout)
    # Build and cache User-Agent string
    build_user_agent()
    # Bind to specific source IP if specified
    if args.source:
        source = args.source
        socket.socket = bound_socket
    # Use HTTPS if requested
    if args.secure:
        scheme = 'https'
    if not args.simple:
        print_('Retrieving speedtest.net configuration...')
    try:
        config = getConfig()
    except URLError:
        print_('Cannot retrieve speedtest configuration')
        sys.exit(1)
    # Retrieve server list
    if not args.simple:
        print_('Retrieving speedtest.net server list...')
    if args.list or args.server:
        # Get all servers if listing or selecting specific server
        servers = closestServers(config['client'], True)
        if args.list:
            # Print server list and exit
            serverList = []
            for server in servers:
                line = ('%(id)4s) %(sponsor)s (%(name)s, %(country)s) '
                        '[%(d)0.2f km]' % server)
                serverList.append(line)
            print_('\n'.join(serverList).encode('utf-8', 'ignore'))
            sys.exit(0)
    else:
        # Get only 5 closest servers
        servers = closestServers(config['client'])
    if not args.simple:
        print_('Testing from %(isp)s (%(ip)s)...' % config['client'])
    if args.server:
        try:
            best = getBestServer(filter(lambda x: x['id'] == args.server, servers))
        except IndexError:
            print_('Invalid server ID')
            sys.exit(1)
    elif args.mini:
        name, ext = os.path.splitext(args.mini)
        if ext:
            url = os.path.dirname(args.mini)
        else:
            url = args.mini
        urlparts = urlparse(url)
        try:
            request = build_request(args.mini)
            f = urlopen(request)
        except Exception:
            print_('Invalid Speedtest Mini URL')
            sys.exit(1)
        else:
            text = f.read()
            f.close()
        extension = re.findall('upload_extension: "([^"]+)"', text.decode())
        if not extension:
            for ext in ['php', 'asp', 'aspx', 'jsp']:
                try:
                    request = build_request('%s/speedtest/upload.%s' %
                                            (args.mini, ext))
                    f = urlopen(request)
                except Exception:
                    pass
                else:
                    data = f.read().strip()
                    if (f.code == 200 and len(data.splitlines()) == 1
                      and re.match('size=[0-9]', data)):
                        extension = [ext]
                        break
        if not urlparts or not extension:
            print_('Please provide the full URL of your Speedtest Mini server')
            sys.exit(1)
        servers = [{
            'sponsor': 'Speedtest Mini',
            'name': urlparts[1],
            'd': 0,
            'url': '%s/speedtest/upload.%s' % (url.rstrip('/'), extension[0]),
            'latency': 0,
            'id': 0
        }]
        try:
            best = getBestServer(servers)
        except Exception:
            best = servers[0]
    else:
        if not args.simple:
            print_('Selecting best server based on latency...')
        best = getBestServer(servers)

    if not args.simple:
        print_(('Hosted by %(sponsor)s (%(name)s) [%(d)0.2f km]: '
               '%(latency)s ms' % best).encode('utf-8', 'ignore'))
    else:
        print_('Ping: %(latency)s ms' % best)
    # Prepare download test URLs (various image sizes, 4 of each)
    sizes = [350, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
    urls = []
    for size in sizes:
        for i in range(0, 4):
            urls.append('%s/random%sx%s.jpg' % (os.path.dirname(best['url']), size, size))
    # Run download test
    if not args.simple:
        print_('Testing download speed', end='')
    dlspeed = downloadSpeed(urls, args.simple)
    if not args.simple:
        print_()
    print_('Download: %0.2f M%s/s' % ((dlspeed / 1000 / 1000) * args.units[1], args.units[0]))
    # Prepare upload test sizes (25 uploads each of 250KB and 500KB)
    sizesizes = [int(.25 * 1000 * 1000), int(.5 * 1000 * 1000)]
    sizes = []
    for size in sizesizes:
        for i in range(0, 25):
            sizes.append(size)
    # Run upload test
    if not args.simple:
        print_('Testing upload speed', end='')
    ulspeed = uploadSpeed(best['url'], sizes, args.simple)
    if not args.simple:
        print_()
    print_('Upload: %0.2f M%s/s' % ((ulspeed / 1000 / 1000) * args.units[1], args.units[0]))
    # Generate shareable results image URL
    if args.share and args.mini:
        print_('Cannot generate a speedtest.net share results image while '
               'testing against a Speedtest Mini server')
    elif args.share:
        # Convert speeds to kbps for API
        dlspeedk = int(round((dlspeed / 1000) * 8, 0))
        ping = int(round(best['latency'], 0))
        ulspeedk = int(round((ulspeed / 1000) * 8, 0))
        # Build API request to submit results
        # Note: List order matters for API
        # API expects parameters in specific order
        apiData = [
            'download=%s' % dlspeedk,
            'ping=%s' % ping,
            'upload=%s' % ulspeedk,
            'promo=',
            'startmode=%s' % 'pingselect',
            'recommendedserverid=%s' % best['id'],
            'accuracy=%s' % 1,
            'serverid=%s' % best['id'],
            'hash=%s' % md5(('%s-%s-%s-%s' % (ping, ulspeedk, dlspeedk, '297aae72')).encode()).hexdigest()]
        headers = {'Referer': 'http://c.speedtest.net/flash/speedtest.swf'}
        request = build_request('://www.speedtest.net/api/api.php', data='&'.join(apiData).encode(), headers=headers)
        f, e = catch_request(request)
        if e:
            print_('Could not submit results to speedtest.net: %s' % e)
            sys.exit(1)
        response = f.read()
        code = f.code
        f.close()
        if int(code) != 200:
            print_('Could not submit results to speedtest.net')
            sys.exit(1)
        qsargs = parse_qs(response.decode())
        resultid = qsargs.get('resultid')
        if not resultid or len(resultid) != 1:
            print_('Could not submit results to speedtest.net')
            sys.exit(1)
        print_('Share results: %s://www.speedtest.net/result/%s.png' %
               (scheme, resultid[0]))


if __name__ == '__main__':
    try:
        description = (
            'Command line interface for testing internet bandwidth using speedtest.net.\n'
            '--------------------------------------------------------------------------\n'
            'https://github.com/sivel/speedtest-cli')
        parser = ArgParser(description=description)
        parser.add_argument('--bytes', dest='units', action='store_const', const=('byte', 1), default=('bit', 8),
            help='Display values in bytes instead of bits. Does not affect the image generated by --share')  # noqa
        parser.add_argument('--share', action='store_true', help='Generate and provide a URL to the speedtest.net share results image')  # noqa
        parser.add_argument('--simple', action='store_true', help='Suppress verbose output, only show basic information')  # noqa
        parser.add_argument('--list', action='store_true', help='Display a list of speedtest.net servers sorted by distance')  # noqa
        parser.add_argument('--server', help='Specify a server ID to test against')  # noqa
        parser.add_argument('--mini', help='URL of the Speedtest Mini server')  # noqa
        parser.add_argument('--source', help='Source IP address to bind to')  # noqa
        parser.add_argument('--timeout', default=10, type=int, help='HTTP timeout in seconds. Default 10')  # noqa
        parser.add_argument('--secure', action='store_true', help='Use HTTPS instead of HTTP when communicating with speedtest.net operated servers')  # noqa
        parser.add_argument('--version', action='store_true', help='Show the version number and exit')  # noqa
        options = parser.parse_args()
        if isinstance(options, tuple):
            args = options[0]
        else:
            args = options
        del options
        # Handle version flag
        if args.version:
            version()
        speedtest(args)
    except KeyboardInterrupt:
        print_('\nCancelling...')
