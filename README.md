# Factur-X Invoice Generator

A Python-based backend service that generates Factur-X compliant hybrid invoices (PDF/A-3 + XML).
This project uses **FastAPI** for the backend API and **WeasyPrint** for PDF generation.
It is configured to generate invoices complying with the **Factur-X Basic-WL** (Basic Without Lines) profile.

## Prerequisites

- Python 3.9+
- Pip

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

1.  Fill out the invoice details (Seller, Buyer, Items).
2.  Click "Générer la Facture Factur-X".
3.  The valid Factur-X PDF will be generated and downloaded automatically.

## Testing API Directly

### Option 1: Using the provided Python script

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
