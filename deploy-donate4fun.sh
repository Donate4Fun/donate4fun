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

extra_args=""
namespace=donate4fun-prod
release=donate4fun-prod

while [[ $# -gt 0 ]]; do
  case $1 in
    -n|--nobuild)
      nobuild=yes
      shift # past argument
      ;;
    -s|--stage)
      extra_args="--values charts/donate4fun.stage.yaml"
      namespace=donate4fun-stage
      release=donate4fun-stage
      shift # past argument
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

if [ -z $nobuild ]; then
  build $backend_repo
  (cd frontend && build $frontend_repo)
fi
backend_digest=$(digest $backend_repo)
frontend_digest=$(digest $frontend_repo)

helm upgrade --install --create-namespace --namespace $namespace --values charts/donate4fun.yaml $extra_args --values secrets://charts/secrets.donate4fun.yaml --set backend.image.digest=$backend_digest --set frontend.image.digest=$frontend_digest --wait $release charts/donate4fun
