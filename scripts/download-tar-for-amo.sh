#!/bin/sh -e

ref=${1:-master}
output=${2:-~/Downloads/donate4fun.src.tar.gz}

tmpfile=$(mktemp)
tmpdir=$(mktemp -d)
wget -O $tmpfile https://github.com/donate4fun/donate4fun/tarball/$ref
tar -C $tmpdir -zxf $tmpfile
rm $tmpfile
tar -C $tmpdir --dereference --hard-dereference -zcf "$output" .
rm -r $tmpdir
