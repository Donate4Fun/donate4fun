#!/bin/sh -e

xdg-open "https://accounts.google.com/o/oauth2/auth?response_type=code&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fchromewebstore&redirect_uri=http%3A%2F%2Flocalhost%3A8818&access_type=offline&client_id=$GOOGLE_CLIENT_ID"
read -p "Enter code:" authcode
resp=$(curl -XPOST "https://accounts.google.com/o/oauth2/token?client_id=$GOOGLE_CLIENT_ID&client_secret=$GOOGLE_CLIENT_SECRET&code=$authcode&grant_type=authorization_code&redirect_uri=http://localhost:8818")
echo "$resp" | jq -r .refresh_token
