#!/bin/sh -e

(
  cd extensions
  (
    cd src
    npm run build
    cp -r . ../firefox/src
    cp -r . ../chrome/src
  )
  cp -r ../frontend/public/static firefox/
  cp -r ../frontend/public/static chrome/
  rm -f ../chrome.zip
  (
    cd chrome
    zip -r ../chrome.zip manifest.json src static -x 'src/node_modules/*'
  )
)
