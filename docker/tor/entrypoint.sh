#!/bin/sh -e

cp /tor-config/torrc /tmp/torrc
echo "HashedControlPassword $(tor --quiet --hash-password ${TOR_PASSWORD})" >> /tmp/torrc

exec tor -f /tmp/torrc
