#!/bin/sh -e

name=$1

[ -z "$name" ] && echo "Usage: $0 <lnd|rtl|tor>" && exit 1
repo=nikicat/$name

docker build -t $repo docker/$name
docker push $repo
fulldigest=$(docker inspect $repo -f '{{ index .RepoDigests 0 }}')
digest=${fulldigest#*@}
[ -f "charts/${name}.yaml" ] && conf_arg="--values=charts/${name}.yaml"
[ -f "charts/secrets.${name}.yaml" ] && conf_arg="--values=charts/secrets.${name}.yaml"
helm secrets upgrade --install --create-namespace --namespace=${name}-prod $conf_arg --set image.digest=$digest $name-prod charts/$name
