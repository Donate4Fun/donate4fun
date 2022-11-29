#!/bin/sh -e

ffmpeg -i "$1" -vcodec libwebp -lossless 0 -compression_level 3 -q:v 70 -loop 1 -preset drawing -an -vf "scale=iw/2:ih/2" "${1%.*}.webp"
