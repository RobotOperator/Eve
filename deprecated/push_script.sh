#!/bin/zsh

if (( $# > 4))
then
   echo "X- Only 4 arguments allowed, encapsulate strings in single quotes if needed. -X"
   exit
fi

if (( $# < 4))
then
   echo "X- Requires 4 arguments, server, bearer_token, script_file_path, and name for new script -X"
   exit
fi

proxychains curl -k --request POST \
     --url $1/api/v1/scripts \
     --header 'accept: application/json' \
     --header 'content-type: application/json' \
     --header "Authorization: Bearer $2" \
     --data "
{
  \"scriptContents\": \"$(cat $3)\",
  \"name\": \"$4\",
  \"info\": \"$4\",
  \"priority\": \"BEFORE\"
}
"
