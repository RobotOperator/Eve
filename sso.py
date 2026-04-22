#!/bin/env python3
import argparse
import json
import os

import requests
import urllib3

from auth import auth_token, create_server_string


def _decode_response(response):
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return response.text


def get_sso_config(base_url, bearer_token):
    url = f"{base_url}/api/v3/sso"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return json.loads(response.text)


def get_sso_history(base_url, bearer_token):
    url = f"{base_url}/api/v3/sso/history"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return json.loads(response.text)


def get_sso_failover(base_url, bearer_token):
    url = f"{base_url}/api/v1/sso/failover"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return json.loads(response.text)


def get_all_sso_configs(base_url, bearer_token):
    response = {
        "sso_config": get_sso_config(base_url, bearer_token)
    }

    try:
        response["sso_failover"] = get_sso_failover(base_url, bearer_token)
    except Exception as e:
        response["sso_failover"] = {
            "status": "unavailable",
            "detail": str(e)
        }

    '''try:
        response["sso_history"] = get_sso_history(base_url, bearer_token)
    except Exception as e:
        response["sso_history"] = {
            "status": "unavailable",
            "detail": str(e)
        }'''

    return response


def regenerate_sso_failover(base_url, bearer_token):
    url = f"{base_url}/api/v1/sso/failover/generate"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, headers=headers, verify=False)
    try:
        response.raise_for_status()
        return _decode_response(response)
    except Exception as e:
        print(e)
        return _decode_response(response)


def update_sso_config(base_url, bearer_token, input_file):
    if not os.path.exists(input_file) or not os.path.isfile(input_file):
        raise Exception("X - input_file was not found or is not a valid JSON file. - X")

    url = f"{base_url}/api/v3/sso"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    with open(input_file, "r") as file:
        data = json.loads(file.read())

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.put(url, headers=headers, json=data, verify=False)
    try:
        response.raise_for_status()
        return _decode_response(response)
    except Exception as e:
        print(e)
        return _decode_response(response)


def disable_sso_config(base_url, bearer_token):
    url = f"{base_url}/api/v3/sso/disable"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, headers=headers, verify=False)
    try:
        response.raise_for_status()
        return _decode_response(response)
    except Exception as e:
        print(e)
        return _decode_response(response)


def generate_sso_cert(base_url, bearer_token):
    url = f"{base_url}/api/v2/sso/cert"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, headers=headers, verify=False)
    try:
        response.raise_for_status()
        return _decode_response(response)
    except Exception as e:
        print(e)
        return _decode_response(response)

def delete_sso_cert(base_url, bearer_token):
    url = f"{base_url}/api/v2/sso/cert"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.delete(url, headers=headers, verify=False)
    try:
        response.raise_for_status()
        return "- OK -"
    except Exception as e:
        print(e)
        return _decode_response(response)

def get_sso_cert(base_url, bearer_token):
    url = f"{base_url}/api/v2/sso/cert/download"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(url, headers=headers, verify=False)  
    try:
        response.raise_for_status()
        return _decode_response(response)
    except Exception as e:
        print(e)
        return _decode_response(response)


def _print_result(output):
    if isinstance(output, (dict, list)):
        print(json.dumps(output, indent=2))
    else:
        print(output)


def main():
    parser = argparse.ArgumentParser(description="Accepts authentication values for JAMF")

    parser.add_argument('--username', type=str, help="The username for authentication.")
    parser.add_argument('--password', type=str, help="The password for authentication.")
    parser.add_argument('--basic_auth', type=str, help="The base64 basic auth token for authentication.")
    parser.add_argument('--bearer_token', type=str, help="A bearer token to use for authentication.")
    parser.add_argument('--jamf_server', type=str, help="The URL of the target JAMF server.")
    parser.add_argument('--api_port', type=str, help="The port of the JAMF server API to communicate with.")
    parser.add_argument('--get_all_sso_configs', action="store_true", help="Retrieves SSO configuration and failover details when available.")
    parser.add_argument('--get_sso_config', action="store_true", help="Retrieves the current SSO configuration from the Jamf Pro API.")
    parser.add_argument('--get_sso_history', action="store_true", help="Retrieves the SSO history object from the Jamf Pro API.")
    parser.add_argument('--get_sso_failover', action="store_true", help="Retrieves the current SSO failover settings.")
    parser.add_argument('--regenerate_sso_failover', action="store_true", help="Regenerates and retrieves the current SSO failover settings.")
    parser.add_argument('--update_sso_config', action="store_true", help="Updates the SSO configuration using a supplied input JSON file.")
    parser.add_argument('--disable_sso_config', action="store_true", help="Disables the current SSO configuration.")
    parser.add_argument('--generate_sso_cert', action="store_true", help="Generates the SSO certificate used by Jamf Pro to sign identity provider requests.")
    parser.add_argument('--delete_sso_cert', action="store_true", help="Deletes the SSO certificate used by Jamf Pro to sign identity provider requests.")
    parser.add_argument('--get_sso_cert', action="store_true", help="Gets the SSO certificate used by Jamf Pro to sign identity provider requests.")
    parser.add_argument('--input_file', type=str, help="File path for input to update_sso_config.")
    args = parser.parse_args()

    if not os.path.isdir('./.data'):
        os.makedirs('./.data')
        print("[i] - Directory .data created in current folder. -[i]")

    jamf_sstring = create_server_string(args)

    if args.bearer_token:
        bearer_token = args.bearer_token
    else:
        bearer_string = auth_token(jamf_sstring, args)
        if 'token' not in bearer_string:
            print("X- Failed to retrieve token. Please check your credentials. -X")
            return 1

        with open('./.data/token', 'w') as out:
            out.write(bearer_string)
        data = json.loads(bearer_string)
        bearer_token = data.get('token')

    if args.get_all_sso_configs:
        _print_result(get_all_sso_configs(jamf_sstring, bearer_token))
    elif args.get_sso_config:
        _print_result(get_sso_config(jamf_sstring, bearer_token))
    elif args.get_sso_history:
        _print_result(get_sso_history(jamf_sstring, bearer_token))
    elif args.get_sso_failover:
        _print_result(get_sso_failover(jamf_sstring, bearer_token))
    elif args.regenerate_sso_failover:
        _print_result(regenerate_sso_failover(jamf_sstring, bearer_token))
    elif args.update_sso_config:
        if args.input_file:
            _print_result(update_sso_config(jamf_sstring, bearer_token, args.input_file))
        else:
            raise Exception("X - Missing args: input file is required - X")
    elif args.disable_sso_config:
        _print_result(disable_sso_config(jamf_sstring, bearer_token))
    elif args.generate_sso_cert:
        _print_result(generate_sso_cert(jamf_sstring, bearer_token))
    elif args.delete_sso_cert:
        _print_result(delete_sso_cert(jamf_sstring, bearer_token))
    elif args.get_sso_cert:
        _print_result(get_sso_cert(jamf_sstring, bearer_token))
    else:
        raise Exception("X - Missing args. - X")


if __name__ == "__main__":
    main()
