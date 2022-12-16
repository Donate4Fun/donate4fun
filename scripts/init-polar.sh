#!/bin/sh -e

# deinit
(cd polar && docker-compose down)
rm -rf polar/volumes

# init
cp -rf polar/volumes-ref polar/volumes
(cd polar && docker-compose up -d)
while true; do
  ./scripts/lncli.sh bob getinfo && break || true
  sleep 0.1
done
scripts/bitcoin-cli.sh -generate
while true; do
  synced=$(./scripts/lncli.sh bob getinfo | jq -r .synced_to_chain)
  [ "$synced" = "true" ] && break || true
  sleep 0.1
done
./scripts/lncli.sh bob connect 03e803ff6eb04880c8c9644bb0acc78e4aceba87b3e4c6db9b6f57bb3f797f29d8@alice:9735
./scripts/lncli.sh bob connect 031815bada9500dd9fc6aa3b3d3c58c9a1d10b3d9b40d7f1159a17410e915c3789@carol:9735
