This project is open source and has a GitHub Actions workflow for building: https://github.com/Donate4Fun/donate4fun/actions/workflows/build-extension.yaml
To build it locally you could use https://github.com/nektos/act
To build it manually step by step you need environment with nodejs 16, git, zip, pnpm (may be some other tools included in GitHub Actions) and run

```
(cd frontend && pnpm install)
cd extensions/src
pnpm install
pnpm package-clean
```

the output file will be extensions/firefox.zip
