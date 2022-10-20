#!/bin/sh -e

kubectl -n postgresql port-forward service/postgresql 15432:5432 &
kubectl -n lnd-prod port-forward service/lnd-prod 18080:rest 19735:rpc &
kubectl -n rtl-prod port-forward service/rtl-prod 33000:http &

trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT
wait
