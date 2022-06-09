#!/bin/sh -e

LISTEN_IP=$(ip route get 1.1.1.1 | grep -oP 'src \K\S+')

exec lnd \
  --rpclisten=${LISTEN_IP} \
  --restlisten=${LISTEN_IP} \
  --listen=${LISTEN_IP} \
  --rpclisten=127.0.0.1 \
  --restlisten=127.0.0.1 \
  --listen=127.0.0.1 \
  "$@"
