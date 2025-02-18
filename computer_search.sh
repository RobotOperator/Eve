#!/bin/bash
proxychains curl -k "$1/JSSResource/computers/match/$3" --header "Authorization: Bearer $2" -H "Content-Type: application/json" -H "Accept: application/json" | jq
