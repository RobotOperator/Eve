#!/bin/env python3
import subprocess
import argparse
import base64, json, os
import urllib3
import requests
from auth import auth_token

#web request
def get_accounts(base_url, bearer_token):
    url = f"{base_url}/JSSResource/accounts"
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
def get_account_by_id(base_url, bearer_token, id):
    url = f"{base_url}/JSSResource/accounts/userid/{id}"
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
def create_account(base_url, bearer_token, filepath):

    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        raise Exception("X - File path is invalid. - X")

    url = f"{base_url}/JSSResource/accounts/userid/0"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/xml",
        "Accept": "application/json"
    }

    with open(filepath, "rb") as file:
        data = file.read()

    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, headers=headers, data=data, verify=False)
    response.raise_for_status()
    return response.text

def main():
    #Create arg parser
    parser = argparse.ArgumentParser(description="Accepts authentication values for JAMF")

    parser.add_argument('--username', type=str, help="The username for authentication.")
    parser.add_argument('--password', type=str, help="The password for authentication.")
    parser.add_argument('--basic_auth', type=str, help="The base64 basic auth token for authentication.")
    parser.add_argument('--bearer_token', type=str, help="A bearer token to use for authentication.")
    parser.add_argument('--jamf_server', required=True, type=str, help="The URL of the target JAMF server.")
    parser.add_argument('--get_accounts', action="store_true", help="Retrieves all JAMF accounts and groups from the server.")
    parser.add_argument('--api_port', type=str, required=True, help="The port of the JAMF server API to communicate with.")
    parser.add_argument('--create_account', type=str, help="Uses an XML file that is used to create a new JAMF account.")
    parser.add_argument('--get_account_by_id', type=str, help="Retrieves the full details of a JAMF account specified by the ID.")

    args = parser.parse_args()

    if not os.path.isdir('./.data'):
        os.makedirs('./.data')
        print("[i] - Directory .data created in current folder. -[i]")

    #Create jamf server string
    jamf_sstring = args.jamf_server + ':' + args.api_port

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
    if args.get_accounts:
        print(json.dumps(get_accounts(jamf_sstring, bearer_token), indent=2))
    elif args.create_account:
        print(create_account(jamf_sstring, bearer_token, args.create_account))
    elif args.get_account_by_id:
        print(json.dumps(get_account_by_id(jamf_sstring, bearer_token, args.get_account_by_id), indent=2))
    else:
        raise Exception("X - Missing args - X")

if __name__ == "__main__":
    main()
