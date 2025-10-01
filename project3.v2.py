#!/usr/bin/env python3
"""
ip_checker_advanced.py
Improved IP checking utility with manual override, mock data, selectable fields,
periodic checking, and history logging.

Usage examples:
  # Run once, default behavior (live API)
  python ip_checker_advanced.py

  # Run once using a manual IP value (useful to simulate)
  python ip_checker_advanced.py --manual-ip 1.2.3.4 --fields ip,city,region,country,isp

  # Monitor every 60s for 10 checks and save history
  python ip_checker_advanced.py --interval 60 --count 10 --save-history ip_history.csv

  # Use a mock JSON file instead of calling the API (for testing)
  python ip_checker_advanced.py --mock sample_mock.json

  # Display all available fields (comma-separated)
  python ip_checker_advanced.py --fields ip,version,city,region,country,country_code,latitude,longitude,timezone,isp,asn
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime

import requests

API_URL = "https://ipapi.co/json/"

# Default ordered fields and friendly labels
FIELD_LABELS = {
    "ip": "Public IP Address",
    "version": "IP Version",
    "city": "City",
    "region": "Region",
    "country": "Country",
    "country_code": "Country Code",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "timezone": "Timezone",
    "isp": "ISP / Provider",
    "asn": "ASN",
    "org": "Organization",  # fallback if org present
}


def fetch_live(api_url=API_URL, timeout=10):
    r = requests.get(api_url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def load_mock(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_data(data):
    """Return a normalized dictionary with keys similar to FIELD_LABELS"""
    normalized = {}
    ip = data.get("ip") or data.get("query") or data.get("ip_address")
    normalized["ip"] = ip
    normalized["version"] = "IPv6" if ip and ":" in ip else "IPv4"
    # many APIs use slightly different keys; try a few common ones
    normalized["city"] = data.get("city")
    normalized["region"] = data.get("region") or data.get("region_name")
    normalized["country"] = data.get("country_name") or data.get("country")
    normalized["country_code"] = data.get("country") or data.get("country_code")
    # latitude/longitude sometimes nested or named lat/lon
    normalized["latitude"] = data.get("latitude") or data.get("lat")
    normalized["longitude"] = data.get("longitude") or data.get("lon") or data.get("lng")
    normalized["timezone"] = data.get("timezone")
    # org / isp keys
    normalized["isp"] = data.get("org") or data.get("isp")
    normalized["asn"] = data.get("asn") or data.get("as")
    normalized["org"] = data.get("org")
    return normalized


def print_selected(data, fields):
    print("\n========== Public IP Address Information ==========")
    for f in fields:
        label = FIELD_LABELS.get(f, f)
        print(f"{label:20}: {data.get(f) if data.get(f) is not None else 'N/A'}")
    print("===================================================\n")


def append_history_csv(path, fields, data):
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["timestamp"] + fields)
        if not file_exists:
            writer.writeheader()
        row = {"timestamp": datetime.utcnow().isoformat() + "Z"}
        for f in fields:
            row[f] = data.get(f)
        writer.writerow(row)


def parse_args():
    parser = argparse.ArgumentParser(description="IP Checker - advanced options")
    parser.add_argument("--mock", help="Path to mock JSON file to use instead of calling the API")
    parser.add_argument("--manual-ip", help="Manually override the IP value to simulate results")
    parser.add_argument("--fields",
                        help="Comma-separated list of fields to display (default: ip,version,city,region,country,isp,asn)",
                        default="ip,version,city,region,country,isp,asn")
    parser.add_argument("--interval", type=int, default=0,
                        help="Interval in seconds to re-run checks (0 = run once)")
    parser.add_argument("--count", type=int, default=1,
                        help="How many times to run (default 1). Use with --interval for periodic runs.")
    parser.add_argument("--save-history", metavar="FILE",
                        help="Append history to CSV file")
    parser.add_argument("--api-url", default=API_URL, help="API endpoint to use")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP request timeout seconds")
    parser.add_argument("--no-print-time", action="store_true", help="Don't print the timestamp before each check")
    return parser.parse_args()


def main():
    args = parse_args()

    # Prepare fields list
    fields = [f.strip() for f in args.fields.split(",") if f.strip()]
    if not fields:
        print("No fields specified. Exiting.")
        sys.exit(1)

    run_count = 0
    while run_count < args.count:
        try:
            if not args.no_print_time:
                print(f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] Running check ({run_count + 1}/{args.count})")

            # get data from mock or live
            if args.mock:
                data_raw = load_mock(args.mock)
            else:
                data_raw = fetch_live(api_url=args.api_url, timeout=args.timeout)

            data = normalize_data(data_raw)

            # If manual-ip provided, override the ip field and recalc version
            if args.manual_ip:
                data["ip"] = args.manual_ip
                data["version"] = "IPv6" if ":" in args.manual_ip else "IPv4"

            # print selected fields
            print_selected(data, fields)

            # save history if requested
            if args.save_history:
                append_history_csv(args.save_history, fields, data)
                print(f"✅ Appended to history: {args.save_history}")

        except requests.RequestException as re:
            print("❌ Network/API error:", re)
        except FileNotFoundError as fnfe:
            print("❌ Mock file not found:", fnfe)
            break
        except json.JSONDecodeError as jde:
            print("❌ Mock file or API returned invalid JSON:", jde)
            break
        except Exception as e:
            print("❌ Unexpected error:", e)

        run_count += 1
        if run_count >= args.count:
            break

        # Sleep only if we will run again
        if args.interval > 0:
            time.sleep(args.interval)
        else:
            # no interval but more runs requested -> avoid busy loop
            time.sleep(1)

    print("Done.")


if __name__ == "__main__":
    main()

