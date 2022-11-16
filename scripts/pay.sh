#!/bin/sh -e
exec docker/lncli-bob payinvoice --force "$@"
