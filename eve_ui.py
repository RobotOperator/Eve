from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import base64
import os
import sys
import json
from datetime import datetime, timedelta

# Add the eve directory to the Python path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the eve modules
import accounts
import computers
import policies
import scripts
import api
import auth

app = Flask(__name__, static_folder='ui/frontend/build', static_url_path='')
CORS(app)

# Store tokens temporarily (in production, use a proper session store)
tokens = {}

# Store authentication credentials for token refresh
auth_credentials = {}

@app.route('/')
def serve():
    """Serve the React app"""
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except:
        # Fallback if build folder doesn't exist
        return "Build folder not found. Run 'npm run build' in the frontend directory first.", 404

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files and fallback to index.html for client-side routing"""
    try:
        return send_from_directory(app.static_folder, path)
    except:
        # Fallback to index.html for client-side routing
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    """Authenticate with Jamf API using either OAuth2 client credentials or username/password"""
    try:
        data = request.json
        jamf_url = data.get('url', '').rstrip('/')
        auth_method = data.get('auth_method', 'oauth2')  # 'oauth2' or 'username_password'
        
        if not jamf_url:
            return jsonify({'error': 'Jamf URL is required'}), 400
        
        if auth_method == 'oauth2':
            return authenticate_oauth2(data, jamf_url)
        elif auth_method == 'username_password':
            return authenticate_username_password(data, jamf_url)
        else:
            return jsonify({'error': 'Invalid authentication method'}), 400
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

def authenticate_oauth2(data, jamf_url):
    """Authenticate using OAuth2 client credentials"""
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    
    if not all([client_id, client_secret]):
        return jsonify({'error': 'Client ID and Client Secret are required for OAuth2'}), 400
    
    # Prepare authentication
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    # Make token request
    token_url = f"{jamf_url}/api/oauth/token"
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    token_data = {
        'grant_type': 'client_credentials'
    }
    
    response = requests.post(token_url, headers=headers, data=token_data)
    
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info.get('access_token')
        
        # Store token (in production, use proper session management)
        session_id = f"oauth2_{client_id}_{jamf_url.replace('://', '_').replace('/', '_')}"
        tokens[session_id] = {
            'access_token': access_token,
            'jamf_url': jamf_url,
            'auth_method': 'oauth2',
            'expires_in': token_info.get('expires_in', 3600)
        }
        
        # Store credentials for token refresh
        auth_credentials[session_id] = {
            'auth_method': 'oauth2',
            'jamf_url': jamf_url,
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'auth_method': 'oauth2',
            'expires_in': token_info.get('expires_in', 3600)
        })
    else:
        return jsonify({
            'error': f'OAuth2 authentication failed: {response.status_code}',
            'message': response.text
        }), 401

def authenticate_username_password(data, jamf_url):
    """Authenticate using username and password"""
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({'error': 'Username and Password are required'}), 400
    
    # Prepare authentication for username/password
    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    # Make token request to the v1 auth endpoint
    token_url = f"{jamf_url}/api/v1/auth/token"
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Accept': 'application/json'
    }
    
    response = requests.post(token_url, headers=headers)
    
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info.get('token')
        
        # Store token (in production, use proper session management)
        session_id = f"userpass_{username}_{jamf_url.replace('://', '_').replace('/', '_')}"
        tokens[session_id] = {
            'access_token': access_token,
            'jamf_url': jamf_url,
            'auth_method': 'username_password',
            'expires_in': token_info.get('expires', 1800)  # Usually 30 minutes for username/password
        }
        
        # Store credentials for token refresh
        auth_credentials[session_id] = {
            'auth_method': 'username_password',
            'jamf_url': jamf_url,
            'username': username,
            'password': password
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'auth_method': 'username_password',
            'expires_in': token_info.get('expires', 1800)
        })
    else:
        return jsonify({
            'error': f'Username/Password authentication failed: {response.status_code}',
            'message': response.text
        }), 401

@app.route('/api/jamf/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def jamf_proxy(endpoint):
    """Proxy requests to Jamf API with authentication"""
    try:
        session_id = request.headers.get('X-Session-ID')
        if not session_id or session_id not in tokens:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        token_info = tokens[session_id]
        jamf_url = token_info['jamf_url']
        access_token = token_info['access_token']
        auth_method = token_info['auth_method']
        
        # Prepare request to Jamf API
        url = f"{jamf_url}/api/{endpoint}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Forward the request
        if request.method == 'GET':
            response = requests.get(url, headers=headers, params=request.args)
        elif request.method == 'POST':
            response = requests.post(url, headers=headers, json=request.json)
        elif request.method == 'PUT':
            response = requests.put(url, headers=headers, json=request.json)
        elif request.method == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        return jsonify(response.json() if response.content else {}), response.status_code
        
    except Exception as e:
        return jsonify({'error': f'Proxy error: {str(e)}'}), 500

# Helper function to get token info from session
def get_token_info(session_id):
    if not session_id or session_id not in tokens:
        return None
    return tokens[session_id]

# Accounts API endpoints
@app.route('/api/accounts', methods=['GET'])
def get_accounts_endpoint():
    """Get all accounts"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 401
    
    result, status_code, error = make_jamf_request(session_id, 'GET', '/JSSResource/accounts')
    
    if error:
        return jsonify({'error': error}), status_code
    
    # Extract users from the response
    users = result.get('accounts', {}).get('users', [])
    return jsonify(users), status_code

@app.route('/api/groups', methods=['GET'])
def get_groups_endpoint():
    """Get all groups"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 401
    
    result, status_code, error = make_jamf_request(session_id, 'GET', '/JSSResource/accounts')
    
    if error:
        return jsonify({'error': error}), status_code
    
    # Extract groups from the response
    groups = result.get('accounts', {}).get('groups', [])
    return jsonify(groups), status_code

@app.route('/api/groups/<int:group_id>', methods=['GET'])
def get_group_by_id_endpoint(group_id):
    """Get group by ID"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 401
    
    result, status_code, error = make_jamf_request(session_id, 'GET', f'/JSSResource/accounts/groupid/{group_id}')
    
    if error:
        return jsonify({'error': error}), status_code
    
    return jsonify(result), status_code

# Computers API endpoints
@app.route('/api/computers/search/<search_string>', methods=['GET'])
def search_computers_endpoint(search_string):
    """Search computers"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 401
    
    # Add wildcards around search string like the original implementation
    updated_string = '*' + search_string + '*'
    result, status_code, error = make_jamf_request(session_id, 'GET', f'/JSSResource/computers/match/{updated_string}')
    
    if error:
        return jsonify({'error': error}), status_code
    
    return jsonify(result), status_code

@app.route('/api/computers/udid/<udid>', methods=['GET'])
def get_computer_by_udid_endpoint(udid):
    """Get computer by UDID"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 401
    
    result, status_code, error = make_jamf_request(session_id, 'GET', f'/JSSResource/computers/udid/{udid}')
    
    if error:
        return jsonify({'error': error}), status_code
    
    return jsonify(result), status_code

@app.route('/api/computers/id/<int:computer_id>', methods=['GET'])
def get_computer_by_id_endpoint(computer_id):
    """Get computer by ID"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 401
    
    result, status_code, error = make_jamf_request(session_id, 'GET', f'/JSSResource/computers/id/{computer_id}')
    
    if error:
        return jsonify({'error': error}), status_code
    
    return jsonify(result), status_code

# Policies API endpoints
@app.route('/api/policies', methods=['GET'])
def get_policies_endpoint():
    """Get all policies"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 401
    
    result, status_code, error = make_jamf_request(session_id, 'GET', '/JSSResource/policies')
    
    if error:
        return jsonify({'error': error}), status_code
    
    return jsonify(result), status_code

@app.route('/api/policies/<int:policy_id>', methods=['GET'])
def get_policy_by_id_endpoint(policy_id):
    """Get policy by ID"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 401
    
    result, status_code, error = make_jamf_request(session_id, 'GET', f'/JSSResource/policies/id/{policy_id}')
    
    if error:
        return jsonify({'error': error}), status_code
    
    return jsonify(result), status_code

@app.route('/api/policies/<int:policy_id>', methods=['DELETE'])
def delete_policy_endpoint(policy_id):
    """Delete policy by ID"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 401
    
    result, status_code, error = make_jamf_request(session_id, 'DELETE', f'/JSSResource/policies/id/{policy_id}')
    
    if error:
        return jsonify({'error': error}), status_code
    
    return jsonify({'success': True, 'message': 'Policy deleted successfully'}), 200

@app.route('/api/policies/<int:policy_id>/xml', methods=['GET'])
def get_policy_xml_endpoint(policy_id):
    """Get policy XML by ID"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 401
    
    # For XML requests, we need to use the direct approach with proper headers
    if session_id not in tokens:
        return jsonify({'error': 'Invalid session'}), 401
    
    token_info = tokens[session_id]
    jamf_url = token_info['jamf_url']
    access_token = token_info['access_token']
    
    url = f"{jamf_url}/JSSResource/policies/id/{policy_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/xml',
        'Accept': 'application/xml'
    }
    
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(url, headers=headers, verify=False)
        
        # Handle 401 for XML requests
        if response.status_code == 401:
            new_token = refresh_token(session_id)
            if new_token:
                headers['Authorization'] = f'Bearer {new_token}'
                response = requests.get(url, headers=headers, verify=False)
            else:
                return jsonify({'error': 'Token refresh failed. Please re-authenticate.'}), 401
        
        if response.status_code == 200:
            return jsonify({'xml': response.text}), 200
        else:
            return jsonify({'error': f'Failed to get policy XML: {response.status_code}'}), response.status_code
    
    except Exception as e:
        return jsonify({'error': f'Error getting policy XML: {str(e)}'}), 500

@app.route('/api/policies', methods=['POST'])
def create_policy_endpoint():
    """Create a new policy"""
    try:
        session_id = request.headers.get('X-Session-ID')
        token_info = get_token_info(session_id)
        if not token_info:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        data = request.json
        policy_xml = data.get('xml')
        
        if not policy_xml:
            return jsonify({'error': 'Policy XML is required'}), 400
        
        # Create a temporary file with the policy XML
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as temp_file:
            temp_file.write(policy_xml)
            temp_file_path = temp_file.name
        
        try:
            result = policies.create_policy(token_info['jamf_url'], token_info['access_token'], temp_file_path)
            return jsonify({'success': True, 'message': 'Policy created successfully', 'result': result})
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
    except Exception as e:
        return jsonify({'error': f'Error creating policy: {str(e)}'}), 500

@app.route('/api/policies/<int:policy_id>', methods=['PUT'])
def update_policy_endpoint(policy_id):
    """Update policy by ID"""
    try:
        session_id = request.headers.get('X-Session-ID')
        token_info = get_token_info(session_id)
        if not token_info:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        data = request.json
        policy_xml = data.get('xml')
        
        if not policy_xml:
            return jsonify({'error': 'Policy XML is required'}), 400
        
        # Create a temporary file with the policy XML
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as temp_file:
            temp_file.write(policy_xml)
            temp_file_path = temp_file.name
        
        try:
            result = policies.update_policy_by_id(token_info['jamf_url'], token_info['access_token'], policy_id, temp_file_path)
            return jsonify({'success': True, 'message': 'Policy updated successfully', 'result': result})
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
    except Exception as e:
        return jsonify({'error': f'Error updating policy: {str(e)}'}), 500

@app.route('/api/policy-templates', methods=['GET'])
def get_policy_templates_endpoint():
    """Get available policy templates"""
    try:
        templates = []
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        
        # Define template metadata
        template_info = {
            'policy_template_run_script.xml': {
                'name': 'Run Script Policy',
                'description': 'Policy template for running scripts on target computers',
                'icon': '📜'
            },
            'policy_template_execute_command.xml': {
                'name': 'Execute Command Policy', 
                'description': 'Policy template for executing shell commands on target computers',
                'icon': '⚡'
            }
        }
        
        # Look for policy template files
        for filename in os.listdir(templates_dir):
            if filename.startswith('policy_template_') and filename.endswith('.xml'):
                template_path = os.path.join(templates_dir, filename)
                if os.path.isfile(template_path):
                    with open(template_path, 'r') as f:
                        content = f.read()
                    
                    template_data = template_info.get(filename, {
                        'name': filename.replace('policy_template_', '').replace('.xml', '').replace('_', ' ').title(),
                        'description': f'Policy template: {filename}',
                        'icon': '📋'
                    })
                    
                    templates.append({
                        'id': filename,
                        'name': template_data['name'],
                        'description': template_data['description'],
                        'icon': template_data['icon'],
                        'content': content
                    })
        
        return jsonify({'templates': templates})
    except Exception as e:
        return jsonify({'error': f'Error getting policy templates: {str(e)}'}), 500

# Scripts API endpoints
@app.route('/api/scripts', methods=['GET'])
def get_scripts_endpoint():
    """Get all scripts"""
    try:
        session_id = request.headers.get('X-Session-ID')
        token_info = get_token_info(session_id)
        if not token_info:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        result = scripts.get_scripts(token_info['jamf_url'], token_info['access_token'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Error getting scripts: {str(e)}'}), 500

@app.route('/api/scripts', methods=['POST'])
def create_script_endpoint():
    """Create a new script"""
    try:
        session_id = request.headers.get('X-Session-ID')
        token_info = get_token_info(session_id)
        if not token_info:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        data = request.json
        script_name = data.get('name')
        script_content = data.get('content')
        
        if not script_name or not script_content:
            return jsonify({'error': 'Script name and content are required'}), 400
        
        # Create a temporary file with the script content
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
            temp_file.write(script_content)
            temp_file_path = temp_file.name
        
        try:
            result = scripts.create_script(token_info['jamf_url'], token_info['access_token'], script_name, temp_file_path)
            return jsonify({'success': True, 'message': 'Script created successfully', 'result': result})
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
    except Exception as e:
        return jsonify({'error': f'Error creating script: {str(e)}'}), 500

@app.route('/api/scripts/<int:script_id>', methods=['PUT'])
def update_script_endpoint(script_id):
    """Update script by ID"""
    try:
        session_id = request.headers.get('X-Session-ID')
        token_info = get_token_info(session_id)
        if not token_info:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        data = request.json
        script_content = data.get('content')
        
        if not script_content:
            return jsonify({'error': 'Script content is required'}), 400
        
        # Create a temporary file with the script content
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
            temp_file.write(script_content)
            temp_file_path = temp_file.name
        
        try:
            result = scripts.update_script_by_id(token_info['jamf_url'], token_info['access_token'], script_id, temp_file_path)
            return jsonify({'success': True, 'message': 'Script updated successfully', 'result': result})
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
    except Exception as e:
        return jsonify({'error': f'Error updating script: {str(e)}'}), 500

@app.route('/api/scripts/<int:script_id>', methods=['GET'])
def get_script_by_id_endpoint(script_id):
    """Get script by ID"""
    try:
        session_id = request.headers.get('X-Session-ID')
        token_info = get_token_info(session_id)
        if not token_info:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        result = scripts.get_script_by_id(token_info['jamf_url'], token_info['access_token'], script_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Error getting script: {str(e)}'}), 500

@app.route('/api/scripts/<int:script_id>', methods=['DELETE'])
def delete_script_endpoint(script_id):
    """Delete script by ID"""
    try:
        session_id = request.headers.get('X-Session-ID')
        token_info = get_token_info(session_id)
        if not token_info:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        result = scripts.delete_script_by_id(token_info['jamf_url'], token_info['access_token'], script_id)
        return jsonify({'success': True, 'message': 'Script deleted successfully'})
    except Exception as e:
        return jsonify({'error': f'Error deleting script: {str(e)}'}), 500

# API Management endpoints
@app.route('/api/api-roles', methods=['GET'])
def get_api_roles_endpoint():
    """Get all API roles"""
    try:
        session_id = request.headers.get('X-Session-ID')
        token_info = get_token_info(session_id)
        if not token_info:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        result = api.get_api_roles(token_info['jamf_url'], token_info['access_token'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Error getting API roles: {str(e)}'}), 500

@app.route('/api/api-clients', methods=['GET'])
def get_api_clients_endpoint():
    """Get all API clients"""
    try:
        session_id = request.headers.get('X-Session-ID')
        token_info = get_token_info(session_id)
        if not token_info:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        result = api.get_api_clients(token_info['jamf_url'], token_info['access_token'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Error getting API clients: {str(e)}'}), 500

@app.route('/api/api-roles/<int:role_id>', methods=['GET'])
def get_role_by_id_endpoint(role_id):
    """Get API role by ID"""
    try:
        session_id = request.headers.get('X-Session-ID')
        token_info = get_token_info(session_id)
        if not token_info:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        result = api.get_role_by_id(token_info['jamf_url'], token_info['access_token'], role_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Error getting API role: {str(e)}'}), 500

# Auth endpoints
@app.route('/api/token-details', methods=['GET'])
def get_token_details_endpoint():
    """Get current token details"""
    try:
        session_id = request.headers.get('X-Session-ID')
        token_info = get_token_info(session_id)
        if not token_info:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        result = auth.get_token_details(token_info['jamf_url'], token_info['access_token'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Error getting token details: {str(e)}'}), 500

def refresh_token(session_id):
    """Refresh an expired token using stored credentials"""
    if session_id not in auth_credentials:
        return None
    
    creds = auth_credentials[session_id]
    auth_method = creds['auth_method']
    jamf_url = creds['jamf_url']
    
    try:
        if auth_method == 'oauth2':
            # OAuth2 token refresh
            client_id = creds['client_id']
            client_secret = creds['client_secret']
            
            auth_string = f"{client_id}:{client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            token_url = f"{jamf_url}/api/oauth/token"
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            token_data = {'grant_type': 'client_credentials'}
            response = requests.post(token_url, headers=headers, data=token_data)
            
            if response.status_code == 200:
                token_info = response.json()
                access_token = token_info.get('access_token')
                
                # Update stored token
                tokens[session_id] = {
                    'access_token': access_token,
                    'jamf_url': jamf_url,
                    'auth_method': 'oauth2',
                    'expires_in': token_info.get('expires_in', 3600),
                    'refreshed_at': datetime.now()
                }
                return access_token
                
        elif auth_method == 'username_password':
            # Username/password token refresh
            username = creds['username']
            password = creds['password']
            
            auth_string = f"{username}:{password}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            token_url = f"{jamf_url}/api/v1/auth/token"
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Accept': 'application/json'
            }
            
            response = requests.post(token_url, headers=headers)
            
            if response.status_code == 200:
                token_info = response.json()
                access_token = token_info.get('token')
                
                # Update stored token
                tokens[session_id] = {
                    'access_token': access_token,
                    'jamf_url': jamf_url,
                    'auth_method': 'username_password',
                    'expires_in': token_info.get('expires', 1800),
                    'refreshed_at': datetime.now()
                }
                return access_token
                
    except Exception as e:
        print(f"Token refresh failed for session {session_id}: {str(e)}")
        
    return None

def make_jamf_request(session_id, method, endpoint, **kwargs):
    """Make a request to Jamf API with automatic token refresh on 401"""
    if session_id not in tokens:
        return None, 401, "Invalid session"
    
    token_info = tokens[session_id]
    jamf_url = token_info['jamf_url']
    access_token = token_info['access_token']
    
    url = f"{jamf_url}/{endpoint.lstrip('/')}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Add any additional headers
    if 'headers' in kwargs:
        headers.update(kwargs['headers'])
        del kwargs['headers']
    
    # Make the initial request
    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        
        # If we get a 401, try to refresh the token and retry
        if response.status_code == 401:
            print(f"Token expired for session {session_id}, attempting refresh...")
            new_token = refresh_token(session_id)
            
            if new_token:
                print(f"Token refreshed successfully for session {session_id}")
                # Update headers with new token and retry
                headers['Authorization'] = f'Bearer {new_token}'
                response = requests.request(method, url, headers=headers, **kwargs)
            else:
                print(f"Token refresh failed for session {session_id}")
                # Remove invalid session
                if session_id in tokens:
                    del tokens[session_id]
                if session_id in auth_credentials:
                    del auth_credentials[session_id]
                return None, 401, "Token refresh failed. Please re-authenticate."
        
        return response.json() if response.content else {}, response.status_code, None
        
    except requests.exceptions.RequestException as e:
        return None, 500, f"Request error: {str(e)}"
    except json.JSONDecodeError:
        return {}, response.status_code, None
    except Exception as e:
        return None, 500, f"Unexpected error: {str(e)}"

# Add an endpoint to check token refresh status
@app.route('/api/token/status', methods=['GET'])
def token_status():
    """Check token status and provide refresh information"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 401
    
    if session_id not in tokens:
        return jsonify({'error': 'Invalid session'}), 401
    
    token_info = tokens[session_id]
    auth_available = session_id in auth_credentials
    
    return jsonify({
        'session_id': session_id,
        'auth_method': token_info.get('auth_method'),
        'expires_in': token_info.get('expires_in'),
        'refresh_available': auth_available,
        'refreshed_at': token_info.get('refreshed_at').isoformat() if token_info.get('refreshed_at') else None
    })

# Add a simple test endpoint to trigger 401 scenarios
@app.route('/api/test/protected', methods=['GET'])
def test_protected():
    """Test endpoint to verify token refresh functionality"""
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({'error': 'Session ID required'}), 401
    
    result, status_code, error = make_jamf_request(session_id, 'GET', '/api/v1/auth')
    
    if error:
        return jsonify({'error': error}), status_code
    
    return jsonify({
        'message': 'Token is valid',
        'auth_info': result
    }), status_code

if __name__ == '__main__':
    app.run(debug=True, port=8003)