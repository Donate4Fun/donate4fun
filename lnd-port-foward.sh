#!/bin/sh -e

kubectl -n lnd-prod port-forward service/lnd-prod rpc rest
