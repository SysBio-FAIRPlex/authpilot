# SysBio FAIRplex GA4GH Auth Pilot

This is a **GA4GH Authentication and Authorization Infrastructure (AAI) proof of concept** that demonstrates federated authentication and authorization for genomics data access. The system implements GA4GH standards for secure data sharing across institutions using Passports and Visas.

## Quick Start

```bash
docker-compose -f auth-pilot-compose.yml up --force-recreate -d
```

## Architecture Overview

The system consists of 5 main microservices that work together to provide secure, federated access to genomics datasets:

### Core Components

#### 1. **fairplex-client** (TypeScript/Node.js)
- **Purpose**: Frontend client application that orchestrates the authentication flow
- **Key Features**:
  - Handles OpenID Connect authentication with Hydra
  - Manages user sessions and token exchange
  - Provides UI for data transfer operations
  - Exchanges tokens for GA4GH Passports

#### 2. **auth-pilot-amp-pd-visa-issuer** (Python/FastAPI)
- **Purpose**: Issues GA4GH Visas for AMP-PD dataset access authorization
- **Key Features**:
  - Generates RSA key pairs for signing Visas
  - Validates user group membership via Terra API
  - Issues signed JWT tokens (Visas) for authorized users
  - Provides mock DRS (Data Repository Service) endpoints

#### 3. **auth-pilot-data-transfer** (Python/FastAPI)
- **Purpose**: Handles secure data transfers between cloud storage systems
- **Key Features**:
  - Downloads files from signed URLs
  - Uploads to Google Cloud Storage buckets
  - Manages temporary file handling during transfers

#### 4. **auth-pilot-terra-api** (Python/FastAPI)
- **Purpose**: Interfaces with Terra/Firecloud APIs for group membership validation
- **Key Features**:
  - Authenticates using Google service accounts
  - Fetches user group membership data for authorization decisions

#### 5. **fairplex-token-exchange** (Python/FastAPI)
- **Purpose**: Implements OAuth2 token exchange for GA4GH Passports
- **Key Features**:
  - Exchanges OAuth2 access tokens for GA4GH Passport tokens
  - Manages token validation and transformation

## GA4GH Implementation

This POC implements the GA4GH Authentication and Authorization Infrastructure standard:

### **Visas**
- Cryptographically signed assertions about a researcher's attributes or access rights
- Contain claims like dataset access permissions and user group memberships
- Signed by trusted Visa Issuers using RSA keys

### **Passports**
- Collections of Visas bundled together in a single token
- Presented to data repositories for access decisions
- Enable federated authorization across multiple institutions

### **Data Flow**
1. **User Authentication**: User logs in via Google OAuth through Kratos/Hydra
2. **Token Exchange**: Access token exchanged for GA4GH Passport containing Visas
3. **Authorization**: Passport validates user's access to AMP-PD datasets
4. **Data Access**: If authorized, user can transfer data from DRS to their GCS bucket

## Infrastructure Components

- **Ory Hydra**: OAuth2/OpenID Connect server
- **Ory Kratos**: Identity management and user registration
- **Nginx**: Reverse proxy and load balancer
- **PostgreSQL**: Database for Hydra/Kratos
- **Google Cloud Storage**: File storage backend

## Setup Requirements

1. You must put in the fairplex client id/secret in config/kratos-fairplex.yml
2. You must authenticate with the Auth-Spike project in Google Cloud cli:
```bash
gcloud config set account your-email@sysbio-fairplex.org
gcloud config set project auth-spike-445014
gcloud auth application-default login
```
3. You will need the service key file for the amp-pd-visa-issuer service to create a signed url. It is currently providing the DRS service.

## Deployment

### Local Development
Uses Docker Compose with all services running locally:
- Includes Ory Hydra and Kratos for identity management
- All microservices communicate via Docker network
- Suitable for development and testing

### Production (Google Cloud Run)
Each service deployed as a separate Cloud Run service:
- Auto-scaling based on demand
- Configuration managed via Google Secret Manager
- See `cloudrundeploy/README.md` for deployment instructions

## Todos
1. Make a separate DRS service
