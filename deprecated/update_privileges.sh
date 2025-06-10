proxychains curl -X PUT \
    --url "$1/JSSResource/accounts/userid/$3" \
    -H "Accept: application/json" \
    -H "Content-Type: application/xml" \
    -H "Authorization: Bearer $2" \
    -d @admin.xml
