#!/bin/env python3
import subprocess
import argparse
import base64, json, os
from datetime import datetime

def auth_token(server, args):
    if args.username and args.password:
        auth_string = args.username + ':' + args.password
        auth_token =  base64.b64encode(auth_string.encode()).decode()
        command = ["./get_token.sh", server, auth_token]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    elif args.basic_auth:
        command = ["./get_token.sh", server, auth_token]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    elif os.file.exists('./.data/token'):
        with open('./.data/token') as f:
            json_string = f.read()
        data = json.loads(json_string)
        exp_string = date.get('expires')
        exp_date = datetime.strptime(exp_string, "%Y-%m-%dT%H:%M:%S:%fZ")
        now = datetime.utcnow()
        if exp_date > now:
            return json_string
        else:
           print("X - Cached token expired. Enter credentials to obtain a new token. -X")
           raise Exception("X - Missing args - X")
    else:
        print("X - Either a bearer token, basic auth string, or username and password must be supplied. -X")
        raise Exception("X - Missing args - X")
