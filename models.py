from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class Address(BaseModel):
    street: str
    zip_code: str
    city: str
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 code, e.g., FR")

class Party(BaseModel):
    name: str
    address: Address
    vat_id: Optional[str] = None
    siret: Optional[str] = None
    email: Optional[str] = None

class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    vat_rate: float # e.g., 20.0 for 20%

class InvoiceRequest(BaseModel):
    invoice_number: str
    date: date
    seller: Party
    buyer: Party
    items: List[LineItem]
    currency: str = "EUR"
