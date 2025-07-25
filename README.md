# Eve
<p align="center" width="100%">
    <img align="middle" src="/images/Eve.png" width=35% height=35%/>
</p>

## Overview
Eve is a JAMF exploitation toolkit used to interact with either cloud hosted JAMF tenants or locally hosted JAMF servers using various API calls. To use this toolkit credentials for an account registered with the JAMF instance that has API access will be required. This tooling automates attacks that my team and I have performed successfully to exploit JAMF access to enumerate Apple devices as well as execute code in varying contexts to laterally move to different systems. The intended user for this toolkit should already have some awareness about JAMF API permissions to know how to best leverage their access. For those trying to discover what can be done I recommend starting <a href="https://developer.jamf.com/jamf-pro/docs/classic-api-minimum-required-privileges-and-endpoint-mapping">here</a>.

## Requirements
1. Python3
2. A unix system capable of executing the embedded scripts with curl (for CLI tools)
3. <a href="https://github.com/rofl0r/proxychains-ng">proxychains</a> (optional, for CLI tools)
4. <a href="https://jqlang.org">jq</a> for parsing JSON output (for CLI tools)

## Setup
### Web UI Setup (Recommended)
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

### Development Setup (for frontend modifications)
If you want to modify the frontend, you'll need Node.js and npm:
```bash
cd ui/frontend
npm install
# Make your changes, then build
npm run build
```

### CLI Setup
```bash
# Setup /etc/proxychains.conf to use proxied system or alias proxychains command to a benign action

git clone https://github.com/RobotOperator/Eve.git
cd Eve

# Get initial token using API username and password, basic authentication string, or an already obtained Bearer token
# API port is usually either 443 or 8443 for local instances
python3 token_ApplePy.py --username api_admin --password 'my_pass123!@#' --jamf_server https://test.jamfcloud.com --api_port 443
```

## Usage

### Web UI (Recommended)
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

### Features
- **Modern Web UI**: Clean, responsive interface with dark mode support
- **Policy Editor**: Advanced XML editor with syntax highlighting, auto-completion, and helper pane
- **Extension Attributes**: Create and manage computer extension attributes with templates
- **Token Management**: Automatic token refresh for uninterrupted sessions
- **Multi-Auth Support**: Both OAuth2 and username/password authentication

###  CLI Tools
### Enumerating Computers
```
#Searching for computers with ADM_ the same as a simple search in the GUI
python3 search_ApplePy.py --jamf_server https://test.jamfcloud.com --api_port 443 --search_string "ADM_"

#Get computer details with UDID
./computer_details_by_id.sh <JAMFURL:PORT> <Bearer Token> <Computer ID>
./computer_details_by_id.sh https://test.jamfcloud.com:443 'eyxxx' 1029
```
### Scripts
```
#Get script contents by script id
./get_script_contents.sh <JAMFURL:PORT> <Bearer Token> <Script ID>
./get_script_contents.sh https://test.jamfcloud.com:443 'eyxxx' 29

#Push new script to the JAMF server, requires the source script to have quotes escaped/prepped. Highly recommend base64 encoding scripts and decoding the content to be executed
./push_script.sh <JAMFURL:PORT> <Bearer Token> <Path to Script> <New Script Name>
./push_script.sh https://test.jamfcloud.com:443 'eyxxx' ~/Eve/script6.txt 'Updated_System_Check'

#Delete scripts by id
./delete_script_by_id.sh <JAMFURL:PORT> <Bearer Token> <Script ID>
./push_script.sh https://test.jamfcloud.com:443 'eyxxx' 29
```
### Policies
```
#Delete policy by id
python3 policy_Applepy.py --bearer_token 'eyxxxx' --jamf_server https://test.jamfcloud.com --action delete --policy_id 493 --api_port 443

#Push new policy to execute scripts on target computers specified by ids, update computer ids embedded within the zsh script for now
./push_policy.zsh <JAMFURL:PORT> <Bearer Token> <Script ID to Execute> <New Policy Name>
./push_policy.zsh https://test.jamfcloud.com 'eyxxxx' 29 'New_Compliance_Policy'

#Retrive policy logs for a specific computer by supplying the UDID
./policy_logs_by_udid.sh <JAMFURL:PORT> <Bearer Token> <Computer UDID>
./policy_logs_by_udid.sh https://test.jamfcloud.com 'eyxxxx' AB5XDXXXX
```
### Privileges
```
#Update privileges of a target account id, admin.xml serves as a template for granting admin privileges and is statically specified in script
./update_privileges.sh <JAMFURL:PORT> <Bearer Token> <Account ID>
./update_privileges.sh https://test.jamfcloud.com 'eyxxxx' 285
```

## Planned Work

## Contributors
<a href="https://github.com/MayerDaniel">Daniel Mayer</a>


