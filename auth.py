#!/bin/env python3
import subprocess
import argparse
import base64, json, os
from datetime import datetime
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
           print("\033[91m X - Cached token expired. Enter credentials to obtain a new token. -X \033[00m")
           raise Exception("X - Missing args - X")
    else:
        print("\033[91m X - Either a bearer token, basic auth string, or username and password must be supplied. -X \033[00m")
        raise Exception("X - Missing args - X")


#def auth_token(server, args):
#    if args.username and args.password:
#        auth_string = args.username + ':' + args.password
#        auth_token =  base64.b64encode(auth_string.encode()).decode()
#        command = ["./get_token.sh", server, auth_token]
#        result = subprocess.run(command, capture_output=True, text=True, check=True)
#        return result.stdout
#    elif args.basic_auth:
#        command = ["./get_token.sh", server, auth_token]
#        result = subprocess.run(command, capture_output=True, text=True, check=True)
#        return result.stdout
#    elif os.file.exists('./.data/token'):
#        with open('./.data/token') as f:
#            json_string = f.read()
#        data = json.loads(json_string)
#        exp_string = date.get('expires')
#        exp_date = datetime.strptime(exp_string, "%Y-%m-%dT%H:%M:%S:%fZ")
#        now = datetime.utcnow()
#        if exp_date > now:
#            return json_string
#        else:
#           print("X - Cached token expired. Enter credentials to obtain a new token. -X")
#           raise Exception("X - Missing args - X")
#    else:
#        print("X - Either a bearer token, basic auth string, or username and password must be supplied. -X")
#        raise Exception("X - Missing args - X")
