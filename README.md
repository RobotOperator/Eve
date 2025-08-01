# Eve
<p align="center" width="100%">
    <img align="middle" src="/images/Eve.png" width=35% height=35%/>
</p>

## Overview
Eve is a Jamf exploitation toolkit used to interact with either cloud hosted Jamf Pro tenants or locally hosted Jamf Pro servers using API calls. To use this toolkit credentials for an account registered with the Jamf instance that has API access will be required. This tooling automates attacks that my team and I have performed successfully to exploit Jamf access to enumerate Apple devices, escalate privileges, as well as execute code in varying contexts to laterally move to different systems. The intended user for this toolkit should already have some awareness about Jamf API permissions to know how to best leverage their access. For those trying to discover what can be done I recommend starting <a href="https://developer.jamf.com/jamf-pro/docs/classic-api-minimum-required-privileges-and-endpoint-mapping">here</a>.

## Requirements
1. Python 3.12 or newer
2. requests Python Module
3. urllib Python Module
4. dateutil Python Module
5. flask Python Module
6. flask_cors Python Module
7. pytz Python Module
8. certifi Python Module
9. pprint Python Module

## Setup
### Web UI Setup
```bash
# Clone the repository
git clone https://github.com/RobotOperator/Eve.git
cd Eve

# Start the Flask server
python3 eve_ui.py
```

The web UI will be available at `http://localhost:8003`

### Proxied Web UI Setup (for red teaming/pivoting)
To proxy outbound JAMF API requests while keeping the web UI local:
```bash
# Configure proxychains (edit /etc/proxychains.conf or use custom config)
# Only the outbound requests to JAMF will be proxied, not the local web UI

# Start the Flask server through proxychains
proxychains python3 eve_ui.py

# Access the UI normally in your browser (this connection is NOT proxied)
# http://localhost:8003
```

### CLI Setup
```bash
# Clone Repo
git clone https://github.com/RobotOperator/Eve.git
cd Eve

# Get initial token using username and password, api client id and secret, basic authentication string, or an already obtained Bearer token
# API port is usually either 443 for cloud or 8443 for local instances
# Bearer token and server string will be stored locally and used if not expired
python3 auth.py --username JamfUser --password $(jpass) --tenant https://tenant.jamfcloud.com --token_details
python3 auth.py --api_client_id "f273dfb9-XXXX-XXXX" --api_client_secret u2... --tenant https://jamf.local --api_port 8443
python3 auth.py --basic_auth ua... --tenant https://tenant.jamfcloud.com
python3 auth.py --bearer_token ey... --tenant https://tenant.jamfcloud.com
```

### Development Setup
If you want to modify the frontend, you'll need Node.js and npm:
```bash
cd ui/frontend
npm install
# Make your changes, then build
npm run build
```

## Usage
Eve includes some pre-defined XML and JSON templates for interaction with Jamf Pro APIs in the "templates" directory. These can be modified and provided to command-line input_file arguments or loaded automatically in the Eve UI. 

### Web UI
1. Start the Flask server: `python3 eve_ui.py`
2. Open your browser to `http://localhost:8003`
3. Authenticate using either:
   - **OAuth2**: Client ID and Client Secret
   - **Username/Password**: JAMF username and password
4. Use the web interface to:
   - Manage accounts and groups
   - Search and manage computers
   - Create and manage extension attributes
   - Create, edit, and manage policies with advanced XML editor
   - Manage scripts
   - View API roles and clients

### Web UI Features
- **Modern Web UI**: Clean, responsive interface with dark mode support
- **Policy Editor**: Advanced XML editor with syntax highlighting, auto-completion, and helper pane
- **Extension Attributes**: Create and manage computer extension attributes with templates
- **Token Management**: Automatic token refresh for uninterrupted sessions
- **Multi-Auth Support**: Both OAuth2 and username/password authentication

###  CLI Tools
Any of the CLI commands will show elligible parameters and usage with the scripts by running --help.
```
python3 <script_name.py> --help
```

### Auth.py
```
# Used for authenticating and storing a bearer token/Jamf server details using username/password, basic auth string, existing bearer token, or API credentials
# token_details can show permissions included with obtained token following authentication
# Once first authentication has occurred, jamf_server can be omitted unless a different server URL needs to be specified
python3 auth.py --username auditor --password "auditor_Pass" --jamf_server https://tenant.local --api_port 8443
python3 auth.py --basic_auth "UX...." --jamf_server https://tenant.jamfcloud.com
python3 auth.py --api_client_id f273dfb9 --api_client_secret=-UX... #Use = after parameter if there is a dash in any value
python3 auth.py --bearer_token ey... --jamf_server https://tenant.jamfcloud.com --token_details
```
### Computers.py
```
# Used for searching for computer details, pulling computer policy logs, and creating/updating/deleting/reading computer extension attributes
# Requires bearer token with Read Computers JSSObject permission and/or Create/Read/Update/Delete Computer Extension Attributes JSSObject permissions
# Authentication details are optional/shown in first example below
python3 computers.py --get_computers [--username --password --jamf_server]
python3 computers.py --search_for_computer_by_string "JVM"
python3 computers.py --get_computer_by_id 3
python3 computers.py --get_policy_logs_by_udid <Computer UDID>
python3 computers.py --get_computer_extension_attributes
python3 computers.py --get_computer_extension_attribute_by_id 2
python3 computers.py --create_computer_extension_attribute --input_file ./my_extension_template.xml
python3 computers.py --update_computer_extension_attribute_by_id 3 --input_file ./my_extension_template.xml
python3 computers.py --delete_computer_extension_attribute_by_id 3
```
### Accounts.py
```
# Used for interacting with Jamf Pro accounts and groups, create/read/update/delete
# Requires bearer token with Create/Read/Update/Delete Accounts and/or Create/Read/Update/Delete Groups JSSObject permissions
# 'Update Accounts' allows resetting other account passwords and updating their permissions
# Authentication parameters are available as shown previously
python3 accounts.py --get_accounts
python3 accounts.py --get_account_by_id 21
python3 accounts.py --create_account --input_file ./my_path_to_account.xml
python3 accounts.py --update_account_by_id 21 --input_file ./my_path_to_account.xml
python3 accounts.py --delete_account_by_id 21
python3 accounts.py --get_groups
python3 accounts.py --get_group_by_id 1
python3 accounts.py --create_group --input_file ./my_path_to_group.xml
python3 accounts.py --update_group_by_id 1 --input_file ./my_path_to_group.xml
python3 accounts.py --delete_group_by_id 1
```
### Api.py
```
# Used for interacting with API roles and clients, create/read/update/delete and retrieving client credentials
# Requires bearer token with Create/Read/Update/Delete API Integrations and/or Create/Read/Update/Delete API Roles JSSObject permissions
# 'Create API Integrations' permission required to get API Client/Integration credentials
# Authentication parameters are available as shown previously
python3 api.py --get_api_roles
python3 api.py --get_api_clients
python3 api.py --get_role_by_id 2
python3 api.py --get_client_by_id 3
python3 api.py --create_api_role --input_file ./path_to_my_role.json
python3 api.py --update_api_role_by_id 2 --input_file ./path_to_my_role.json
python3 api.py --delete_api_role_by_id 3
python3 api.py --create_api_client --input_file ./path_to_my_client.json
python3 api.py --update_api_client_by_id 3 --input_file ./path_to_my_client.json
python3 api.py --delete_api_client_by_id 3
python3 api.py --get_client_credentials 3
```
### Scripts.py
```
# Used for interacting with scripts stored on the Jamf Pro server to be executed by policies, create/read/update/delete
# Requires bearer token with Create/Read/Update/Delete Scripts JSSObject permissions
# Authentication parameters are available as shown previously
python3 scripts.py --get_scripts
python3 scripts.py --get_script_by_id 3
python3 scripts.py --create_script My_Script --input_file ./path_to_my_script.sh
python3 scripts.py --update_script_by_id 3 --input_file ./path_to_my_script.sh
python3 scripts.py --delete_script_by_id 3
```
### Policies.py
```
# Used for interacting with policies to execute commands or scripts on managed macOS devices, create/read/update/delete
# Requires bearer token with Create/Read/Update/Delete Policies JSSObject permissions
# Authentication parameters are available as shown previously
python3 policies.py --get_policies
python3 policies.py --get_policy_by_id 27
python3 policies.py --create_policy --input_file ./path_to_my_policy.xml
python3 policies.py --update_policy_by_id 27 --input_file ./path_to_my_policy.xml
python3 policies.py --delete_policy_by_id 27
```

## Contributors
<a href="https://github.com/MayerDaniel">Daniel Mayer</a>


