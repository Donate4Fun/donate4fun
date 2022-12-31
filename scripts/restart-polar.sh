#!/bin/sh -e

# deinit
(cd polar && docker-compose down)
rm -rf polar/volumes

# init
cp -rf polar/volumes-ref polar/volumes
(cd polar && docker-compose up -d)
$(dirname -- "$0")/init-polar.sh
