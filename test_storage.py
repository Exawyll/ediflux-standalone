import requests
import sys

base_url = "http://localhost:8000"
invoice_id = "FV-STORAGE-TEST"

payload = {
    "invoice_number": invoice_id,
    "date": "2023-12-01",
    "seller": {
        "name": "Storage Corp",
        "address": { "street": "Cloud Av", "zip_code": "10000", "city": "Cloud City", "country_code": "US" }
    },
    "buyer": {
        "name": "Local User",
        "address": { "street": "Localhost", "zip_code": "12700", "city": "Home", "country_code": "US" }
    },
    "items": [
        { "description": "Storage Unit", "quantity": 10, "unit_price": 5.0, "vat_rate": 10.0 }
    ],
    "currency": "USD"
}

print(f"1. Creating invoice {invoice_id}...")
resp = requests.post(f"{base_url}/invoices", json=payload)
if resp.status_code != 200:
    print(f"Failed to create: {resp.status_code}")
    sys.exit(1)
print("Created.")

print("2. Listing invoices...")
resp_list = requests.get(f"{base_url}/invoices")
if resp_list.status_code == 200:
    invoices = resp_list.json()
    print(f"Received {len(invoices)} invoices.")
    found = False
    for inv in invoices:
        if inv["id"] == invoice_id:
            print(f"Found our invoice: {inv}")
            found = True
            break
    if not found:
        print("Error: Did not find the new invoice in the list.")
        sys.exit(1)
else:
    print(f"Failed to list: {resp_list.status_code}")
    sys.exit(1)

print("3. Deleting invoice...")
resp_del = requests.delete(f"{base_url}/invoices/{invoice_id}")
if resp_del.status_code == 204:
    print("Deleted successfully.")
else:
    print(f"Failed to delete: {resp_del.status_code}")
    sys.exit(1)

print("4. Verifying deletion (List)...")
resp_list_2 = requests.get(f"{base_url}/invoices")
invoices_2 = resp_list_2.json()
for inv in invoices_2:
    if inv["id"] == invoice_id:
        print("Error: Invoice still exists in list after delete.")
        sys.exit(1)
print("Verification successful: Invoice gone from list.")

print("5. Verifying deletion (Get)...")
resp_get = requests.get(f"{base_url}/invoices/{invoice_id}")
if resp_get.status_code == 404:
    print("Verification successful: 404 on Get.")
else:
    print(f"Error: Expected 404, got {resp_get.status_code}")
    sys.exit(1)
