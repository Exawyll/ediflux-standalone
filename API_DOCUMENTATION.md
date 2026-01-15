# Factur-X Invoice Generator API Documentation

Base URL: `http://localhost:8000`

## Endpoints

### 1. Create Invoice

Generates a valid Factur-X Basic-WL invoice (PDF with embedded XML) and stores it on the server.

- **URL**: `/invoices`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### Request Body Schema

```json
{
  "invoice_number": "string",  // Unique identifier
  "date": "YYYY-MM-DD",
  "seller": {
    "name": "string",
    "address": {
      "street": "string",
      "zip_code": "string",
      "city": "string",
      "country_code": "string" // ISO 3166-1 alpha-2 (e.g., "FR")
    },
    "vat_id": "string",        // Optional: VAT number
    "siret": "string",         // Optional: SIRET number
    "email": "string"          // Optional
  },
  "buyer": {
    "name": "string",
    "address": {
      "street": "string",
      "zip_code": "string",
      "city": "string",
      "country_code": "string"
    },
    "vat_id": "string",        // Optional
    "siret": "string",         // Optional
    "email": "string"          // Optional
  },
  "items": [
    {
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "vat_rate": number       // Percentage (e.g., 20.0)
    }
  ],
  "currency": "string"         // e.g., "EUR" (default)
}
```

#### Response

- **Status Code**: `200 OK`
- **Content-Type**: `application/pdf`
- **Body**: The generated PDF file is returned directly.

#### Example

```bash
curl -X POST "http://localhost:8000/invoices" \
     -H "Content-Type: application/json" \
     -d '{
       "invoice_number": "FV-2023-001",
       "date": "2023-10-27",
       "seller": { "name": "My Corp", "address": { "street": "123 St", "zip_code": "75001", "city": "Paris", "country_code": "FR" } },
       "buyer": { "name": "Client Inc", "address": { "street": "456 Av", "zip_code": "69002", "city": "Lyon", "country_code": "FR" } },
       "items": [ { "description": "Consulting", "quantity": 1, "unit_price": 1000, "vat_rate": 20.0 } ]
     }' --output invoice.pdf
```

---

### 2. List Invoices

Retrieves a list of all listing generated invoices with their metadata.

- **URL**: `/invoices`
- **Method**: `GET`

#### Response

- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Body**: Array of invoice metadata.

```json
[
  {
    "id": "FV-2023-001",
    "date": "2023-10-27",
    "seller_name": "My Corp",
    "buyer_name": "Client Inc",
    "total_ht": 1000.0,
    "total_ttc": 1200.0,
    "currency": "EUR",
    "created_at": "2023-10-27"
  }
]
```

---

### 3. Retrieve Invoice

Retrieves a stored invoice. Supports Content Negotiation to return either the visual PDF or the structured XML.

- **URL**: `/invoices/{invoice_number}`
- **Method**: `GET`

#### URL Parameters

- `invoice_number`: The unique ID provided during creation.

#### Headers

- `Accept` (optional):
    - `application/pdf`: Returns the generated PDF file (Default).
    - `application/xml` or `text/xml`: Returns the embedded Factur-X XML file.

#### Responses

- **200 OK**: The requested file (PDF or XML).
- **404 Not Found**: If the invoice ID does not exist.

#### Examples

**Get PDF (Default)**
```bash
curl "http://localhost:8000/invoices/FV-2023-001" -H "Accept: application/pdf" --output invoice.pdf
```

**Get XML**
```bash
curl "http://localhost:8000/invoices/FV-2023-001" -H "Accept: application/xml" --output invoice.xml
```

---

### 4. Delete Invoice

Deletes an invoice and its associated files.

- **URL**: `/invoices/{invoice_number}`
- **Method**: `DELETE`

#### Response

- **Status Code**: `204 No Content`

