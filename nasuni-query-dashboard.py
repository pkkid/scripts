#!/usr/bin/python
"""
Query the Nasuni Dashboard for live and analytics data.

This script authenticates with the Nasuni Dashboard and executes SQL-like queries
against either the live database or analytics database. Results are returned as
JSON for further processing.

Usage:
  ./nasuni-query-dashboard.py -u <username> -p <password> -l <live_query>
  ./nasuni-query-dashboard.py -u <username> -p <password> -a <analytics_query>

Examples:
  ./nasuni-query-dashboard.py -u user@example.com -p secret -l "SELECT * FROM filers WHERE status='active'"
  ./nasuni-query-dashboard.py -u user@example.com -p secret -a "SELECT volume, sum(size) FROM usage GROUP BY volume"

Requirements:
  pip install requests

Note: Queries follow standard SQL syntax. Results are printed as JSON.
"""
import argparse, json, requests

URL_LOGIN = 'https://account.nasuni.com/account/login/'
URL_QUERY = 'https://account.nasuni.com/dashboard/reports/custom/'


def get_dashboard_session(username, password):
    # Create session and send initial GET to create the cookie
    session = requests.Session()
    response = session.get(URL_LOGIN)
    # Login to the Dashboard
    data = {'username':username, 'password':password, 'csrfmiddlewaretoken':session.cookies['csrftoken']}
    response = session.post(URL_LOGIN, data=data, headers={'Referer': URL_LOGIN})
    if 'Welcome back' not in response.text:
        raise SystemExit('Invalid username or password.')
    return session


def run_query(session, live, analytics):
    data = {'action':'run', 'csrfmiddlewaretoken':session.cookies['csrftoken'],
        'query_live':live, 'query_analytics':analytics}
    response = session.post(URL_QUERY, data=data, headers={'Referer': URL_QUERY})
    return json.loads(response.text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch resize images.')
    parser.add_argument('-u', '--username', help='Nasuni dashboard username.')
    parser.add_argument('-p', '--password', help='Nasuni dashboard password.')
    parser.add_argument('-l', '--live', help='Live database query.')
    parser.add_argument('-a', '--analytics', help='Analytics database query.')
    # Run query from command line
    args = parser.parse_args()
    session = get_dashboard_session(args.username, args.password)
    results = run_query(session, args.live, args.analytics)
    print(results)
