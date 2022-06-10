#!/bin/sh -e

kubectl -n lnd-prod cp lnd-prod-0:/lnd/tls.cert ./tls.cert
