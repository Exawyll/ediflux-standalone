import requests
import sys

base_url = "http://localhost:8000"
invoice_id = "FV-TEST-CONTENT-NEG"

payload = {
    "invoice_number": invoice_id,
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
}

# 1. Create Invoice
print(f"Creating invoice {invoice_id}...")
try:
    resp = requests.post(f"{base_url}/invoices", json=payload)
    if resp.status_code == 200:
        print("Invoice created successfully.")
    else:
        print(f"Failed to create invoice: {resp.status_code} {resp.text}")
        sys.exit(1)
except Exception as e:
    print(f"Error connecting: {e}")
    sys.exit(1)

# 2. Get PDF
print("Requesting PDF...")
headers = {"Accept": "application/pdf"}
resp_pdf = requests.get(f"{base_url}/invoices/{invoice_id}", headers=headers)
if resp_pdf.status_code == 200 and "application/pdf" in resp_pdf.headers.get("Content-Type", ""):
    print("Success: Received PDF")
    with open("retrieved.pdf", "wb") as f:
        f.write(resp_pdf.content)
else:
    print(f"Failed to get PDF: {resp_pdf.status_code} {resp_pdf.headers.get('Content-Type')}")

# 3. Get XML
print("Requesting XML...")
headers = {"Accept": "application/xml"}
resp_xml = requests.get(f"{base_url}/invoices/{invoice_id}", headers=headers)
if resp_xml.status_code == 200 and "application/xml" in resp_xml.headers.get("Content-Type", ""):
    print("Success: Received XML")
    with open("retrieved.xml", "w") as f:
        f.write(resp_xml.text)
        if "CrossIndustryInvoice" in resp_xml.text:
             print("XML content validated (contains CrossIndustryInvoice)")
else:
    print(f"Failed to get XML: {resp_xml.status_code} {resp_xml.headers.get('Content-Type')}")
