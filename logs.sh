#!/bin/sh -e

namespace=$1
exec kubectl -n donate4fun-$namespace logs -l app.kubernetes.io/name=donate4fun -f
