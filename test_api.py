import requests
import json
import base64

url = "http://localhost:8000/invoices"

payload = {
    "invoice_number": "FV-2023-001",
    "date": "2023-10-27",
    "seller": {
        "name": "My Company",
        "address": {
            "street": "123 Business Rd",
            "zip_code": "75001",
            "city": "Paris",
            "country_code": "FR"
        },
        "vat_id": "FR123456789",
        "siret": "12345678900012",
        "email": "contact@mycompany.com"
    },
    "buyer": {
        "name": "Client Corp",
        "address": {
            "street": "456 Client St",
            "zip_code": "69002",
            "city": "Lyon",
            "country_code": "FR"
        },
        "vat_id": "FR987654321"
    },
    "items": [
        {
            "description": "Consulting Services",
            "quantity": 5.0,
            "unit_price": 100.0,
            "vat_rate": 20.0
        },
        {
            "description": "Hosting",
            "quantity": 1.0,
            "unit_price": 50.0,
            "vat_rate": 20.0
        }
    ],
    "currency": "EUR"
}

try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        with open("test_invoice.pdf", "wb") as f:
            f.write(response.content)
        print("Success: Invoice saved to test_invoice.pdf")
        
        # Verify Factur-X attachment exists
        # We can use factur-x library to check it or simply check file size/header
        from facturx import get_facturx_xml_from_pdf
        try:
            xml = get_facturx_xml_from_pdf("test_invoice.pdf")
            print("Success: Factur-X XML found in PDF")
            print(f"XML length: {len(xml)}")
        except Exception as e:
            print(f"Error checking Factur-X XML: {e}")

    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Failed to connect: {e}")
