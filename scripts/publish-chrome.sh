#!/bin/sh -e

tokenfile=secrets/chrome-web-store-token.json
token=$(jq -r .access_token "$tokenfile")
item_id=acckcppgcafhbdledejfiiaomafpjmgc

function call_api() {
  curl \
    -H "Authorization: Bearer $token"  \
    -H "x-goog-api-version: 2" \
    "$@"
}

function upload() {
  call_api \
    -X PUT \
    -T extensions/chrome.zip \
    https://www.googleapis.com/upload/chromewebstore/v1.1/items/$item_id
}

function publish() {
  call_api \
    -H "Content-Length: 0" \
    -X POST \
    https://www.googleapis.com/chromewebstore/v1.1/items/$item_id/publish
}

function refresh_token() {
  local refresh_token=$(jq -r .refresh_token "$tokenfile")
  local url="https://accounts.google.com/o/oauth2/token?grant_type=refresh_token&client_id=$CHROME_WEB_STORE_CLIENT_ID&client_secret=$CHROME_WEB_STORE_CLIENT_SECRET&refresh_token=$refresh_token"
  local body
  body=$(curl --fail-with-body -X POST "$url")
  local retval=$?
  if [ $retval -ne 0 ]; then
    echo "$body"
    exit $retval
  fi
  local access_token=$(echo "$body" | jq -r .access_token)
  mv "$tokenfile" "$tokenfile.old"
  jq --arg token "$access_token" '.access_token = $token' "$tokenfile.old" > "$tokenfile"
}

"$@"
