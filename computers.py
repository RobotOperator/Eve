#!/bin/env python3
import subprocess
import argparse
import base64, json, os
import urllib3
import requests
from auth import auth_token, create_server_string

#web request
def get_computers(base_url, bearer_token, search_string):
    updated_string = '*' + search_string + '*'
    url = f"{base_url}/JSSResource/computers/match/{updated_string}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return json.loads(response.text)

#Used to get more details about a computer using a supplied udid
def get_computer_by_udid(base_url, bearer_token, udid):
    url = f"{base_url}/JSSResource/computers/udid/{udid}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return json.loads(response.text)

#Used to get more details about a computer using a supplied udid
def get_computer_by_id(base_url, bearer_token, id):
    url = f"{base_url}/JSSResource/computers/id/{id}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return json.loads(response.text)

#Used to get computer policy logs  using a supplied udid
def get_policy_logs_by_udid(base_url, bearer_token, udid):
    url = f"{base_url}/JSSResource/computerhistory/udid/{udid}/subset/policy_logs"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return json.loads(response.text)


def main():
    #Create arg parser
    parser = argparse.ArgumentParser(description="Accepts authentication values for JAMF")

    parser.add_argument('--username', type=str, help="The username for authentication.")
    parser.add_argument('--password', type=str, help="The password for authentication.")
    parser.add_argument('--basic_auth', type=str, help="The base64 basic auth token for authentication.")
    parser.add_argument('--bearer_token', type=str, help="A bearer token to use for authentication.")
    parser.add_argument('--jamf_server', type=str, help="The URL of the target JAMF server.")
    parser.add_argument('--search_for_computer_by_string', type=str, help="Uses a supplied string to find macs that have attributes such as name or user which match the value.")
    parser.add_argument('--api_port', type=str, help="The port of the JAMF server API to communicate with.")
    parser.add_argument('--get_computer_by_udid', type=str, help="Retrieves the full details of a macOS device specified by the device UDID.")
    parser.add_argument('--get_computer_by_id', type=str, help="Retrieves the full details of a macOS device specified by the device ID.")
    parser.add_argument('--get_policy_logs_by_udid', type=str, help="Retrieves the policy logs for a computer specified by UDID.")
    args = parser.parse_args()

    if not os.path.isdir('./.data'):
        os.makedirs('./.data')
        print("[i] - Directory .data created in current folder. -[i]")

    #Create jamf server string
    jamf_sstring = create_server_string(args)

    #Get our web request bearer token
    if args.bearer_token:
        bearer_token = args.bearer_token
    else:
        bearer_string = auth_token(jamf_sstring, args)
        if 'token' not in bearer_string:
            print("X- Failed to retrieve token. Please check your credentials. -X")
            return 1

        #JSON parsing the output
        with open('./.data/token', 'w') as out:
            out.write(bearer_string)
        data = json.loads(bearer_string)
        bearer_token = data.get('token')

    #Perform action based on supplied argument
    if args.search_for_computer_by_string:
        print(json.dumps(get_computers(jamf_sstring, bearer_token, args.search_for_computer_by_string), indent=2))
    elif args.get_computer_by_udid:
        print(json.dumps(get_computer_by_udid(jamf_sstring, bearer_token, args.get_computer_by_udid), indent=2))
    elif args.get_computer_by_id:
        print(json.dumps(get_computer_by_id(jamf_sstring, bearer_token, args.get_computer_by_id), indent=2))
    elif args.get_policy_logs_by_udid:
        print(json.dumps(get_policy_logs_by_udid(jamf_sstring, bearer_token, args.get_policy_logs_by_udid), indent=2))
    else:
        raise Exception("X - Missing args, Either search_string or a computer UDID must be supplied - X")

if __name__ == "__main__":
    main()
