#!/bin/env python3
import subprocess
import argparse
import base64, json, os
import urllib3
import requests
from auth import auth_token, create_server_string

#web request
def get_scripts(base_url, bearer_token):
    url = f"{base_url}/JSSResource/scripts"
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

#Used to get details of a script by specifying id
def get_script_by_id(base_url, bearer_token, id):
    url = f"{base_url}/JSSResource/scripts/id/{id}"
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

#Used to delete a script specified by id
def delete_script_by_id(base_url, bearer_token, id):
    url = f"{base_url}/JSSResource/scripts/id/{id}"
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
def create_script(base_url, bearer_token, script_name, script_path):
    #Check script path
    if not os.path.exists(script_path) or not os.path.isfile(script_path):
        raise Exception(f"X - {script_path} not found or is not file. - X")

    #Base64 encode supplied script content
    with open(script_path, 'rb') as f:
        file_content = f.read()

    encoded_bytes = base64.b64encode(file_content)
    encoded_content = encoded_bytes.decode('utf-8')

    #Create POST data
    data = f'''<script>
	<name>{script_name}</name>
	<category>None</category>
	<priority>Before</priority>
	<script_contents_encoded>{encoded_content}</script_contents_encoded>
</script>
'''
    print(data)
    
    url = f"{base_url}/JSSResource/scripts/id/0"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/xml",
        "Accept": "application/xml"
    }
        
    # Disable SSL verification and execute request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, headers=headers, data=data, verify=False)
    try:
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(e)
        return response.text


# Update an existing script by id
def update_script_by_id(base_url, bearer_token, id, script_path):
    
    if not os.path.exists(script_path) or not os.path.isfile(script_path):
        raise Exception(f"X - {script_path} is an invalid argument - X")

    #Base64 encode supplied script content
    with open(script_path, 'rb') as f:
        file_content = f.read()
    
    encoded_bytes = base64.b64encode(file_content)
    encoded_content = encoded_bytes.decode('utf-8')
        
    #Create PUT data
    data = f'''<script>
        <priority>Before</priority>
        <script_contents_encoded>{encoded_content}</script_contents_encoded>
</script>
'''
    print(data)
    
    url = f"{base_url}/JSSResource/scripts/id/{id}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",  
        "Content-Type": "application/xml",
        "Accept": "application/xml"
    }
        
#    with open("policy_template.xml", "rb") as file:
#        data = file.read()

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
    parser.add_argument('--get_scripts', action="store_true", help="Gets all script ids and names from the JAMF Pro server.")
    parser.add_argument('--api_port', type=str, help="The port of the JAMF server API to communicate with.")
    parser.add_argument('--get_script_by_id', type=str, help="Retrieves the full details of a JAMF Pro script specified by id.")
    parser.add_argument('--delete_script_by_id', type=str, help="Deletes a script specified by id.")
    parser.add_argument('--create_script', type=str, help="Creates a new script using supplied input file.")
    parser.add_argument('--update_script_by_id', type=str, help="Updates a script specified by id using the contents of script.sh.")
    parser.add_argument('--input_file', type=str, help="File path for input to create_script or update_script_by_id")

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
    if args.get_scripts:
        print(json.dumps(get_scripts(jamf_sstring, bearer_token), indent=2))
    elif args.get_script_by_id:
        print(json.dumps(get_script_by_id(jamf_sstring, bearer_token, args.get_script_by_id), indent=2))
    elif args.delete_script_by_id:
        print(delete_script_by_id(jamf_sstring, bearer_token, args.delete_script_by_id))
    elif args.create_script:
        if args.input_file:
            print(create_script(jamf_sstring, bearer_token, args.create_script, args.input_file))
        else:
            raise Exception("X - Missing args: input file is required - X")
    elif args.update_script_by_id:
        if args.input_file:
            print(update_script_by_id(jamf_sstring, bearer_token, args.update_script_by_id, args.input_file))
        else:
            raise Exception("X - Missing args: input file is required - X")
    else:
        raise Exception("X - Missing or invalid args - X")

if __name__ == "__main__":
    main()
