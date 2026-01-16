# Factur-X Invoice Generator

A Python-based backend service that generates Factur-X compliant hybrid invoices (PDF/A-3 + XML).
This project uses **FastAPI** for the backend API and **WeasyPrint** for PDF generation.
It is configured to generate invoices complying with the **Factur-X Basic-WL** (Basic Without Lines) profile.

## Prerequisites

- Python 3.9+
- Pip

## Deployment

### Google Cloud Platform (GCP) Ready

This application is designed to be deployed on GCP (Cloud Run) with invoice storage on Google Cloud Storage (GCS).

**Configuration:**
- Set `STORAGE_TYPE=GCS`.
- Set `GCS_BUCKET_NAME=your-bucket-name`.
- Ensure the service account has `roles/storage.objectAdmin` on the bucket.

The Frontend is stateless and served directly by the backend, ensuring it works seamlessly in a containerized environment (relative paths).

## Installation

1.  **Create and activate a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  **Start the server:**

    ```bash
    uvicorn main:app --port 8000 --reload
    ```
    
    The API will be available at `http://localhost:8000`.

2.  **Open the Frontend:**

    Open your browser and navigate to:
    
    [http://localhost:8000/](http://localhost:8000/)
    
    This will load the simple Invoice Generator form.

## Usage

1.  **Generate Invoke:**
    - Fill out the invoice details (Auto-fill available via Company Search).
    - Click "Générer la Facture Factur-X".
    - The generated PDF/A-3 invoice will be downloaded.

2.  **View & Re-download:**
    - Scroll down to "Factures Existantes".
    - Click "Actualiser" (Refresh) if needed.
    - Click the **PDF** or **XML** buttons to re-download the files.

## Testing

### Manual Testing (Step-by-Step)

1.  **Start the server**: `uvicorn main:app --reload`
2.  **Open Frontend**: Go to `http://localhost:8000/`.
3.  **Search Company**: Type "Google" in the Seller search box and select a result. Verify fields are filled.
4.  **Create Invoice**: Fill remaining fields and submit. Verify PDF download.
5.  **Verify List**: Check the "Factures Existantes" table. The new invoice should appear.
6.  **Download Again**: Click "PDF" and "XML" in the table row. Verify both files download correctly.

### Automated Testing

We have provided a `test_api.py` script that sends a sample request to your running local server and saves the generated invoice.

1.  Ensure the server is running (see above).
2.  Open a new terminal window, activate the venv, and run:

    ```bash
    source venv/bin/activate
    python test_api.py
    ```

3.  Check the output:
    - You should see `Success: Invoice saved to test_invoice.pdf`.
    - A file named `test_invoice.pdf` will be created in the current directory.
    - You can open this PDF to verify it looks correct and has the XML attachment (using Adobe Reader or similar, look for the Attachments panel).

### Option 2: Using cURL

You can manually send a request using cURL:

```bash
curl -X POST "http://localhost:8000/invoices" \
     -H "Content-Type: application/json" \
     -d '{
    "invoice_number": "FV-TEST-001",
    "date": "2023-11-01",
    "seller": {
        "name": "My Company",
        "address": { "street": "1 Main St", "zip_code": "75001", "city": "Paris", "country_code": "FR" },
        "vat_id": "FR123456789",
        "siret": "12345678900012"
    },
    "buyer": {
        "name": "Client Inc",
        "address": { "street": "2 Market St", "zip_code": "69001", "city": "Lyon", "country_code": "FR" },
        "vat_id": "FR987654321"
    },
    "items": [
        { "description": "Service A", "quantity": 1, "unit_price": 500, "vat_rate": 20.0 }
    ],
    "currency": "EUR"
}' --output invoice.pdf
```

### Validating the Factur-X Compliance

You can use the online validator [FNFE-MPE Validator](https://services.fnfe-mpe.org/factur-x/validation) or the `factur-x` python library to inspect the generated PDF.

The `test_api.py` script attempts to verify the existence of the XML attachment automatically.

## Remote Invoice Integration

You can send generated invoices to a distant API for processing/integration (RabbitMQ injection).

**Environment Variables:**
Ensure the following variables are set (e.g., via `.env` or shell):
- `KEYCLOAK_SERVER_URL`: Keycloak server URL.
- `KEYCLOAK_REALM_NAME`: Keycloak Realm.
- `KEYCLOAK_CLIENT_ID`: Keycloak Client ID.
- `KEYCLOAK_CLIENT_SECRET`: Keycloak Client Secret.
- `REMOTE_API_URL`: URL of the remote API.
- `APP_BASE_URL`: Public URL of this application (for callbacks).
- `RABBITMQ_ROUTING_KEY`: Routing key for the message.

**Trigger Sending:**
Send a POST request to:
`POST /invoices/{invoice_number}/send`
