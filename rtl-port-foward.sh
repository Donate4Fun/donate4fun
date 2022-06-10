#!/bin/sh -e

kubectl -n rtl-prod port-forward service/rtl-prod 3000:http
