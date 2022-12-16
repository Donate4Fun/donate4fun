#!/bin/sh -e
bitcoin-cli -rpcport=18444 -rpcpassword=polarpass -rpcuser=polaruser "$@"
