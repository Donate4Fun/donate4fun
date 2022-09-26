Donate4.Fun
==
This is monorepo for Donate4.Fun webservice.
Directory structure:
 - `/donate4fun/` (python) - backend (API)
 - `/tests/` (python) - tests for backend
 - `/frontend/` (SvelteJS) - website
 - `/extensions/` (SvelteJS) - browser extensions
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
It's pretty simple
```
cd extensions/src
npm i
npm run dev
```
Then open browser and install unpacked extension from `extensions/chrome` or `extensions/firefox`.

To build extension for webstore run `npm run package-clean`.

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
