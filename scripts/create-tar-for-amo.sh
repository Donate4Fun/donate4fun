#!/bin/sh -e

tmpfile=$(mktemp --suffix=.tar)
git archive -o $tmpfile HEAD .
tmpdir=$(mktemp -d)
tar -C $tmpdir -xf $tmpfile
rm $tmpfile
tar -C $tmpdir --dereference --hard-dereference -zc .
rm -r $tmpdir
