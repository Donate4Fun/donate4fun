#!/bin/sh -e

LISTEN_IP=$(ip route get 1.1.1.1 | grep -oP 'src \K\S+')

lnd \
  --noseedbackup \
  --no-rest-tls \
  --no-macaroons \
  --rpclisten=${LISTEN_IP} \
  --restlisten=${LISTEN_IP} \
  --listen=${LISTEN_IP} \
  --tlsautorefresh \
  --lnddir=/lnd \
  --bitcoin.active \
  --bitcoin.regtest \
  --bitcoin.node=neutrino \
  --neutrino.connect=bitcoind:${BITCOIN_PORT}
 
