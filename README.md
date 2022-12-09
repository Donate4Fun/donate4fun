[![Telegram Chat](https://img.shields.io/static/v1?label=chat&message=Telegram&color=blue&logo=telegram)](https://t.me/donate4fun)
[![Twitter Follow](https://img.shields.io/twitter/follow/donate4_fun?style=social)](https://twitter.com/donate4_fun)
[![Website](https://img.shields.io/website/https/donate4.fun%2Fapi%2Fv1%2Fstatus)](https://donate4.fun)

[![Chrome Web Store](https://img.shields.io/chrome-web-store/v/acckcppgcafhbdledejfiiaomafpjmgc?color=green&label=Chrome%20Extension&logo=google-chrome)](https://chrome.google.com/webstore/detail/donate4fun/acckcppgcafhbdledejfiiaomafpjmgc)
[![Firefox Add-on](https://img.shields.io/amo/v/donate4fun?label=Firefox%20Addon&logo=firefox)](https://addons.mozilla.org/en-US/firefox/addon/donate4fun/)

[![Latest Chrome Extension](https://img.shields.io/github/workflow/status/donate4fun/donate4fun/Browser%20Extension?label=Dev%20Chrome%20Extension&logo=google-chrome)](https://nightly.link/Donate4Fun/donate4fun/workflows/build-extension.yaml/master/chrome.zip.zip)
[![Latest Firefox Add-on](https://img.shields.io/github/workflow/status/donate4fun/donate4fun/Browser%20Extension?label=Dev%20Firefox%20Add-on&logo=firefox)](https://nightly.link/Donate4Fun/donate4fun/workflows/build-extension.yaml/master/firefox.xpi.zip)

Donate4.Fun
==
This is repository for [Donate4.Fun](https://donate4.fun) webservice and browser extension.
Directory structure:
 - `/donate4fun/` - backend (API)
 - `/tests/` - tests for backend
 - `/frontend/` - website and shared libraries
 - `/extensions/` - browser extensions
 - `/charts/` - Helm charts for webservice and dependencies (LND, PostgreSQL, Tor)
 - `/docker/` - Docker-compose config and Dockerfiles for local development

Development
==

Website
===
For developing you need a Docker and docker-compose (see /docker dir).
It's recommended to use some virtual env manager, for example direnv.
 - Create config.yaml
 - launch Docker containers `(cd docker; docker-compose up -d)`
 - launch api `python -m donate4fun`
 - launch frontend `(cd frontend; pnpm run dev)`

Tests
===
Run tests with `pytest` from repository root.

Trubleshooting
===
If tests are failing with error FAILURE_REASON_INSUFFICIENT_BALANCE try restarting lnd-bob: 
`docker-compose restart lnd-bob`
Sometimes channel could not start after starting all services.

If you are getting an error 'database "donate4fun-test" already exists' then connect to local postgresql and drop this database
`psql -U postgres -c 'drop database "donate4fun-test"'`

Browser extension
===
You need to install both frontend and extension dependencies to build.
```
(cd frontend && pnpm i)
cd extensions/src
pnpm i
pnpm run dev
```
Then open browser and install unpacked extension from `extensions/chrome` or `extensions/firefox`.

To build release versions run `npm run package-clean`.

Deploy
==
For deploying publicly you need a Kubernetes cluster and Helm (see /charts dir).

Build and deploy dependencies
===
```
./deploy.sh tor
./deploy.sh lnd
./deploy.sh rtl
```

Build and deploy the service
===
```
./deploy-donate4fun.sh
```
