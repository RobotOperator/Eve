#!/bin/bash

#echo "$1/api/v1/auth/token"
#echo "Authorization: Basic '$2'"
#proxychains 
curl -k "$1/api/v1/auth/token" --request POST --header "Authorization: Basic '$2'"

