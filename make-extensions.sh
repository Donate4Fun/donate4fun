#!/bin/sh -e

(
  cd extensions/src
  npm run build
  cp -r . ../firefox/src
  cp -r . ../chrome/src
)
