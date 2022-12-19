#!/bin/sh -e
ffmpeg -i "$1" -codec copy "${1%.*}.mp4"
