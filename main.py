#!/bin/env python3
import importlib
import json
import os
import secrets
import string
import subprocess
import sys
import time
import webbrowser
from datetime import datetime, timezone
from getpass import getpass
from types import SimpleNamespace
from xml.etree import ElementTree as ET


DEPENDENCIES = [
    ("dateutil.parser", "python-dateutil"),
    ("requests", "requests"),
    ("urllib3", "urllib3"),
]

MODULE_NAMES = (
    "auth",
    "accounts",
    "api",
    "computers",
    "policies",
    "scripts",
    "sso",
)

TEMPLATES_DIR = os.path.join(os.getcwd(), "templates")


def check_dependencies():
    import_error = []

    for module_name, package_name in DEPENDENCIES:
        try:
            importlib.import_module(module_name)
        except ImportError:
            import_error.append(package_name)

    if import_error:
        missing_modules = " ".join(import_error)
        print(
            "Required module(s) [",
            missing_modules,
            "] threw errors on import, install by running: python3 -m pip install",
            missing_modules,
        )
        return False

    return True


def load_modules():
    loaded = {}
    for name in MODULE_NAMES:
        loaded[name] = importlib.import_module(name)
    return loaded

class ProcessNotRunningError(Exception):
    pass


def ensure_data_dir():
    if not os.path.isdir("./.data"):
        os.makedirs("./.data")
        print("[i] - Directory .data created in current folder. -[i]")


def prompt_choice(title, options):
    print(title)
    for index, option in enumerate(options, 1):
        print(f"{index}. {option}")

    while True:
        choice = input("> ").strip()
        if choice.isdigit():
            selected = int(choice)
            if 1 <= selected <= len(options):
                return selected
        print("X - Invalid option selected. - X")


def prompt_text(label, secret=False, allow_empty=False):
    while True:
        if secret:
            value = getpass(f"{label}: ")
        else:
            value = input(f"{label}: ")

        value = value.strip()
        if value or allow_empty:
            return value
        print("X - Input is required. - X")


def prompt_optional_text(label):
    return input(f"{label}: ").strip()


def prompt_optional_secret(label):
    return getpass(f"{label}: ").strip()


def prompt_file_path(label):
    value = prompt_text(label)
    return os.path.abspath(os.path.expanduser(value))


def prompt_yes_no(label, default=False):
    suffix = " [Y/n]: " if default else " [y/N]: "
    value = input(f"{label}{suffix}").strip().lower()
    if not value:
        return default
    return value in ("y", "yes")


def print_result(output):
    if isinstance(output, (dict, list)):
        print(json.dumps(output, indent=2))
    else:
        print(output)


def template_file_path(filename):
    return os.path.join(TEMPLATES_DIR, filename)


def make_temp_path(prefix, suffix):
    ensure_data_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    token = secrets.token_hex(4)
    return os.path.join(".data", f"{prefix}_{stamp}_{token}{suffix}")


def read_json_file(path):
    with open(path, "r") as handle:
        return json.load(handle)


def write_json_file(path, data):
    with open(path, "w") as handle:
        json.dump(data, handle, indent=2)


def load_xml_root(path):
    return ET.parse(path).getroot()


def write_xml_root(path, root):
    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def set_xml_text(root, xpath, value):
    element = root.find(xpath)
    if element is None:
        raise Exception(f"X - Required XML element {xpath} was not found in template. - X")
    element.text = value


def random_suffix(length=6):
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def random_password(length=18):
    alphabet = string.ascii_letters + string.digits + "!@#$%^*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_parser_module():
    return importlib.import_module("dateutil.parser")


def parse_timestamp(value):
    if not value:
        return None

    try:
        parsed = get_parser_module().parse(value)
    except Exception:
        cleaned = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(cleaned)
        except Exception:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def load_cached_session():
    token_path = os.path.join(".", ".data", "token")
    if not os.path.exists(token_path):
        return None

    try:
        with open(token_path, "r") as handle:
            data = json.load(handle)
    except Exception:
        return None

    token = data.get("token")
    server = data.get("server")
    if not token or not server:
        return None

    expires = parse_timestamp(data.get("expires"))
    if expires is not None and expires <= datetime.now(timezone.utc):
        return None

    return {
        "token": token,
        "server": server,
        "auth_method": "cached_token",
    }


def save_cached_session(result_json):
    ensure_data_dir()
    with open("./.data/token", "w") as handle:
        handle.write(json.dumps(result_json))


def build_auth_args(**kwargs):
    values = {
        "username": None,
        "password": None,
        "basic_auth": None,
        "bearer_token": None,
        "api_client_id": None,
        "api_client_secret": None,
        "jamf_server": None,
        "api_port": None,
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def prompt_server_args():
    jamf_server = prompt_text("JAMF Pro server").rstrip("/")
    api_port = prompt_optional_text("API port (optional)")
    if not api_port:
        api_port = None
    return jamf_server, api_port


def show_token_details(modules, state):
    try:
        print(modules["auth"].get_token_details(state["server"], state["token"]))
    except Exception as exc:
        print(exc)


def fetch_token_details(modules, state):
    try:
        return modules["auth"].get_token_details(state["server"], state["token"])
    except Exception as exc:
        print(exc)
        return None


def complete_authentication(modules, state, args, show_details):
    auth_module = modules["auth"]
    try:
        server = auth_module.create_server_string(args)
        bearer_string = auth_module.auth_token(server, args)
    except Exception as exc:
        print(exc)
        return False
    if "token" not in bearer_string:
        print("X- Failed to retrieve token. Please check your credentials. -X")
        print(bearer_string)
        return False

    print(bearer_string)
    result_json = json.loads(bearer_string)
    save_cached_session(result_json)

    state["server"] = server
    state["token"] = result_json.get("token")
    state["auth_method"] = "stored_token"

    if show_details:
        show_token_details(modules, state)

    return True


def authenticate_user_account(modules, state):
    while True:
        choice = prompt_choice(
            "Select account credential method:",
            [
                "Username + Password",
                "Basic Credentials",
                "Back",
            ],
        )

        if choice == 1:
            jamf_server, api_port = prompt_server_args()
            username = prompt_text("Username")
            password = prompt_text("Password", secret=True)
            show_details = prompt_yes_no("Display token details after authentication?")
            args = build_auth_args(
                username=username,
                password=password,
                jamf_server=jamf_server,
                api_port=api_port,
            )
            complete_authentication(modules, state, args, show_details)
            return

        if choice == 2:
            jamf_server, api_port = prompt_server_args()
            basic_auth = prompt_text("Base64 basic authentication string", secret=True)
            show_details = prompt_yes_no("Display token details after authentication?")
            args = build_auth_args(
                basic_auth=basic_auth,
                jamf_server=jamf_server,
                api_port=api_port,
            )
            complete_authentication(modules, state, args, show_details)
            return

        return


def authenticate_api_client(modules, state):
    jamf_server, api_port = prompt_server_args()
    api_client_id = prompt_text("API client ID")
    api_client_secret = prompt_text("API client secret", secret=True)
    show_details = prompt_yes_no("Display token details after authentication?")

    args = build_auth_args(
        api_client_id=api_client_id,
        api_client_secret=api_client_secret,
        jamf_server=jamf_server,
        api_port=api_port,
    )
    complete_authentication(modules, state, args, show_details)


def authenticate_bearer_token(modules, state):
    jamf_server, api_port = prompt_server_args()
    bearer_token = prompt_text("Bearer token", secret=True)
    args = build_auth_args(jamf_server=jamf_server, api_port=api_port)
    server = modules["auth"].create_server_string(args)

    state["server"] = server
    state["token"] = bearer_token
    state["auth_method"] = "bearer_token"

    if prompt_yes_no("Display token details after authentication?"):
        show_token_details(modules, state)


def auth_menu(modules, state):
    while True:
        choice = prompt_choice(
            "Select authentication type:",
            [
                "User Account",
                "API Client",
                "Bearer Token",
                "Back",
            ],
        )

        if choice == 1:
            authenticate_user_account(modules, state)
        elif choice == 2:
            authenticate_api_client(modules, state)
        elif choice == 3:
            authenticate_bearer_token(modules, state)
        else:
            return


def ensure_authenticated(modules, state):
    if state.get("server") and state.get("token"):
        return True

    cached = load_cached_session()
    if cached:
        state.update(cached)
        print("[i] - Loaded cached token from ./.data/token. - [i]")
        return True

    print("X - Authentication is required before running this action. - X")
    auth_menu(modules, state)
    return bool(state.get("server") and state.get("token"))


def run_authenticated_action(modules, state, func, *args):
    if not ensure_authenticated(modules, state):
        return

    try:
        result = func(state["server"], state["token"], *args)
        print_result(result)
    except Exception as exc:
        print(exc)


def accounts_menu(modules, state):
    accounts_module = modules["accounts"]

    while True:
        choice = prompt_choice(
            "Select accounts option:",
            [
                "Get Accounts",
                "Get Account By ID",
                "Create Account",
                "Update Account By ID",
                "Delete Account By ID",
                "Get Groups",
                "Get Group By ID",
                "Create Group",
                "Update Group By ID",
                "Delete Group By ID",
                "Back",
            ],
        )

        if choice == 1:
            run_authenticated_action(modules, state, accounts_module.get_accounts)
        elif choice == 2:
            run_authenticated_action(
                modules,
                state,
                accounts_module.get_account_by_id,
                prompt_text("Account ID"),
            )
        elif choice == 3:
            run_authenticated_action(
                modules,
                state,
                accounts_module.create_account,
                prompt_file_path("Input XML file"),
            )
        elif choice == 4:
            run_authenticated_action(
                modules,
                state,
                accounts_module.update_account_by_id,
                prompt_text("Account ID"),
                prompt_file_path("Input XML file"),
            )
        elif choice == 5:
            run_authenticated_action(
                modules,
                state,
                accounts_module.delete_account_by_id,
                prompt_text("Account ID"),
            )
        elif choice == 6:
            run_authenticated_action(modules, state, accounts_module.get_groups)
        elif choice == 7:
            run_authenticated_action(
                modules,
                state,
                accounts_module.get_group_by_id,
                prompt_text("Group ID"),
            )
        elif choice == 8:
            run_authenticated_action(
                modules,
                state,
                accounts_module.create_group,
                prompt_file_path("Input XML file"),
            )
        elif choice == 9:
            run_authenticated_action(
                modules,
                state,
                accounts_module.update_group_by_id,
                prompt_text("Group ID"),
                prompt_file_path("Input XML file"),
            )
        elif choice == 10:
            run_authenticated_action(
                modules,
                state,
                accounts_module.delete_group_by_id,
                prompt_text("Group ID"),
            )
        else:
            return


def api_menu(modules, state):
    api_module = modules["api"]

    while True:
        choice = prompt_choice(
            "Select API option:",
            [
                "Get API Roles",
                "Get API Clients",
                "Get Role By ID",
                "Get Client By ID",
                "Create API Role",
                "Update API Role By ID",
                "Delete API Role By ID",
                "Create API Client",
                "Get Client Credentials",
                "Update API Client By ID",
                "Delete API Client By ID",
                "Back",
            ],
        )

        if choice == 1:
            run_authenticated_action(modules, state, api_module.get_api_roles)
        elif choice == 2:
            run_authenticated_action(modules, state, api_module.get_api_clients)
        elif choice == 3:
            run_authenticated_action(
                modules,
                state,
                api_module.get_role_by_id,
                prompt_text("Role ID"),
            )
        elif choice == 4:
            run_authenticated_action(
                modules,
                state,
                api_module.get_client_by_id,
                prompt_text("Client ID"),
            )
        elif choice == 5:
            run_authenticated_action(
                modules,
                state,
                api_module.create_api_role,
                prompt_file_path("Input JSON file"),
            )
        elif choice == 6:
            run_authenticated_action(
                modules,
                state,
                api_module.update_api_role_by_id,
                prompt_text("Role ID"),
                prompt_file_path("Input JSON file"),
            )
        elif choice == 7:
            run_authenticated_action(
                modules,
                state,
                api_module.delete_api_role_by_id,
                prompt_text("Role ID"),
            )
        elif choice == 8:
            run_authenticated_action(
                modules,
                state,
                api_module.create_api_client,
                prompt_file_path("Input JSON file"),
            )
        elif choice == 9:
            run_authenticated_action(
                modules,
                state,
                api_module.get_client_credentials,
                prompt_text("Client ID"),
            )
        elif choice == 10:
            run_authenticated_action(
                modules,
                state,
                api_module.update_api_client_by_id,
                prompt_text("Client ID"),
                prompt_file_path("Input JSON file"),
            )
        elif choice == 11:
            run_authenticated_action(
                modules,
                state,
                api_module.delete_api_client_by_id,
                prompt_text("Client ID"),
            )
        else:
            return


def computers_menu(modules, state):
    computers_module = modules["computers"]

    while True:
        choice = prompt_choice(
            "Select computers option:",
            [
                "Get Computers",
                "Search For Computer By String",
                "Get Computer By UDID",
                "Get Computer By ID",
                "Get Policy Logs By UDID",
                "Get Computer Extension Attributes",
                "Get Computer Extension Attribute By ID",
                "Create Computer Extension Attribute",
                "Update Computer Extension Attribute By ID",
                "Delete Computer Extension Attribute By ID",
                "Back",
            ],
        )

        if choice == 1:
            run_authenticated_action(modules, state, computers_module.get_computers)
        elif choice == 2:
            run_authenticated_action(
                modules,
                state,
                computers_module.get_computers,
                prompt_text("Search string"),
            )
        elif choice == 3:
            run_authenticated_action(
                modules,
                state,
                computers_module.get_computer_by_udid,
                prompt_text("Computer UDID"),
            )
        elif choice == 4:
            run_authenticated_action(
                modules,
                state,
                computers_module.get_computer_by_id,
                prompt_text("Computer ID"),
            )
        elif choice == 5:
            run_authenticated_action(
                modules,
                state,
                computers_module.get_policy_logs_by_udid,
                prompt_text("Computer UDID"),
            )
        elif choice == 6:
            run_authenticated_action(
                modules,
                state,
                computers_module.get_computer_extension_attributes,
            )
        elif choice == 7:
            run_authenticated_action(
                modules,
                state,
                computers_module.get_computer_extension_attribute_by_id,
                prompt_text("Extension Attribute ID"),
            )
        elif choice == 8:
            run_authenticated_action(
                modules,
                state,
                computers_module.create_computer_extension_attribute,
                prompt_file_path("Input XML file"),
            )
        elif choice == 9:
            run_authenticated_action(
                modules,
                state,
                computers_module.update_computer_extension_by_id,
                prompt_text("Extension Attribute ID"),
                prompt_file_path("Input XML file"),
            )
        elif choice == 10:
            run_authenticated_action(
                modules,
                state,
                computers_module.delete_computer_extension_by_id,
                prompt_text("Extension Attribute ID"),
            )
        else:
            return


def policies_menu(modules, state):
    policies_module = modules["policies"]

    while True:
        choice = prompt_choice(
            "Select policies option:",
            [
                "Get Policies",
                "Get Policy By ID",
                "Create Policy",
                "Update Policy By ID",
                "Delete Policy By ID",
                "Back",
            ],
        )

        if choice == 1:
            run_authenticated_action(modules, state, policies_module.get_policies)
        elif choice == 2:
            run_authenticated_action(
                modules,
                state,
                policies_module.get_policy_by_id,
                prompt_text("Policy ID"),
            )
        elif choice == 3:
            run_authenticated_action(
                modules,
                state,
                policies_module.create_policy,
                prompt_file_path("Input XML file"),
            )
        elif choice == 4:
            run_authenticated_action(
                modules,
                state,
                policies_module.update_policy_by_id,
                prompt_text("Policy ID"),
                prompt_file_path("Input XML file"),
            )
        elif choice == 5:
            run_authenticated_action(
                modules,
                state,
                policies_module.delete_policy_by_id,
                prompt_text("Policy ID"),
            )
        else:
            return


def scripts_menu(modules, state):
    scripts_module = modules["scripts"]

    while True:
        choice = prompt_choice(
            "Select scripts option:",
            [
                "Get Scripts",
                "Get Script By ID",
                "Create Script",
                "Update Script By ID",
                "Delete Script By ID",
                "Back",
            ],
        )

        if choice == 1:
            run_authenticated_action(modules, state, scripts_module.get_scripts)
        elif choice == 2:
            run_authenticated_action(
                modules,
                state,
                scripts_module.get_script_by_id,
                prompt_text("Script ID"),
            )
        elif choice == 3:
            run_authenticated_action(
                modules,
                state,
                scripts_module.create_script,
                prompt_text("Script name"),
                prompt_file_path("Input script file"),
            )
        elif choice == 4:
            run_authenticated_action(
                modules,
                state,
                scripts_module.update_script_by_id,
                prompt_text("Script ID"),
                prompt_file_path("Input script file"),
            )
        elif choice == 5:
            run_authenticated_action(
                modules,
                state,
                scripts_module.delete_script_by_id,
                prompt_text("Script ID"),
            )
        else:
            return


def sso_menu(modules, state):
    sso_module = modules["sso"]

    while True:
        choice = prompt_choice(
            "Select SSO option:",
            [
                "Get All SSO Configs",
                "Get SSO Config",
                "Get SSO History",
                "Get SSO Failover",
                "Regenerate SSO Failover",
                "Update SSO Config",
                "Disable SSO Config",
                "Generate SSO Certificate",
                "Get SSO Certificate",
                "Delete SSO Certificate",
                "Back",
            ],
        )

        if choice == 1:
            run_authenticated_action(modules, state, sso_module.get_all_sso_configs)
        elif choice == 2:
            run_authenticated_action(modules, state, sso_module.get_sso_config)
        elif choice == 3:
            run_authenticated_action(modules, state, sso_module.get_sso_history)
        elif choice == 4:
            run_authenticated_action(modules, state, sso_module.get_sso_failover)
        elif choice == 5:
            run_authenticated_action(modules, state, sso_module.regenerate_sso_failover)
        elif choice == 6:
            run_authenticated_action(
                modules,
                state,
                sso_module.update_sso_config,
                prompt_file_path("Input JSON file"),
            )
        elif choice == 7:
            run_authenticated_action(modules, state, sso_module.disable_sso_config)
        elif choice == 8:
            run_authenticated_action(modules, state, sso_module.generate_sso_cert)
        elif choice == 9:
            run_authenticated_action(modules, state, sso_module.get_sso_cert)
        elif choice == 10:
            run_authenticated_action(modules, state, sso_module.delete_sso_cert)
        else:
            return


def contains_any(text, values):
    for value in values:
        if value in text:
            return True
    return False


def collect_strings(value, bucket):
    if isinstance(value, dict):
        for item in value.values():
            collect_strings(item, bucket)
    elif isinstance(value, list):
        for item in value:
            collect_strings(item, bucket)
    elif isinstance(value, str):
        bucket.add(value)


def extract_permissions(token_details):
    try:
        details = json.loads(token_details)
    except Exception:
        return set()

    values = set()
    collect_strings(details, values)
    return values


def lazy_authenticate(modules, state):
    print("Oh great you're lazy... let me try and help.")
    # TODO: Add logic branch to check if authenticated already
    ensure_authenticated(modules, state)
    '''print("I know you are lazy, but I need some type of auth. material")

    choice = prompt_choice(
        "Select authentication material:",
        [
            "Username + Password",
            "Basic Auth",
            "Bearer Token",
            "Back",
        ],
    )

    if choice == 4:
        return None

    jamf_server, api_port = prompt_server_args()
    auth_module = modules["auth"]

    try:
        server = auth_module.create_server_string(
            build_auth_args(jamf_server=jamf_server, api_port=api_port)
        )
    except Exception as exc:
        print(exc)
        print("X - Credential material invalid or authentication failed. Returning to main menu. - X")
        return None

    try:
        if choice == 1:
            username = prompt_optional_text("Username")
            password = prompt_optional_secret("Password")
            if not username or not password:
                print("X - No credential material supplied. Returning to main menu. - X")
                return None
            bearer_string = auth_module.auth_token(
                server,
                build_auth_args(
                    username=username,
                    password=password,
                    jamf_server=jamf_server,
                    api_port=api_port,
                ),
            )
            if "token" not in bearer_string:
                raise Exception(bearer_string)
            result_json = json.loads(bearer_string)
            state["server"] = server
            state["token"] = result_json.get("token")
            state["auth_method"] = "lazy_username_password"
            save_cached_session(result_json)
        elif choice == 2:
            basic_auth = prompt_optional_secret("Base64 basic authentication string")
            if not basic_auth:
                print("X - No credential material supplied. Returning to main menu. - X")
                return None
            bearer_string = auth_module.auth_token(
                server,
                build_auth_args(
                    basic_auth=basic_auth,
                    jamf_server=jamf_server,
                    api_port=api_port,
                ),
            )
            if "token" not in bearer_string:
                raise Exception(bearer_string)
            result_json = json.loads(bearer_string)
            state["server"] = server
            state["token"] = result_json.get("token")
            state["auth_method"] = "lazy_basic_auth"
            save_cached_session(result_json)
        else:
            bearer_token = prompt_optional_secret("Bearer token")
            if not bearer_token:
                print("X - No credential material supplied. Returning to main menu. - X")
                return None
            state["server"] = server
            state["token"] = bearer_token
            state["auth_method"] = "lazy_bearer_token"
    except Exception as exc:
        print(exc)
        print("X - Credential material invalid or authentication failed. Returning to main menu. - X")
        state.pop("server", None)
        state.pop("token", None)
        state.pop("auth_method", None)
        return None'''

    token_details = fetch_token_details(modules, state)
    if not token_details:
        print("X - Credential material invalid or authentication failed. Returning to main menu. - X")
        state.pop("server", None)
        state.pop("token", None)
        state.pop("auth_method", None)
        return None

    print("Got a bearer token, seeing what you can do...")
    return token_details


def lazy_create_admin_account(modules, state):
    template_path = template_file_path("account_create.xml")
    root = load_xml_root(template_path)
    new_name = f"eve_lazy_admin_{random_suffix()}"
    new_password = random_password()

    set_xml_text(root, "name", new_name)
    set_xml_text(root, "real_name", new_name.upper())
    set_xml_text(root, "password", new_password)

    temp_path = make_temp_path("lazy_account_create", ".xml")
    write_xml_root(temp_path, root)

    result = modules["accounts"].create_account(state["server"], state["token"], temp_path)
    print(result)
    print(f"Created administrator account: {new_name}")
    print(f"Password: {new_password}")


def lazy_update_account(modules, state):
    target_id = prompt_optional_text("Target account ID")
    if not target_id:
        print("X - Account ID is required. - X")
        return

    template_path = template_file_path("account_update.xml")
    root = load_xml_root(template_path)
    new_name = f"eve_lazy_update_{random_suffix()}"
    new_password = random_password()

    set_xml_text(root, "name", new_name)
    set_xml_text(root, "real_name", new_name.upper())
    set_xml_text(root, "password", new_password)

    temp_path = make_temp_path("lazy_account_update", ".xml")
    write_xml_root(temp_path, root)

    result = modules["accounts"].update_account_by_id(
        state["server"], state["token"], target_id, temp_path
    )
    print(result)
    print(f"Updated account ID {target_id}")
    print(f"New username: {new_name}")
    print(f"New password: {new_password}")


def lazy_list_accounts(modules, state):
    print_result(modules["accounts"].get_accounts(state["server"], state["token"]))


def lazy_create_extension_attribute(modules, state):
    template_path = template_file_path("computer_extension_attribute.xml")
    root = load_xml_root(template_path)
    new_name = f"Eve Lazy EA {random_suffix()}"
    set_xml_text(root, "name", new_name)

    temp_path = make_temp_path("lazy_extension_attribute_create", ".xml")
    write_xml_root(temp_path, root)

    result = modules["computers"].create_computer_extension_attribute(
        state["server"], state["token"], temp_path
    )
    print(result)
    print(f"Created computer extension attribute: {new_name}")


def lazy_update_extension_attribute(modules, state):
    target_id = prompt_optional_text("Target computer extension attribute ID")
    if not target_id:
        print("X - Extension attribute ID is required. - X")
        return

    template_path = template_file_path("computer_extension_attribute.xml")
    root = load_xml_root(template_path)
    new_name = f"Eve Lazy EA Updated {random_suffix()}"
    set_xml_text(root, "name", new_name)

    temp_path = make_temp_path("lazy_extension_attribute_update", ".xml")
    write_xml_root(temp_path, root)

    result = modules["computers"].update_computer_extension_by_id(
        state["server"], state["token"], target_id, temp_path
    )
    print(result)
    print(f"Updated computer extension attribute ID {target_id} with name: {new_name}")


def lazy_list_extension_attributes(modules, state):
    print_result(
        modules["computers"].get_computer_extension_attributes(state["server"], state["token"])
    )


def lazy_create_policy(modules, state):
    template_path = template_file_path("policy_template_execute_command.xml")
    root = load_xml_root(template_path)
    new_name = f"Eve Lazy Policy {random_suffix()}"
    set_xml_text(root, "general/name", new_name)

    temp_path = make_temp_path("lazy_policy_create", ".xml")
    write_xml_root(temp_path, root)

    result = modules["policies"].create_policy(state["server"], state["token"], temp_path)
    print(result)
    print(f"Created policy: {new_name}")


def lazy_update_policy(modules, state):
    target_id = prompt_optional_text("Target policy ID")
    if not target_id:
        print("X - Policy ID is required. - X")
        return

    template_path = template_file_path("policy_template_execute_command.xml")
    root = load_xml_root(template_path)
    new_name = f"Eve Lazy Policy Updated {random_suffix()}"
    set_xml_text(root, "general/name", new_name)

    temp_path = make_temp_path("lazy_policy_update", ".xml")
    write_xml_root(temp_path, root)

    result = modules["policies"].update_policy_by_id(
        state["server"], state["token"], target_id, temp_path
    )
    print(result)
    print(f"Updated policy ID {target_id} with name: {new_name}")


def lazy_list_policies(modules, state):
    print_result(modules["policies"].get_policies(state["server"], state["token"]))


def lazy_create_api_client_and_role(modules, state):
    role_template = read_json_file(template_file_path("api_role.json"))
    client_template = read_json_file(template_file_path("api_client.json"))

    role_name = f"Eve_Lazy_Role_{random_suffix()}"
    client_name = f"Eve_Lazy_Client_{random_suffix()}"

    role_template["displayName"] = role_name
    client_template["displayName"] = client_name
    client_template["authorizationScopes"] = [role_name]

    role_temp_path = make_temp_path("lazy_api_role_create", ".json")
    client_temp_path = make_temp_path("lazy_api_client_create", ".json")
    write_json_file(role_temp_path, role_template)
    write_json_file(client_temp_path, client_template)

    role_result = modules["api"].create_api_role(state["server"], state["token"], role_temp_path)
    print(role_result)
    client_result = modules["api"].create_api_client(
        state["server"], state["token"], client_temp_path
    )
    print(client_result)
    print(f"Created API role: {role_name}")
    print(f"Created API client: {client_name}")


def lazy_list_api_clients(modules, state):
    print_result(modules["api"].get_api_clients(state["server"], state["token"]))


def lazy_list_api_roles(modules, state):
    print_result(modules["api"].get_api_roles(state["server"], state["token"]))


def build_lazy_actions(modules, permissions):
    actions = []

    if "Create Accounts" in permissions:
        actions.append(("Create New Administrator Account", lazy_create_admin_account))
    if "Update Accounts" in permissions:
        actions.append(("Update Existing Account Username And Password", lazy_update_account))
    if "Read Accounts" in permissions:
        actions.append(("List Accounts", lazy_list_accounts))
    if "Create Computer Extension Attributes" in permissions:
        actions.append(
            ("Create New Computer Extension Attribute", lazy_create_extension_attribute)
        )
    if "Update Computer Extension Attributes" in permissions:
        actions.append(
            ("Update Existing Computer Extension Attribute", lazy_update_extension_attribute)
        )
    if "Read Computer Extension Attributes" in permissions:
        actions.append(("List Computer Extension Attributes", lazy_list_extension_attributes))
    if "Create Policies" in permissions:
        actions.append(("Create New Policy", lazy_create_policy))
    if "Update Policies" in permissions:
        actions.append(("Update Existing Policy", lazy_update_policy))
    if "Read Policies" in permissions:
        actions.append(("List Policies", lazy_list_policies))
    if "Create API Integrations" in permissions and "Create API Roles" in permissions:
        actions.append(("Create New API Client And Role", lazy_create_api_client_and_role))
    if "Read API Integrations" in permissions:
        actions.append(("List API Clients", lazy_list_api_clients))
    if "Read API Roles" in permissions:
        actions.append(("List API Roles", lazy_list_api_roles))

    return actions


def lazy_mode_menu(modules, state):
    token_details = lazy_authenticate(modules, state)
    if not token_details:
        return

    permissions = extract_permissions(token_details)

    while True:
        lazy_actions = build_lazy_actions(modules, permissions)
        options = [label for label, _ in lazy_actions]
        options.append("Show Raw Token Details")
        options.append("Back")

        if not lazy_actions:
            print("No guided actions matched the permissions in the current token.")
        choice = prompt_choice("Select lazy mode option:", options)

        if choice <= len(lazy_actions):
            _, func = lazy_actions[choice - 1]
            try:
                func(modules, state)
            except Exception as exc:
                print(exc)
        elif choice == len(lazy_actions) + 1:
            print(token_details)
        else:
            return


def launch_ui(state):
    script_path = os.path.join(os.getcwd(), "eve_ui.py")
    process = state.get("ui_process")

    if process is not None and process.poll() is None:
        print("[i] - Eve UI is already running. Opening browser. -[i]")
        webbrowser.open("http://localhost:8003")
        return

    try:
        process = subprocess.Popen([sys.executable, script_path], cwd=os.getcwd())
        state["ui_process"] = process
        time.sleep(1)
        if process.poll() is not None:
            raise ProcessNotRunningError("X - Dependency failed, eve_ui.py subprocess encountered errors. - X")
        webbrowser.open("http://localhost:8003")
        print("[i] - Eve UI launched on http://localhost:8003 -[i]")
    except Exception as exc:
        print(exc)


def main():
    if not check_dependencies():
        sys.exit(1)

    ensure_data_dir()
    modules = load_modules()
    state = {}

    while True:
        choice = prompt_choice(
            "Welcome to eve, select your option below:",
            [
                "Auth - Provide credentials to authenticate",
                "Accounts - Interact with JAMF Pro Accounts and Groups",
                "APIs - Interact with API Clients and Roles",
                "Computers - Interact with JAMF Pro Computers",
                "Policies - Interact with JAMF Pro Policies",
                "Scripts - Interact with JAMF Pro Scripts",
                "SSO - Interact with JAMF Pro SSO",
                "UI - Launch Eve Web UI",
                "Lazy Mode - For lazy or new users guided actions based on credential access",
                "Exit",
            ],
        )

        if choice == 1:
            auth_menu(modules, state)
        elif choice == 2:
            accounts_menu(modules, state)
        elif choice == 3:
            api_menu(modules, state)
        elif choice == 4:
            computers_menu(modules, state)
        elif choice == 5:
            policies_menu(modules, state)
        elif choice == 6:
            scripts_menu(modules, state)
        elif choice == 7:
            sso_menu(modules, state)
        elif choice == 8:
            launch_ui(state)
        elif choice == 9:
            lazy_mode_menu(modules, state)
        else:
            return


if __name__ == "__main__":
    main()
