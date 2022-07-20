#!/bin/sh -exv

sed -i "s/%HOST%/${HOST}/g" /usr/share/nginx/html/index.html 

exec nginx
