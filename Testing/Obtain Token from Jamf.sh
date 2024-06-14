#!/bin/bash

url="https://chippewanfr.jamfcloud.com"
client_id="5141eb89-b33a-4fa3-823d-ba553cf229d9"
client_secret="NWmaiOwMHPYU4nbE7kbX3PNExDQJz_XE7bZF-ihLXiWswg6N9kaeKbmW4jWgk2CN"

getAccessToken() {
	response=$(curl --silent --location --request POST "${url}/api/oauth/token" \
 	 	--header "Content-Type: application/x-www-form-urlencoded" \
 		--data-urlencode "client_id=${client_id}" \
 		--data-urlencode "grant_type=client_credentials" \
 		--data-urlencode "client_secret=${client_secret}")
 	access_token=$(echo "$response" | plutil -extract access_token raw -)
 	token_expires_in=$(echo "$response" | plutil -extract expires_in raw -)
 	token_expiration_epoch=$(($current_epoch + $token_expires_in - 1))
}
getAccessToken

echo "access token:"
echo ""
echo $access_token