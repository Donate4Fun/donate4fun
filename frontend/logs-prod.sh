#!/bin/sh -e
exec kubectl -n donate4fun-prod logs -l app.kubernetes.io/name=donate4fun -f
