# Local Development Setup Guide

This guide walks you through setting up the SysBio FAIRplex GA4GH Auth Pilot system for local development.

## Prerequisites

### System Requirements

- macOS, Linux, or Windows with WSL2
- At least 8GB RAM recommended
- 10GB free disk space

### Required Software

- **Docker Desktop** (includes Docker and Docker Compose)
- **Git** (for cloning the repository)

## Step-by-Step Setup

### 1. Install Docker Desktop

#### On macOS (using Homebrew):

```bash
brew install --cask docker
```

#### On other platforms:

- Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
- Follow the installation instructions for your platform

#### Start Docker Desktop:

1. Open **Applications** → **Docker.app** (macOS) or start Docker Desktop from your applications
2. Wait for Docker to start completely (you'll see a whale icon in your system tray)
3. Verify installation:

```bash
docker --version
docker-compose --version
```

### 2. Clone and Navigate to Repository

```bash
git clone <repository-url>
cd authpilot
```

### 3. Build Docker Images

Build all the custom Docker images required for the system:

```bash
# Build fairplex-client
docker build -t fairplex-client:0.1 ./fairplex-client/

# Build fairplex-token-exchange
docker build -t fairplex-token-exchange:0.1 ./fairplex-token-exchange/

# Build auth-pilot-amp-pd-visa-issuer
docker build -t auth-pilot-amp-pd-visa-issuer:0.1 ./auth-pilot-amp-pd-visa-issuer/

# Build auth-pilot-data-transfer
docker build -t auth-pilot-data-transfer:0.1 ./auth-pilot-data-transfer/
```

### 4. Create SSL Certificates

Generate self-signed certificates for development:

```bash
# Create certificates directory
mkdir -p certs

# Generate self-signed SSL certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/nginx-selfsigned.key \
  -out certs/nginx-selfsigned.crt \
  -subj "/C=US/ST=CA/L=SF/O=Dev/CN=fairplex.io"

# Create password file for nginx
echo "password" > certs/myCA.pass
```

### 5. Configure Authentication (Required)

#### Google OAuth2 Setup (Required for full functionality):

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
5. Configure the OAuth consent screen
6. Create OAuth2 credentials with these redirect URIs:

   - `http://localhost:4433/self-service/methods/oidc/callback/google`
   - `https://fairplex-login.io:4433/self-service/methods/oidc/callback/google`

7. Update the Kratos configuration with your credentials:

```bash
# Edit config/kratos/kratos-fairplex.yml
# Replace the placeholder values:
client_id: "your-actual-google-client-id"
client_secret: "your-actual-google-client-secret"
```

**Note**: For basic testing, you can leave the placeholder values, but Google OAuth login won't work.

### 6. Start the System

#### Option A: Start All Services at Once

```bash
docker-compose -f auth-pilot-compose.yaml up -d
```

#### Option B: Start Services Incrementally (Recommended for troubleshooting)

```bash
# Start database first
docker-compose -f auth-pilot-compose.yaml up -d postgresd

# Start Hydra migration and service
docker-compose -f auth-pilot-compose.yaml up -d hydra-migrate hydra

# Start Kratos migration and service
docker-compose -f auth-pilot-compose.yaml up -d kratos-migrate kratos

# Start remaining services
docker-compose -f auth-pilot-compose.yaml up -d
```

### 7. Verify System Status

Check that all services are running:

```bash
# Check service status
docker-compose -f auth-pilot-compose.yaml ps

# Test core services
curl http://localhost:80                    # Main endpoint
curl http://localhost:4444/health/ready     # Hydra health
curl http://localhost:4433/health/ready     # Kratos health
```

## Service Overview

### Core Services (Should be running):

- **PostgreSQL** (`postgresd`) - Database on port 5432
- **Ory Hydra** (`hydra`) - OAuth2/OpenID Connect server
  - Public API: `http://localhost:4444`
  - Admin API: `http://localhost:4445`
- **Ory Kratos** (`kratos`) - Identity management
  - Public API: `http://localhost:4433`
  - Admin API: `http://localhost:4434`
- **Nginx** (`nginx`) - Reverse proxy on port 80

### Application Services (May need additional configuration):

- **fairplex-client-app** - Frontend application
  - **🌐 Main UI**: http://localhost:8884
- **fairplex-token-exchange** - Token exchange service on port 8000
- **auth-pilot-amp-pd-visa-issuer** - Visa issuer service on port 7000

## Troubleshooting

### Common Issues

#### Docker not starting:

```bash
# Check Docker status
docker info

# Restart Docker Desktop if needed
```

#### Services restarting:

```bash
# Check logs for specific service
docker-compose -f auth-pilot-compose.yaml logs <service-name>

# Example:
docker-compose -f auth-pilot-compose.yaml logs kratos
docker-compose -f auth-pilot-compose.yaml logs fairplex-client-app
```

#### Port conflicts:

```bash
# Check what's using a port
lsof -i :4444
lsof -i :4433

# Stop conflicting services or change ports in compose file
```

#### Permission issues with certificates:

```bash
# Fix certificate permissions
chmod 644 certs/nginx-selfsigned.crt
chmod 600 certs/nginx-selfsigned.key
```

### Stopping Services

```bash
# Stop all services
docker-compose -f auth-pilot-compose.yaml down

# Stop and remove volumes (reset database)
docker-compose -f auth-pilot-compose.yaml down -v

# Stop specific service
docker-compose -f auth-pilot-compose.yaml stop <service-name>
```

### Rebuilding Images

If you make changes to the application code:

```bash
# Rebuild specific image
docker build -t fairplex-client:0.1 ./fairplex-client/

# Restart the service
docker-compose -f auth-pilot-compose.yaml restart fairplex-client-app
```

## Development Workflow

### Making Changes

1. **Code Changes**: Edit files in the respective service directories
2. **Rebuild Image**: `docker build -t <image-name>:0.1 ./<service-directory>/`
3. **Restart Service**: `docker-compose -f auth-pilot-compose.yaml restart <service-name>`
4. **Check Logs**: `docker-compose -f auth-pilot-compose.yaml logs <service-name>`

### Accessing Logs

```bash
# Follow logs for all services
docker-compose -f auth-pilot-compose.yaml logs -f

# Follow logs for specific service
docker-compose -f auth-pilot-compose.yaml logs -f kratos

# View recent logs
docker-compose -f auth-pilot-compose.yaml logs --tail=50 hydra
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it authpilot-postgresd-1 psql -U hydra -d hydra

# Or using external client
psql -h localhost -p 5432 -U hydra -d hydra
```

## Advanced Configuration

### Adding Google Cloud Service Account

For services that need Google Cloud access:

1. Download service account key from Google Cloud Console
2. Update the compose file to mount the key:

```yaml
volumes:
  - /path/to/your/service-account-key.json:/app/service-account-key.json
environment:
  - GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
```

### Custom Domain Setup

To use custom domains (like `fairplex.io`):

1. Add entries to `/etc/hosts`:

```bash
127.0.0.1 fairplex.io
127.0.0.1 fairplex-login.io
```

2. Update nginx configuration as needed

## Next Steps

Once the system is running locally:

1. **Configure Google OAuth2** for authentication
2. **Set up Google Cloud service accounts** for cloud features
3. **Review and customize** the Kratos identity schema
4. **Test the authentication flow** with real credentials
5. **Explore the GA4GH Passport/Visa functionality**

## Getting Help

- Check service logs: `docker-compose -f auth-pilot-compose.yaml logs <service>`
- Verify service health: `curl http://localhost:<port>/health/ready`
- Review the main [README.md](README.md) for system architecture
- Check individual service READMEs in their respective directories

## File Structure

```
authpilot/
├── auth-pilot-compose.yaml     # Main Docker Compose file
├── nginx-minimal.conf          # Nginx configuration
├── certs/                      # SSL certificates
├── config/                     # Service configurations
│   ├── hydra/
│   └── kratos/
├── fairplex-client/           # Frontend application
├── fairplex-token-exchange/   # Token exchange service
├── auth-pilot-amp-pd-visa-issuer/  # Visa issuer
└── auth-pilot-data-transfer/  # Data transfer service
```

---

**Status**: ✅ Core authentication infrastructure working  
**Last Updated**: $(date)  
**Docker Images Built**: fairplex-client:0.1, fairplex-token-exchange:0.1, auth-pilot-amp-pd-visa-issuer:0.1, auth-pilot-data-transfer:0.1
