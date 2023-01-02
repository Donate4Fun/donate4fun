#!/bin/sh -e

while true; do
  ./scripts/lncli.sh bob getinfo && break || true
  sleep 0.1
done
scripts/bitcoin-cli.sh -generate

wait_for_sync() {
  while true; do
    synced=$(./scripts/lncli.sh $1 getinfo | jq -r .synced_to_chain)
    [ "$synced" = "true" ] && break || true
    sleep 0.1
  done
}
wait_for_sync bob
connected_peers=$(./scripts/lncli.sh bob listpeers | jq -r '.peers[].pub_key')

connect() {
  local pubkey=${1%@*}
  local name=${1%:*}
  local name=${name#*@}
  echo "$connected_peers" | grep -w -q $pubkey && return
  wait_for_sync $name
  ./scripts/lncli.sh bob connect $1
}
connect 03e803ff6eb04880c8c9644bb0acc78e4aceba87b3e4c6db9b6f57bb3f797f29d8@alice:9735
connect 031815bada9500dd9fc6aa3b3d3c58c9a1d10b3d9b40d7f1159a17410e915c3789@carol:9735
