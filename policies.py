#!/bin/env python3
import subprocess
import argparse
import base64, json, os
import urllib3
import requests
from auth import auth_token, create_server_string

#web request
def get_policies(base_url, bearer_token):
    url = f"{base_url}/JSSResource/policies"
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

#Used to get details of a policy by specifying id
def get_policy_by_id(base_url, bearer_token, id):
    url = f"{base_url}/JSSResource/policies/id/{id}"
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

#Used to delete a policy specified by id
def delete_policy_by_id(base_url, bearer_token, id):
    url = f"{base_url}/JSSResource/policies/id/{id}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.delete(url, headers=headers, verify=False)
    response.raise_for_status()
    return "+OK+"

#Creates a new policy as defined in policy_template.xml
def create_policy(base_url, bearer_token, input_file):
    
    if not os.path.exists(input_file) or not os.path.isfile(input_file):
        raise Exception(f"X - {input_file} is not found or is not an XML file.  - X")
    
    url = f"{base_url}/JSSResource/policies/id/0"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/xml",
        "Accept": "application/xml"
    }
        
    with open(input_file, "rb") as file:
        data = file.read()

    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, headers=headers, data=data, verify=False)
    try:
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(e)
        return response.text

# Update an existing policy by id using the policy template xml
def update_policy_by_id(base_url, bearer_token, id, input_file):
    
    if not os.path.exists(input_file) or not os.path.isfile(input_file):
        raise Exception("X - input_file was not found or is not a valid XML file. - X")
    
    url = f"{base_url}/JSSResource/policies/id/{id}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",  
        "Content-Type": "application/xml",
        "Accept": "application/xml"
    }
        
    with open(input_file, "rb") as file:
        data = file.read()

    # Disable SSL verification and execute request  
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.put(url, headers=headers, data=data, verify=False)
    try:
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(e)
        return response.text

def main():
    #Create arg parser
    parser = argparse.ArgumentParser(description="Accepts authentication values for JAMF")

    parser.add_argument('--username', type=str, help="The username for authentication.")
    parser.add_argument('--password', type=str, help="The password for authentication.")
    parser.add_argument('--basic_auth', type=str, help="The base64 basic auth token for authentication.")
    parser.add_argument('--bearer_token', type=str, help="A bearer token to use for authentication.")
    parser.add_argument('--jamf_server', type=str, help="The URL of the target JAMF server.")
    parser.add_argument('--get_policies', action="store_true", help="Gets all policy ids and names from the JAMF Pro server.")
    parser.add_argument('--api_port', type=str, help="The port of the JAMF server API to communicate with.")
    parser.add_argument('--get_policy_by_id', type=str, help="Retrieves the full details of a JAMF Pro policy specified by id.")
    parser.add_argument('--delete_policy_by_id', type=str, help="Deletes a policy specified by id.")
    parser.add_argument('--create_policy', action="store_true", help="Creates a new policy as specified by policy_template.xml.")
    parser.add_argument('--update_policy_by_id', type=str, help="Updates a policy specified by id using the contents of policy_template.xml.")
    parser.add_argument('--input_file', type=str, help="File path for input to create_policy or update_policy_by_id")

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
    if args.get_policies:
        print(json.dumps(get_policies(jamf_sstring, bearer_token), indent=2))
    elif args.get_policy_by_id:
        print(json.dumps(get_policy_by_id(jamf_sstring, bearer_token, args.get_policy_by_id), indent=2))
    elif args.delete_policy_by_id:
        print(delete_policy_by_id(jamf_sstring, bearer_token, args.delete_policy_by_id))
    elif args.create_policy:
        if args.input_file:
            print(create_policy(jamf_sstring, bearer_token, args.input_file))
        else:
            raise Exception("X - Missing args: input file is required - X")
#        print(create_policy(jamf_sstring, bearer_token))
    elif args.update_policy_by_id:
        if args.input_file:
            print(update_policy_by_id(jamf_sstring, bearer_token, args.update_policy_by_id, args.input_file))
        else:
            raise Exception("X - Missing args: input file is required - X")
#        print(update_policy_by_id(jamf_sstring, bearer_token, args.update_policy_by_id))
    else:
        raise Exception("X - Missing args - X")

if __name__ == "__main__":
    main()
