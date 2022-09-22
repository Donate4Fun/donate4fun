#!/bin/sh -e

(
  cd extensions
  (
    cd src
    rollup -c
  )
  rm -f chrome.zip
  (
    cd chrome
    zip -r ../chrome.zip manifest.json dist
  )
  rm -f firefox.zip
  (
    cd firefox
    zip -r ../firefox.zip background.html manifest.json dist
  )
)
