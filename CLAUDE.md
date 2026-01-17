# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Factur-X Invoice Generator - A Python/FastAPI backend service that generates Factur-X compliant hybrid invoices (PDF/A-3 + XML) following the **Factur-X Basic-WL** profile. Designed for GCP Cloud Run deployment with optional local storage.

## Development Commands

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run development server (with auto-reload)
uvicorn main:app --port 8000 --reload

# Run production mode
uvicorn main:app --host 0.0.0.0 --port 8080

# Test (requires running server)
python test_api.py

# Build standalone executable
python build.py
```

## Architecture

### Request Flow
```
Frontend (HTML/JS at /static) → FastAPI Endpoints → Invoice Generator → Storage Layer
```

### Key Components

- **main.py**: FastAPI app entry point, all REST endpoints
- **models.py**: Pydantic models (InvoiceRequest, Party, Address, LineItem, Payment)
- **invoice_generator.py**: PDF generation via WeasyPrint + Factur-X XML embedding
- **storage.py**: Abstract storage layer with LocalStorage and GCSStorage implementations
- **invoice_sender.py**: Remote API integration for RabbitMQ message injection
- **auth/token.py**: Keycloak OAuth2 client credentials flow
- **api/secure_client.py**: Authenticated HTTP client wrapper

### Templates
- `templates/invoice.html`: Jinja2 template for invoice PDF rendering
- `templates/factur-x.xml`: Factur-X CII XML template

### Storage Selection
Controlled by `STORAGE_TYPE` env var:
- `LOCAL` (default): Stores in `invoices/` directory
- `GCS`: Stores in Google Cloud Storage bucket (requires `GCS_BUCKET_NAME`)

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/invoices` | Generate and store invoice, returns PDF |
| GET | `/invoices` | List all invoices metadata |
| GET | `/invoices/{id}` | Get PDF (or XML if Accept: application/xml) |
| DELETE | `/invoices/{id}` | Delete invoice |
| POST | `/invoices/{id}/send` | Send to remote RabbitMQ |
| GET | `/documents/{id}` | Get Factur-X XML for remote integration |

## Environment Variables

Required for remote integration features:
- `KEYCLOAK_SERVER_URL`, `KEYCLOAK_REALM_NAME`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`
- `REMOTE_API_URL`, `APP_BASE_URL`, `RABBITMQ_ROUTING_KEY`

For GCS storage:
- `STORAGE_TYPE=GCS`, `GCS_BUCKET_NAME`

## Build & Deployment

- **Docker**: `docker build -t facturier-python .` (uses port 8080)
- **Cloud Run**: Triggered via `cloudbuild.yaml`, deploys to `facturier-service` in europe-west1
- **Windows exe**: GitHub Actions workflow builds with GTK3 runtime for WeasyPrint

## Key Dependencies

WeasyPrint requires system libraries (Pango, Pixbuf). On Windows, GTK3 runtime must be installed. The PyInstaller build (`main.spec`) bundles GTK3 DLLs automatically.
