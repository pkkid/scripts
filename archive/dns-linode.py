#!/usr/bin/env python3
"""
Dynamic DNS updater for Linode.

This script automatically updates DNS A records on Linode to point to your
current external IP address. Useful for maintaining DNS records when using
dynamic IP addresses from ISPs.

Usage:
  ./dns-linode.py --apikey <key> --domain <domain> --record <record>

The script will:
  1. Detect your current external IP address (via checkip.dyndns.org)
  2. Query Linode API for existing DNS records
  3. Create or update the A record to the new IP address

Requirements:
  Generate an API key at: https://cloud.linode.com/profile/tokens
  pip install linode-python

References:
  http://atxconsulting.com/content/linode-api-bindings
  https://github.com/tjfontaine/linode-python/

Author: Michael Shepanski (2010-01-17)
"""
import argparse
import re
from urllib.request import urlopen
from linode import api  # type: ignore

CHECKIP = "http://checkip.dyndns.org:8245/"


def get_extenral_ip():
    """ Return the current external IP. """
    print("Fetching external IP from: %s" % CHECKIP)
    html = urlopen(CHECKIP).read().decode('utf-8')
    external_ip = re.findall('[0-9.]+', html)[0]
    print("Found external IP: %s" % external_ip)
    return external_ip


def set_dns_target(apikey, domain, record, target):
    """ Update the domain's DNS record with the specified target. """
    linode = api.Api(apikey)
    for dom in linode.domain_list():
        if dom['DOMAIN'] == domain:
            # Check the DNS Entry already exists
            for rec in linode.domain_resource_list(domainid=dom['DOMAINID']):
                if rec['NAME'] == record:
                    if rec['TARGET'] == target:
                        # DNS Entry Already at the correct value
                        print("Entry '%s:%s' already set to '%s'." % (domain, record, target))
                        return rec['RESOURCEID']
                    else:
                        # DNS Entry found; Update it
                        print("Updating entry '%s:%s' target to %s." % (domain, record, target))
                        return linode.domain_resource_update(domainid=dom['DOMAINID'],
                            resourceid=rec['RESOURCEID'], target=target)
            # DNS Entry not found; Create it
            print("Creating entry '%s:%s' target as %s." % (domain, record, target))
            return linode.domain_resource_create(domainid=dom['DOMAINID'],
                name=record, type='A', target=target, ttl_sec=3600)
    print("Error: Domain %s not found." % domain)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update Linode DNS A record to current external IP address.')  # noqa
    parser.add_argument('--apikey', required=True, help='Linode API key (generate at https://cloud.linode.com/profile/tokens)')  # noqa
    parser.add_argument('--domain', required=True, help='Domain name to update (e.g., example.com)')  # noqa
    parser.add_argument('--record', required=True, help='Record name to update (e.g., home)')  # noqa
    parser.add_argument('--checkip', default=CHECKIP, help='URL to check external IP (default: %(default)s)')  # noqa
    args = parser.parse_args()
    external_ip = get_extenral_ip()
    set_dns_target(args.apikey, args.domain, args.record, external_ip)
    print("Done.")
