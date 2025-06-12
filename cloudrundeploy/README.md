# FAIRplex Auth Pilot

This pilot implements a GA4GH Passport Broker and Visa Issuer for AMP PD. Ory Hydra and Kratos are used as the OIDC Server and Identity Manager, with Google OAuth as the Identity Provider. All microservices are deployed as a single service in Google Cloud Run. Please see the Deployment README for more details.

The following steps will save our config files as secrets in Google Secret Manager. These config files are not secret, but storing them in Secret Manager is a convenient way to make them available to the Cloud Run services at startup.


## Create a Secret for nginx.conf file
```
gcloud secrets delete nginx_config
gcloud secrets create nginx_config --replication-policy='automatic' --data-file='./nginx.conf'
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding nginx_config --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com --role='roles/secretmanager.secretAccessor'
```

## Create a Secret for Hydra config file
```
gcloud secrets create hydra_config --replication-policy='automatic' --data-file='./hydra-fairplex.yml'
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding hydra_config --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com --role='roles/secretmanager.secretAccessor'
```

## Create a Secret for Kratos config file
```
gcloud secrets delete kratos_config
gcloud secrets create kratos_config --replication-policy='automatic' --data-file='./kratos-fairplex.yml'
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding kratos_config --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com --role='roles/secretmanager.secretAccessor'
```

## Create a Secret for Kratos identity schema file
```
gcloud secrets create kratos_id_schema --replication-policy='automatic' --data-file='./identity.schema.json'
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding kratos_id_schema --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com --role='roles/secretmanager.secretAccessor'
```

## Create a Secret for AMP PD nginx.conf file
```
gcloud secrets delete nginx_config_amp_pd
gcloud secrets create nginx_config_amp_pd --replication-policy='automatic' --data-file='./nginx-amp-pd.conf'
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding nginx_config_amp_pd --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com --role='roles/secretmanager.secretAccessor'
```

## Verify
```
gcloud secrets list
```

## Deploy

### FAIRplex
```
gcloud run services replace service.yml
```

### AMP PD
```
gcloud run services replace amp-pd-service.yml
```