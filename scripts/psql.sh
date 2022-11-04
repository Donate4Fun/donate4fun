#!/bin/sh -e

log=$(mktemp)
trap "rm -f $log" EXIT
kubectl -n postgresql port-forward service/postgresql 15432:5432 > $log &
pid=$!
tail -f $log | sed '/Forwarding from / q' > /dev/null
PGPASSWORD=donate4fun psql -h localhost -p 15432 -U donate4fun -w "$@"
kill $pid
