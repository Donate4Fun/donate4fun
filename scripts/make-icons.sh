#!/bin/sh -e

cd frontend/public/static
for size in 16 24 32 48 64 128 256 512; do
  inkscape -w $size -h $size D.svg -o D-$size.png -b transparent -y 0
done
