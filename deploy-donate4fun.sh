#!/bin/sh -e

backend_repo=europe-central2-docker.pkg.dev/donate4fun-prod/docker/donate4fun-backend
frontend_repo=europe-central2-docker.pkg.dev/donate4fun-prod/docker/donate4fun-frontend

function build() {
  local repo=$1
  docker build -t $repo . >&2
  docker push $repo >&2
}

function digest() {
  local repo=$1
  local fulldigest=$(docker inspect $repo -f '{{ index .RepoDigests 0 }}')
  echo ${fulldigest#*@}
}

if [ "$1" != "-n" ]; then
  build $backend_repo
  (cd frontend && build $frontend_repo)
fi
backend_digest=$(digest $backend_repo)
frontend_digest=$(digest $frontend_repo)

helm upgrade --install --create-namespace --namespace donate4fun-prod --values charts/donate4fun.yaml --values secrets://charts/secrets.donate4fun.yaml --set backend.image.digest=$backend_digest --set frontend.image.digest=$frontend_digest donate4fun-prod charts/donate4fun
