#!/bin/sh -e

listen_ip=$(ip route get 1.1.1.1 | grep -oP 'src \K\S+')
if [ "$NEUTRINO_HOST" != "" ]; then
  # Resolve early because lnd uses tor for resolving
  neutrino_ip=$(dig +short $NEUTRINO_HOST | awk '{ print ; exit }')
  extra_arg="--neutrino.connect=${neutrino_ip}:${NEUTRINO_PORT}"
fi

if [ "$TOR_TARGET_HOST" ]; then
  tor_target_ip=$(dig +short $TOR_TARGET_HOST | awk '{ print ; exit }')
else
  tor_target_ip=$listen_ip
fi

exec lnd \
  --rpclisten=${listen_ip} \
  --restlisten=${listen_ip} \
  --listen=${listen_ip} \
  --rpclisten=127.0.0.1 \
  --restlisten=127.0.0.1 \
  --listen=127.0.0.1 \
  --tor.targetipaddress=${tor_target_ip} \
  $extra_arg \
  "$@"
