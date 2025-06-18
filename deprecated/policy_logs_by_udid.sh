proxychains curl -k "$1/JSSResource/computerhistory/udid/$3/subset/policy_logs" --header "Authorization: Bearer $2" -H "Content-Type: application/json" -H "Accept: application/json" | jq 
