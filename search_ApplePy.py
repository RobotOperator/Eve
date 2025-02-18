#!/bin/env python3
import subprocess
import argparse
import base64, json, os

#Search function for the JAMF API
def search_computer_id(server, btoken, search_s):
    command = ["./computer_search.sh", server, btoken, search_s]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout

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
        #print(result)
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

def main():
    #Create arg parser
    parser = argparse.ArgumentParser(description="Accepts authentication values for JAMF")

    parser.add_argument('--username', type=str, help="The username for authentication.")
    parser.add_argument('--password', type=str, help="The password for authentication.")
    parser.add_argument('--basic_auth', type=str, help="The base64 basic auth token for authentication.")
    parser.add_argument('--bearer_token', type=str, help="A bearer token to use for authentication.")
    parser.add_argument('--jamf_server', required=True, type=str, help="The URL of the target JAMF server.")
    parser.add_argument('--search_string', required=True, type=str, help="The computer ID string to search on.")
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

    #Perform our search
    print(search_computer_id(jamf_sstring, bearer_token, args.search_string))

if __name__ == "__main__":
    main()
