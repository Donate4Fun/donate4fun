#!/bin/sh -e

ref=${1:-master}

tmpfile=$(mktemp)
tmpdir=$(mktemp -d)
wget -O $tmpfile https://github.com/donate4fun/donate4fun/tarball/$ref
tar -C $tmpdir -zxf $tmpfile
rm $tmpfile
tar -C $tmpdir --dereference --hard-dereference -zcf ~/Downloads/donate4fun.src.tar.gz .
rm -r $tmpdir