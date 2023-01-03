#!/bin/sh -e

while true; do
  ./scripts/lncli.sh bob getinfo && break || true
  sleep 0.1
done
scripts/bitcoin-cli.sh -generate

wait_for_sync() {
  while true; do
    synced=$(./scripts/lncli.sh $1 getinfo | jq -r .$2)
    [ "$synced" = "true" ] && break || true
    sleep 0.1
  done
}
echo "Waiting for a bob chain sync..."
wait_for_sync bob synced_to_chain
connected_peers=$(./scripts/lncli.sh bob listpeers | jq -r '.peers[].pub_key')

connect() {
  local pubkey=${1%@*}
  local name=${1%:*}
  local name=${name#*@}
  echo "$connected_peers" | grep -w -q $pubkey && return
  wait_for_sync $name synced_to_chain
  ./scripts/lncli.sh bob connect $1
}
echo "Connecting bob to alice and carol..."
connect 03e803ff6eb04880c8c9644bb0acc78e4aceba87b3e4c6db9b6f57bb3f797f29d8@alice:9735
connect 031815bada9500dd9fc6aa3b3d3c58c9a1d10b3d9b40d7f1159a17410e915c3789@carol:9735
echo "Waiting for all nodes be synced to graph..."
for node in alice bob carol; do
  (wait_for_sync $node synced_to_graph) &
done
for job in $(jobs -p); do
    wait $job
done
echo "Done"
