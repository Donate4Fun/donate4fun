#!/bin/sh -e

name=$1
repo=nikicat/$name

docker build -t $repo docker/$name
docker push $repo
fulldigest=$(docker inspect $repo -f '{{ index .RepoDigests 0 }}')
digest=${fulldigest#*@}
helm upgrade --install --create-namespace --namespace $name-prod --set image.digest=$digest $name-prod charts/$name
