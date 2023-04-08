# Cloduflare DNS updater script
# Author: dan5py
# License: MIT


## !!! IMPORTANT !!!
### You may need to install the following modules:
### - requests

import argparse
import requests
import socket
import datetime


### ARGUMENTS SECTION ###
### * You can hardcode these values or use command line arguments
email = "YOUR_EMAIL"  ## Email used to login to Cloudflare
token = "YOUR_TOKEN"  ## API token (Global or Scoped), generate it from https://dash.cloudflare.com/profile/api-tokens
zone = "YOUR_ZONE_ID"  ## Zone ID, get it from your domain dashboard page
ttl = "1"  # Time to live (seconds, 1 = auto)
verbose = False
################## *

### ? Log file stuff ###
file_format = "[{date}] ({content})"  ## Check https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-patch-dns-record for available variables
date_format = "%Y-%m-%d %H:%M:%S"
################## ?


## Cloudflare API (do not change unless you know what you are doing)
api_endpoint = "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"


class Logger:
    class Chalk:
        red = "\033[91m"
        green = "\033[92m"
        yellow = "\033[93m"
        blue = "\033[94m"
        magenta = "\033[95m"
        cyan = "\033[96m"
        white = "\033[97m"
        reset = "\033[0m"

        @staticmethod
        def colorize(text, color):
            return f"{color}{text}{Logger.Chalk.reset}"

    @staticmethod
    def log(text):
        if not verbose:
            return
        print(f"{Logger.Chalk.colorize('[LOG]', Logger.Chalk.green)} {text}")

    @staticmethod
    def info(text):
        if not verbose:
            return
        print(f"{Logger.Chalk.colorize('[INFO]', Logger.Chalk.blue)} {text}")

    @staticmethod
    def warn(text):
        if not verbose:
            return
        print(f"{Logger.Chalk.colorize('[WARN]', Logger.Chalk.yellow)} {text}")

    @staticmethod
    def error(text):
        if not verbose:
            return
        print(f"{Logger.Chalk.colorize('[ERROR]', Logger.Chalk.red)} {text}")


def parse_args():
    """Parse command line arguments

    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description="Update a DDNS record")
    parser.add_argument(
        "-e",
        "--email",
        required=True if email is None else False,
        help="The account email used to login to Cloudflare",
        default=email,
    )
    parser.add_argument("-r", "--records", required=True, nargs="+", help="The name of record(s) to update")
    parser.add_argument("-s", "--scoped", action="store_true", help="Use scoped API token")
    parser.add_argument(
        "-t", "--token", required=True if token is None else False, help="API token", default=token
    )
    parser.add_argument(
        "-z", "--zone", required=True if zone is None else False, help="Zone ID", default=zone
    )
    parser.add_argument(
        "-T",
        "--ttl",
        required=True if ttl is None else False,
        help="The TTL of the record (seconds)",
        default=ttl,
    )
    parser.add_argument(
        "-p", "--proxied", action="store_true", help="Enable Cloudflare proxy", default=False
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force update even if the IP is the same",
        default=False,
    )

    ## Log arguments
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging", default=verbose
    )
    parser.add_argument(
        "-l",
        "--log-file",
        help="Log file to write to",
        default=None,
    )

    return parser.parse_args()


def fill_endpoint(args, more_text="", more_args={}):
    """Fill the API endpoint with the given arguments

    Args:
        args (argparse.Namespace): The parsed arguments
    """
    output = f"{api_endpoint}{more_text}"

    return output.format(zone_id=args.zone, record_name=args.record, **more_args)


def fill_headers(args):
    """Fill the API headers with the given arguments

    Args:
        args (argparse.Namespace): The parsed arguments

    Returns:
        dict: The API headers
    """
    api_headers = {"X-Auth-Email": None, "X-Auth-Key": None, "Content-Type": "application/json"}
    api_headers["X-Auth-Email"] = args.email

    if args.scoped:
        api_headers.pop("X-Auth-Key")
        api_headers["Authorization"] = f"Bearer {args.token}"
    else:
        api_headers["X-Auth-Key"] = args.token

    return api_headers


def validate_ip(ip):
    """Validate an IP address

    Args:
        ip (str): The IP address to validate

    Returns:
        bool: True if the IP address is valid, False otherwise
    """
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def get_public_ip():
    """Get the public IP address of the machine

    Returns:
        str: The public IP address
    """

    sources = [
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
    ]

    for source in sources:
        try:
            res = requests.get(source).text.strip()
            if validate_ip(res):
                return res
        except Exception:
            pass

    Logger.error("Unable to get public IP address")
    exit(1)


def get_record(args):
    """Get the cloudflare record information

    Returns:
        dict: The record information
    """

    api_headers = fill_headers(args)
    api_endpoint = fill_endpoint(args, "?type=A&name={record_name}")

    try:
        res = requests.get(
            api_endpoint.format(zone_id=zone, record_name=args.record),
            headers=api_headers,
        )
        res = res.json()
    except Exception as e:
        Logger.error(f"Error: {e}")
        exit(1)

    if not res["success"]:
        Logger.error(res["errors"])
        exit(1)

    if len(res["result"]) == 0:
        Logger.error("No record found")
        exit(1)

    return res["result"][0]


def update_record(args, record, public_ip):
    """Update the cloudflare record

    Returns:
        dict: The record information
        bool: True if the record was updated, False otherwise
    """

    api_headers = fill_headers(args)
    api_endpoint = fill_endpoint(args, "/{record_id}", {"record_id": record["id"]})

    try:
        res = requests.put(
            api_endpoint,
            headers=api_headers,
            json={
                "type": "A",
                "name": args.record,
                "content": public_ip,
                "ttl": args.ttl,
                "proxied": args.proxied,
            },
        )
        res = res.json()
    except Exception as e:
        Logger.error(f"Error: {e}")
        exit(1)

    if not res["success"]:
        Logger.error(res["errors"])
        exit(1)

    return res["result"], res["success"]


def log_update(args, record, filepath, mode="w"):
    """Log the update to a file

    Args:
        args (argparse.Namespace): The parsed arguments
        record (dict): The record information
        filepath (str): The path to the log file
    """

    Logger.log(f"Saving update of {args.record} in {filepath}")

    try:
        with open(filepath, mode) as f:
            to_write = file_format.format(
                record=args.record,
                ip=record["content"],
                date=datetime.datetime.now().strftime(date_format),
                **record,
            )
            f.write(to_write)
    except Exception as e:
        Logger.error(f"Error: {e}")
        exit(1)


def main():
    global verbose
    args = parse_args()

    ## Set verbose
    verbose = args.verbose

    for i, record_name in enumerate(args.records):
        args.record = record_name
        record = get_record(args)
        public_ip = get_public_ip()
        if record["content"] == public_ip and not args.force:
            Logger.info(f"Record {record_name} is already up to date ({public_ip})")
            continue

        Logger.log(f"Updating record {record_name} to {public_ip}")
        record, success = update_record(args, record, public_ip)

        if success:
            Logger.info(f"Updated {record_name} successfully!")
        else:
            Logger.error(f"Unable to update {record_name}")
            continue

        if args.log_file:
            log_update(args, record, args.log_file, mode="w")


if __name__ == "__main__":
    main()
