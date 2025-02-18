#!/bin/zsh

# Set variables for Jamf Pro credentials and server URL
JAMF_URL="$1"  # Replace with your Jamf Pro server URL

# Set the computer ID and script ID
SCRIPT_ID="$3"
# XML payload for the policy with Recurring Check-in trigger
read -r -d '' POLICY_PAYLOAD << EOM
<policy>
    <general>
        <name>${4}</name>
        <enabled>true</enabled>
        <target_drive>/</target_drive>
        <trigger>EVENT</trigger>  <!-- Recurring Check-in trigger -->
        <trigger_checkin>true</trigger_checkin>
        <frequency>Once per computer</frequency>
    </general>
    <scope>
        <computers>
            <computer>
                <id>5</id>
            </computer>
            <computer>
                <id>6</id>
            </computer>
            <computer>
                <id>8</id>
            </computer>
        </computers>
    </scope>
    <scripts>
        <script>
            <id>${SCRIPT_ID}</id>
            <priority>After</priority>
        </script>
    </scripts>
</policy>
EOM

# API endpoint to create the policy
POLICY_ENDPOINT="${JAMF_URL}/JSSResource/policies/id/0"

# Make the API request to create the policy using curl
proxychains curl -s -k \
    --request POST \
    --url "$POLICY_ENDPOINT" \
    --header "Authorization: Bearer $2" \
    --header "Content-Type: application/xml" \
    --header "Accept: application/xml" \
    --data "$POLICY_PAYLOAD"

