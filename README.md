=Donate4.Fun

Website and API for donate4.fun service.

==Development
For developing you need a Docker and docker-compose (see /docker dir).
It's recommended to use some virtual env manager, for example direnv.
 - Create config.yaml
 - launch Docker containers `(cd docker; docker-compose up -d)`
 - launch api `python -m donate4fun`
 - launch frontend `(cd frontend; pnpm run dev)`

===Tests
Run tests with `pytest` from repository root.

===Trubleshooting
If tests are failing with error FAILURE_REASON_INSUFFICIENT_BALANCE try restarting lnd-bob: 
`docker-compose restart lnd-bob`
Sometimes channel could not start after starting all services.

If you are getting an error 'database "donate4fun-test" already exists' then connect to local postgresql and drop this database
`psql -U postgres -c 'drop database "donate4fun-test"'`

==Deploy
For deploying publicly you need a Kubernetes cluster and Helm (see /charts dir).

===Build and deploy dependencies
```
./deploy.sh tor
./deploy.sh lnd
./deploy.sh rtl
```

===Build and deploy the service
```
./deploy-donate4fun.sh
```
