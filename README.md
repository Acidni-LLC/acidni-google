# Acidni Google Services Manager

Centralized Google API management service for all Acidni applications.

## Quick Start

```powershell
# Install dependencies
pip install -r requirements.txt

# Set environment variables
$env:AZURE_KEY_VAULT_URL = "https://kv-terprint-dev.vault.azure.net"
$env:COSMOS_ENDPOINT = "https://cosmos-terprint-dev.documents.azure.com:443/"
$env:COSMOS_DATABASE = "TerprintAI"

# Run locally
uvicorn main:app --reload --port 8000
```

## Features

- ✅ Google Analytics 4 management
- ✅ Google Tag Manager operations
- ✅ Google AdSense reporting
- ✅ Google Ads campaign management
- ✅ API enablement/disablement
- ✅ Configuration management via Cosmos DB
- ✅ Azure Key Vault integration
- ✅ Health monitoring

## API Endpoints

- `GET /health` - Health check
- `GET /analytics/properties` - List GA4 properties
- `POST /analytics/events` - Send GA4 event
- `GET /tags/containers` - List GTM containers
- `GET /adsense/reports/revenue` - Get revenue report
- `GET /ads/campaigns` - List campaigns
- `POST /apis/enable` - Enable APIs for product
- `GET /apis/status/{productCode}` - Get API status

## Documentation

- [Architecture](../acidni-config/products/acidni-google/docs/ARCHITECTURE.md)
- [Integration Guide](../acidni-config/products/acidni-google/docs/INTEGRATION.md)
- [Runbook](../acidni-config/products/acidni-google/docs/RUNBOOK.md)

## Deployment

Automatically deploys to Azure Container Apps via GitHub Actions on push to `main`.

```powershell
# Manual deployment
docker build -t crterprint.azurecr.io/acidni-google:dev-latest .
docker push crterprint.azurecr.io/acidni-google:dev-latest
az containerapp update --name ca-acidni-google-dev --resource-group rg-dev-terprint-ca --image crterprint.azurecr.io/acidni-google:dev-latest
```

## Environment Variables

- `AZURE_KEY_VAULT_URL` - Key Vault URL
- `COSMOS_ENDPOINT` - Cosmos DB endpoint
- `COSMOS_DATABASE` - Cosmos DB database name

## Status

🚧 **In Development** - Core framework complete, Google API integrations in progress

---

**Version**: 1.0.0  
**Created**: 2026-02-03
