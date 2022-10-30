#!/bin/sh -exv

sed -i "s|%HOST%|https://${HOST}|g" /usr/share/nginx/html/index.html 

exec nginx
