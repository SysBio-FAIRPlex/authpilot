# SysBio FAIRplex GA4GH Auth Pilot

```
docker-compose -f auth-pilot-compose.yml up --force-recreate -d
```

## Notes

1. You must put in the fairplex client id/secret in config/kratos-fairplex.yml
2. You must authenticate with the Auth-Spike project in Google Cloud cli:
```
gcloud config set account your-email@sysbio-fairplex.org
gcloud config set project auth-spike-445014
gcloud auth application-default login
```
3. You will need the service key file for the amp-pd-visa-issuer service to create a signed url. It is currently providing the DRS service. 

## Todos
1. Make a separate DRS service

## Cloud Run
