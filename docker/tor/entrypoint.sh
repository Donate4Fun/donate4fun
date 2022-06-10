#!/bin/sh -e

cp /tor-config/torrc /etc/tor/torrc
echo "HashedControlPassword $(tor --quiet --hash-password ${TOR_PASSWORD})" >> /etc/tor/torrc

exec tor
