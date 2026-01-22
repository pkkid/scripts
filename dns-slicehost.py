#!/usr/bin/env python3
"""
Dynamic DNS updater for Slicehost.

This script automatically updates DNS A records on Slicehost to point to your
current external IP address. Useful for maintaining DNS records when using
dynamic IP addresses from ISPs.

Example:
  ./dns-slicehost.py --apikey abc123... --zone example.com. --record home

The script will:
  1. Detect your current external IP address (via checkip.dyndns.org)
  2. Query Slicehost API for existing DNS records
  3. Create or update the A record to the new IP address

Requirements:
  pip install pyactiveresource

References:
  http://articles.slicehost.com/2008/5/13/slicemanager-api-documentation
  http://code.google.com/p/pyactiveresource/

Author: Michael Shepanski (2009-05-01)
"""
import argparse
import logging, re, sys
from urllib.request import urlopen
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
from pyactiveresource.activeresource import ActiveResource  # type: ignore

# Default values
IP_SITE = "http://checkip.dyndns.org:8245/"
DEFAULT_LOG_FILE = "/tmp/slicehost-dns.log"

# Python Logger
log = logging.getLogger()
log.setLevel(logging.INFO)


def setup_logging(logfile):
    """ Setup logging handlers. """
    log.addHandler(RotatingFileHandler(logfile, 'a', 1048576))
    log.addHandler(StreamHandler(sys.stdout))
    for handler in log.handlers:
        format = "%(asctime)s %(levelname)-8s at %(filename)s line %(lineno)s %(message)s"
        handler.setFormatter(logging.Formatter(format))


class Zone(ActiveResource):
    _site = None


class Record(ActiveResource):
    _site = None

    
def getCurrentIP():
    """ Return the current external IP. """
    log.info("Fetching the current external IP address from: %s" % IP_SITE)
    resultHtml = urlopen(IP_SITE).read().decode('utf-8')
    currentIP = re.findall('[0-9.]+', resultHtml)[0]
    return currentIP


def getDnsRecord(zone_origin, record_name):
    """ Return the DNS Record to update. """
    dnsZones = Zone.find(origin=zone_origin)
    if (len(dnsZones) == 1):
        log.info("Found DNS Zone: %s" % dnsZones[0].to_dict())
        zoneid = dnsZones[0].id
        dnsRecords = Record.find(name=record_name, zone_id=zoneid)
        if (len(dnsRecords) == 1):
            log.info("Found DNS Record: %s" % dnsRecords[0].to_dict())
            return dnsRecords[0]
    log.error("Can't find Record '%s' via SliceHost API" % record_name)
    sys.exit(1)


def updateDnsRecord(zone_origin, record_name):
    """ Update the SliceHost DNS. """
    recordName = "%s.%s" % (record_name, zone_origin)
    currentIP = getCurrentIP(IP_SITE)
    dnsRecord = getDnsRecord(zone_origin, record_name)
    if (currentIP != dnsRecord.data):
        log.info("Updating DNS Record for '%s' to: %s" % (recordName, currentIP))
        dnsRecord.data = currentIP
        dnsRecord.save()
        log.info("DNS Update Successful!\n")
    else:
        log.info("DNS Record for '%s' already at: %s\n" % (recordName, currentIP))
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update Slicehost DNS A record to current external IP address.')
    parser.add_argument('--apikey', required=True, help='Slicehost API key for your account')
    parser.add_argument('--zone', required=True, help='Zone origin (e.g., example.com.)')
    parser.add_argument('--record', required=True, help='Record name to update (e.g., home)')
    parser.add_argument('--logfile', default=DEFAULT_LOG_FILE, help='Log file path (default: %(default)s)')
    args = parser.parse_args()
    api_site = "https://%s@api.slicehost.com/" % args.apikey
    Zone._site = api_site
    Record._site = api_site
    setup_logging(args.logfile)
    updateDnsRecord(args.zone, args.record)
