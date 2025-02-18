#!/bin/env python3
import subprocess
import argparse
import base64, json, os
from auth.py import auth_token

def delete_policy(token, args):
    #delete_policy_by_id.sh $Server $token $policy_id
    command = ["./delete_policy_by_id.sh", args.jamf_server, token, args.policy_id]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout

def push_policy(args):
    print("Stub")

#Select action to be performed
def parse_action(action, token, args):
    if action.tolower() == "delete":
        print(delete_policy(token, args))
    elif action.tolower() == "create":
        print(push_policy(token, args))
    else:
        print("X - Action not recognized - X")

def main():
    #Create arg parser
    parser = argparse.ArgumentParser(description="Accepts authentication values for JAMF")

    parser.add_argument('--username', type=str, help="The username for authentication.")
    parser.add_argument('--password', type=str, help="The password for authentication.")
    parser.add_argument('--basic_auth', type=str, help="The base64 basic auth token for authentication.")
    parser.add_argument('--bearer_token', type=str, help="A bearer token to use for authentication.")
    parser.add_argument('--jamf_server', required=True, type=str, help="The URL of the target JAMF server.")
    parser.add_argument('--action', required=True, type=str, help="The policy action to perform.")
    parser.add_argument('--policy_id', type=str, help="The policy id.")
    parser.add_argument('--api_port', type=str, required=True, help="The port of the JAMF server API to communicate with.")

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
        print(bearer_string)

        #JSON parsing the output
        with open('./.data/token', 'w') as out:
            out.write(bearer_string)
        data = json.loads(bearer_string)
        bearer_token = data.get('token')

    #Perform our action
    parse_action(args.action, bearer_token, args)
    #print(search_computer_id(jamf_sstring, bearer_token, args.search_string))

if __name__ == "__main__":
    main()
