#!/bin/env python3
import importlib
import json
import os
import subprocess
import sys
import time
import webbrowser
from datetime import datetime, timezone
from getpass import getpass
from types import SimpleNamespace


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
        print("[i] - Loaded cached token from ./.data/token. -[i]")
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


def build_lazy_actions(modules, state, token_details):
    actions = []
    lowered = token_details.lower()

    if contains_any(lowered, ("account", "group")):
        actions.append(("List Accounts", modules["accounts"].get_accounts, ()))
        actions.append(("List Groups", modules["accounts"].get_groups, ()))

    if contains_any(lowered, ("api role", "api roles", "api client", "api clients", "api integration")):
        actions.append(("List API Roles", modules["api"].get_api_roles, ()))
        actions.append(("List API Clients", modules["api"].get_api_clients, ()))

    if contains_any(lowered, ("computer", "computers")):
        actions.append(("List Computers", modules["computers"].get_computers, ()))

    if contains_any(lowered, ("extension attribute", "extension attributes")):
        actions.append(
            (
                "List Computer Extension Attributes",
                modules["computers"].get_computer_extension_attributes,
                (),
            )
        )

    if contains_any(lowered, ("policy", "policies")):
        actions.append(("List Policies", modules["policies"].get_policies, ()))

    if contains_any(lowered, ("script", "scripts")):
        actions.append(("List Scripts", modules["scripts"].get_scripts, ()))

    if "sso" in lowered:
        actions.append(("Show SSO Config", modules["sso"].get_sso_config, ()))

    unique_actions = []
    seen = set()
    for label, func, args in actions:
        if label not in seen:
            unique_actions.append((label, func, args))
            seen.add(label)

    return unique_actions


def lazy_mode_menu(modules, state):
    if not ensure_authenticated(modules, state):
        return

    try:
        token_details = modules["auth"].get_token_details(state["server"], state["token"])
    except Exception as exc:
        print(exc)
        return

    while True:
        lazy_actions = build_lazy_actions(modules, state, token_details)
        options = [label for label, _, _ in lazy_actions]
        options.append("Show Raw Token Details")
        options.append("Back")

        print("Lazy Mode analyzes the current token and offers likely-safe starting actions.")
        choice = prompt_choice("Select lazy mode option:", options)

        if choice <= len(lazy_actions):
            _, func, args = lazy_actions[choice - 1]
            run_authenticated_action(modules, state, func, *args)
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
