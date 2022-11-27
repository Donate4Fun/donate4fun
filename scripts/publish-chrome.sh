#!/bin/sh -e

token=$(jq -r .access_token chrome-web-store-token.json)
curl \
  -H "Authorization: Bearer $token"  \
  -H "x-goog-api-version: 2" \
  -X PUT \
  -T extensions/chrome.zip \
  https://www.googleapis.com/upload/chromewebstore/v1.1/items/acckcppgcafhbdledejfiiaomafpjmgc
