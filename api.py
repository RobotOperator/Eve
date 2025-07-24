#!/bin/env python3
import subprocess
import argparse
import base64, json, os
import urllib3
import requests
from auth import auth_token, create_server_string

#web request
def get_api_roles(base_url, bearer_token):
    url = f"{base_url}/api/v1/api-roles"
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

#Get all api clients in the JAMF tenant
def get_api_clients(base_url, bearer_token):
    url = f"{base_url}/api/v1/api-integrations"
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

#Used to get more details about an api role using a supplied id
def get_role_by_id(base_url, bearer_token, id):
    url = f"{base_url}/api/v1/api-roles/{id}"
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

#Used to get an api client using a supplied id
def get_client_by_id(base_url, bearer_token, id):
    url = f"{base_url}/api/v1/api-integrations/{id}"
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

#Creates a new api role with privileges as defined in input_file
def create_api_role(base_url, bearer_token, input_file):
    
    if not os.path.exists(input_file) or not os.path.isfile(input_file):
        raise Exception(f"X - {input_file} is not found or is not an XML file.  - X")
        
    url = f"{base_url}/api/v1/api-roles"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    with open(input_file, "r") as file:
        data = json.loads(file.read())
    
    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, headers=headers, json=data, verify=False)
    try:
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(e)
        return response.text

#Creates a new api client with assigned roles as defined in input_file
def create_api_client(base_url, bearer_token, input_file):
    
    if not os.path.exists(input_file) or not os.path.isfile(input_file):
        raise Exception(f"X - {input_file} is not found or is not an XML file.  - X")
        
    url = f"{base_url}/api/v1/api-integrations"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    with open(input_file, "r") as file:
        data = json.loads(file.read())

    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, headers=headers, json=data, verify=False)
    try:
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(e)
        return response.text

# Update an existing api role by id using the input json
def update_api_role_by_id(base_url, bearer_token, id, input_file):

    if not os.path.exists(input_file) or not os.path.isfile(input_file):
        raise Exception("X - input_file was not found or is not a valid JSON file. - X")
    
    url = f"{base_url}/api/v1/api-roles/{id}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
        
    with open(input_file, "r") as file:
        data = json.loads(file.read())
    
    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.put(url, headers=headers, json=data, verify=False)
    try:
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(e)
        return response.text

# Update an existing api client by id using the input json
def update_api_client_by_id(base_url, bearer_token, id, input_file):

    if not os.path.exists(input_file) or not os.path.isfile(input_file):
        raise Exception("X - input_file was not found or is not a valid JSON file. - X")
    
    url = f"{base_url}/api/v1/api-integrations/{id}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
        
    with open(input_file, "r") as file:
        data = json.loads(file.read())
    
    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.put(url, headers=headers, json=data, verify=False)
    try:
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(e)
        return response.text


# Delete an existing api role by id
def delete_api_role_by_id(base_url, bearer_token, id):
    
    url = f"{base_url}/api/v1/api-roles/{id}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }   
        
    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.delete(url, headers=headers, verify=False)
    response.raise_for_status()
    return "+OK+"

# Delete an existing api client by id
def delete_api_client_by_id(base_url, bearer_token, id):

    url = f"{base_url}/api/v1/api-integrations/{id}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }
    
    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.delete(url, headers=headers, verify=False)
    response.raise_for_status()
    return "+OK+"


# Get an API Clients Credentials
def get_client_credentials(base_url, bearer_token, client_id):
    
    url = f"{base_url}/api/v1/api-integrations/{client_id}/client-credentials"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"   
    }
    
    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, headers=headers, verify=False)
    try:
        response.raise_for_status()
        return json.loads(response.text)
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
    parser.add_argument('--get_api_roles', action="store_true", help="Retrieves all api roles in the JAMF tenant.")
    parser.add_argument('--api_port', type=str, help="The port of the JAMF server API to communicate with.")
    parser.add_argument('--get_api_clients', action="store_true", help="Retrieves API clients in the JAMF tenant.")
    parser.add_argument('--get_role_by_id', type=str, help="Retrieves details of an API role specified by id.")
    parser.add_argument('--get_client_by_id', type=str, help="Retrieves the details of a client specified by id.")
    parser.add_argument('--create_api_role', action="store_true", help="Creates a new api role with assigned privileges based on supplied input JSON file.")
    parser.add_argument('--input_file', type=str, help="File path for input.")
    parser.add_argument('--update_api_role_by_id', type=str, help="Updates an existing api role based on supplied input JSON file.")
    parser.add_argument('--delete_api_role_by_id', type=str, help="Deletes an existing api role using the id.")
    parser.add_argument('--create_api_client', action='store_true', help="Creates a new api client with assigned roles as specified in the input file.")
    parser.add_argument('--get_client_credentials', type=str, help="Retrieves client credentials for the api client specified by id.")
    parser.add_argument('--update_api_client_by_id', type=str, help="Updates and existing api client by using the supplied id and the input JSON file.")
    parser.add_argument('--delete_api_client_by_id', type=str, help="Deletes an existing api client using the id.")
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
    if args.get_api_roles:
        print(json.dumps(get_api_roles(jamf_sstring, bearer_token), indent=2))
    elif args.get_api_clients:
        print(json.dumps(get_api_clients(jamf_sstring, bearer_token), indent=2))
    elif args.get_role_by_id:
        print(json.dumps(get_role_by_id(jamf_sstring, bearer_token, args.get_role_by_id), indent=2))
    elif args.get_client_by_id:
        print(json.dumps(get_client_by_id(jamf_sstring, bearer_token, args.get_client_by_id), indent=2))
    elif args.create_api_role:  
        if args.input_file:
            print(create_api_role(jamf_sstring, bearer_token, args.input_file))
        else:
            raise Exception("X - Missing args: input file is required - X")
    elif args.create_api_client:
        if args.input_file:
            print(create_api_client(jamf_sstring, bearer_token, args.input_file))
        else:
            raise Exception("X - Missing args: input file is required - X")
    elif args.update_api_role_by_id:
        if args.input_file:
            print(update_api_role_by_id(jamf_sstring, bearer_token, args.update_api_role_by_id, args.input_file))
        else:
            raise Exception("X - Missing args: input file is required - X")
    elif args.update_api_client_by_id:
        if args.input_file:
            print(update_api_client_by_id(jamf_sstring, bearer_token, args.update_api_client_by_id, args.input_file))
        else:
            raise Exception("X - Missing args: input file is required - X")
    elif args.delete_api_role_by_id:
        print(delete_api_role_by_id(jamf_sstring, bearer_token, args.delete_api_role_by_id))
    elif args.get_client_credentials:
        print(json.dumps(get_client_credentials(jamf_sstring, bearer_token, args.get_client_credentials), indent=2))
    elif args.delete_api_client_by_id:
        print(delete_api_client_by_id(jamf_sstring, bearer_token, args.delete_api_client_by_id))
    else:
        raise Exception("X - Missing args. - X")

if __name__ == "__main__":
    main()
