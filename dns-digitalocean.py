#!/usr/bin/env python
"""
Dynamic DNS updater for DigitalOcean.

This script automatically updates DNS A records on DigitalOcean to point to
your current external IP address. Useful for maintaining DNS records when
using dynamic IP addresses from ISPs.

Examples:
  ./dns-digitalocean.py -t dop_v1_abc123... -d example.com -r home
  ./dns-digitalocean.py -t dop_v1_abc123... -d example.com -r home,vpn,server
  ./dns-digitalocean.py -t dop_v1_abc123... -d example.com -r home --ip 192.0.2.1

Options:
  -t, --token <token>     DigitalOcean API token (required)
  -d, --domain <domain>   Domain name to update (required)
  -r, --records <names>   Comma-separated list of record names to update (required)
  --rtype <type>          Record type to update (default: A)
  --ip <address>          Set to specific IP address (default: auto-detect external IP)

The script will:
  1. Detect your current external IP address (via checkip.dyndns.org)
  2. Query DigitalOcean API for existing DNS records
  3. Update matching records to the new IP address

API Token:
  Generate an API token at: https://cloud.digitalocean.com/account/api/tokens

Author: Michael Shepanski (2024-04-04)
"""
import argparse
import re
import requests

APIURL = 'https://api.digitalocean.com'
GETIPURL = 'https://cloudflare.com/cdn-cgi/trace'


def get_extenral_ip():
    """ Return the current external IP. """
    print(f'GET {GETIPURL}')
    resp = requests.get(GETIPURL)
    resp.raise_for_status()
    return re.findall(r'[0-9.]+', resp.content.decode())[0]


def update_records(session, domain, names, ipaddr, rtype='A'):
    """ Get the record for the specified domain. """
    url = f'{APIURL}/v2/domains/{domain}/records'
    print(f'GET {url}')
    resp = session.get(url)
    resp.raise_for_status()
    for record in resp.json()['domain_records']:
        if record['name'] in names and record['type'] == rtype:
            update_record(session, domain, record, ipaddr)


def update_record(session, domain, record, ipaddr):
    """ Update the record to the specified IP address. """
    recid = record['id']
    url = f'{APIURL}/v2/domains/{domain}/records/{recid}'
    data = {'type': record['type'], 'data': ipaddr}
    print(f'PUT {url} {record["name"]} {data}')
    resp = session.put(url, json=data)
    resp.raise_for_status()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update DNS record on Digital Ocean')
    parser.add_argument('-t', '--token', required=True, help='Digital Ocean API Token')
    parser.add_argument('-d', '--domain', required=True, help='Update the specified domain')
    parser.add_argument('-r', '--records', required=True, help='Update the specified records')
    parser.add_argument('--rtype', default='A', help='Update the specified record type')
    parser.add_argument('--ip', help='Set to the specified IP address')
    opts = parser.parse_args()
    names = opts.records.split(',')
    # Update the Domain Record
    print('---')
    session = requests.Session()
    session.headers.update({'Authorization': f'Bearer {opts.token}'})
    ipaddr = opts.ip or get_extenral_ip()
    update_records(session, opts.domain, names, ipaddr)
    print('Success!')
