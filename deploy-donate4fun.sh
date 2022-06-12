#!/bin/sh -e

backend_repo=europe-central2-docker.pkg.dev/donate4fun-prod/docker/donate4fun-backend
frontend_repo=europe-central2-docker.pkg.dev/donate4fun-prod/docker/donate4fun-frontend

function build() {
  local repo=$1
  docker build -t $repo . >&2
  docker push $repo >&2
  local fulldigest=$(docker inspect $repo -f '{{ index .RepoDigests 0 }}')
  echo ${fulldigest#*@}
}

backend_digest=$(build $backend_repo)
frontend_digest=$(cd frontend && build $frontend_repo)

helm upgrade --install --create-namespace --namespace donate4fun-prod --values charts/donate4fun.yaml --set backend.image.digest=$backend_digest --set frontend.image.digest=$frontend_digest donate4fun-prod charts/donate4fun
