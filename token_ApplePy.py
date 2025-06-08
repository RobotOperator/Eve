#!/bin/env python3
import subprocess
import argparse
import base64, json, os
import requests
from datetime import datetime
import requests
import urllib3

def get_auth_token(base_url, auth_header):
    url = f"{base_url}/api/v1/auth/token"
    headers = {
        "Authorization": f"Basic {auth_header}"
    }
    
    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.text

def auth_token(server, args):
    if args.username and args.password:
        auth_string = args.username + ':' + args.password
        auth_token =  base64.b64encode(auth_string.encode()).decode()
        result = get_auth_token(server, auth_token)
        return result
    elif args.basic_auth:
        result = get_auth_token(server, auth_token)
        return result
    elif os.path.exists('./.data/token'):
        with open('./.data/token') as f:
            json_string = f.read()
        data = json.loads(json_string)
        exp_string = data.get('expires')
        exp_date = datetime.strptime(exp_string, "%Y-%m-%dT%H:%M:%S.%fZ")
        now = datetime.utcnow()
        if exp_date > now:
            return json_string
        else:
           print("X - Cached token expired. Enter credentials to obtain a new token. -X")
           raise Exception("X - Missing args - X")
    else:
        print("X - Either a bearer token, basic auth string, or username and password must be supplied. -X")
        raise Exception("X - Missing args - X")

def main():
    #Create arg parser
    parser = argparse.ArgumentParser(description="Accepts authentication values for JAMF")

    parser.add_argument('--username', type=str, help="The username for authentication.")
    parser.add_argument('--password', type=str, help="The password for authentication.")
    parser.add_argument('--basic_auth', type=str, help="The base64 basic auth token for authentication.")
    parser.add_argument('--bearer_token', type=str, help="A bearer token to use for authentication.")
    parser.add_argument('--jamf_server', required=True, type=str, help="The URL of the target JAMF server.")
    parser.add_argument('--api_port', type=str, required=True, help="The port of the JAMF server API to communicate with.")

    args = parser.parse_args()
    
    #Create data directory if not exists
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
            print(bearer_string)
            return 1
        print(bearer_string)

        #JSON parsing the output
        with open('./.data/token', 'w') as out:
            out.write(bearer_string)
        data = json.loads(bearer_string)
        bearer_token = data.get('token')
    #To be continued...

if __name__ == "__main__":
    main()
