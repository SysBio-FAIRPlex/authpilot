# Auth Pilot Terra API

Service to get group memberships from Terra

## Cloud Run Deploy
```console
docker build -t auth-pilot-terra-api:1 .
docker tag auth-pilot-terra-api:1 us-central1-docker.pkg.dev/auth-spike-445014/auth-pilot/auth-pilot-terra-api:1 && \
docker push us-central1-docker.pkg.dev/auth-spike-445014/auth-pilot/auth-pilot-terra-api:1
```