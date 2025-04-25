# Create a Secret for nginx.conf file
```
gcloud secrets delete nginx_config
gcloud secrets create nginx_config --replication-policy='automatic' --data-file='./nginx.conf'
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding nginx_config --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com --role='roles/secretmanager.secretAccessor'
```

# Create a Secret for hydra config file
```
gcloud secrets create hydra_config --replication-policy='automatic' --data-file='./hydra-fairplex.yml'
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding hydra_config --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com --role='roles/secretmanager.secretAccessor'
```

# Create a Secret for kratos config file
```
gcloud secrets delete kratos_config
gcloud secrets create kratos_config --replication-policy='automatic' --data-file='./kratos-fairplex.yml'
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding kratos_config --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com --role='roles/secretmanager.secretAccessor'
```

# Create a Secret for kratos identity schema file
```
gcloud secrets create kratos_id_schema --replication-policy='automatic' --data-file='./identity.schema.json'
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding kratos_id_schema --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com --role='roles/secretmanager.secretAccessor'
```

# Create a Secret for AMP PD nginx.conf file
```
gcloud secrets delete nginx_config_amp_pd
gcloud secrets create nginx_config_amp_pd --replication-policy='automatic' --data-file='./nginx-amp-pd.conf'
export PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding nginx_config_amp_pd --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com --role='roles/secretmanager.secretAccessor'
```

# Verify
```
gcloud secrets list
```

# Deploy

## FAIRplex
```
gcloud run services replace service.yml
```

## AMP PD
```
gcloud run services replace amp-pd-service.yml
```