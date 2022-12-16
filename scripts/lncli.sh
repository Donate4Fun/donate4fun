#!/bin/sh -e

node=$1
shift
case $node in
  alice)
    port=10004
    ;;
  bob)
    port=10005
    ;;
  carol)
    port=10006
    ;;
  *)
    echo "invalid node"
    exit 1
esac

nodedir="polar/volumes/lnd/$node"

lncli --rpcserver localhost:$port --macaroonpath $nodedir/data/chain/bitcoin/regtest/admin.macaroon --tlscertpath $nodedir/tls.cert "$@"
