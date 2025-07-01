#!/bin/env python3
import subprocess
import argparse
import base64, json, os
from datetime import datetime, UTC, timedelta
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

def api_auth_token(base_url, client_id, client_secret):
    url = f"{base_url}/api/v1/oauth/token"
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "accept": "application/json"
    }

    payload = {
        "grant_type": "client_credentials",
        "client_id": f"{client_id}",
        "client_secret": f"{client_secret}"
    }
        
    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, data=payload, headers=headers, verify=False)
    response.raise_for_status()
    return response.text
            
def auth_token(server, args):
    if args.username and args.password:
        auth_string = args.username + ':' + args.password
        auth_token =  base64.b64encode(auth_string.encode()).decode()
        result = get_auth_token(server, auth_token)
        result_json = json.loads(result)
        result_json["server"] = server
        result = json.dumps(result_json)
        return result
    elif args.basic_auth:
        result = get_auth_token(server, auth_token)
        result_json = json.loads(result)
        result_json["server"] = server
        result = json.dumps(result_json)
        return result 
    elif hasattr(args, 'api_client_id') and hasattr(args, 'api_client_secret'):
        result_json = {}
        apistring = api_auth_token(server, args.api_client_id, args.api_client_secret)
        jresponse = json.loads(apistring)
        expiry = datetime.now(UTC) + timedelta(seconds=jresponse.get("expires_in"))
        result_json["expires"] = expiry.strftime("%Y-%m-%dT%H:%M:%SZ")
        result_json["token"] = jresponse.get("access_token")
        result_json["server"] = server
        print(f"Expires in {jresponse.get("expires_in")} seconds.")
        result = json.dumps(result_json)
        return result
    elif os.path.exists('./.data/token'):
        with open('./.data/token') as f:
            json_string = f.read()
        data = json.loads(json_string)
        exp_string = data.get('expires')
        exp_date = datetime.strptime(exp_string, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        now = datetime.now(UTC)
        if exp_date > now:
            return json_string
        else:
           print("\033[91m X - Cached token expired. Enter credentials to obtain a new token. -X \033[00m")
           raise Exception("X - Cached token expired. Enter credentials to obtain a new token. -X")
    else:
        print("\033[91m X - Either a bearer token, basic auth string, or username and password must be supplied. -X \033[00m")
        raise Exception("X - Missing args - X")

#Create jamf server string
def create_server_string(args):
    if args.api_port and args.jamf_server:
        jamf_sstring = args.jamf_server + ':' + args.api_port
    elif args.jamf_server:
        jamf_sstring = args.jamf_server
    else:
        if os.path.exists('./.data/token'):
            with open('./.data/token', 'r') as f:
                data = json.load(f)
            jamf_sstring = data.get("server")
        else:
            raise Exception("X - JAMF Server must be specified -X")
    return jamf_sstring

# Gets details of the current authenticated token
def get_token_details(server, bearer_token):
    url = f"{server}/api/v1/auth"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return json.dumps(json.loads(response.text), indent=2)


def main():
    #Create arg parser
    parser = argparse.ArgumentParser(description="Accepts authentication values for JAMF")
    
    parser.add_argument('--username', type=str, help="The username for authentication.")
    parser.add_argument('--password', type=str, help="The password for authentication.")
    parser.add_argument('--basic_auth', type=str, help="The base64 basic auth token for authentication.")
    parser.add_argument('--bearer_token', type=str, help="A bearer token to use for authentication.")
    parser.add_argument('--api_client_id', type=str, help="The unique api client id.")
    parser.add_argument('--api_client_secret', type=str, help="The unique api client secret.")
    parser.add_argument('--jamf_server', type=str, help="The URL of the target JAMF server.")
    parser.add_argument('--api_port', type=str, help="The port of the JAMF server API to communicate with.")
    parser.add_argument('--token_details', action="store_true", help="Prints the scope and other info. for the current token using the auth current JAMF Pro API.")

    args = parser.parse_args()
        
    #Create data directory if not exists
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
            print(bearer_string)
            return 1
        print(bearer_string)
    
        #JSON parsing the output
        with open('./.data/token', 'w') as out:
            out.write(bearer_string)
        data = json.loads(bearer_string)
        bearer_token = data.get('token')
    if args.token_details:
        print(get_token_details(jamf_sstring, bearer_token))

if __name__ == "__main__":
    main()
