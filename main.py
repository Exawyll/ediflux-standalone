import os
from fastapi import FastAPI, HTTPException, Response, Header
from fastapi.responses import  FileResponse
from models import InvoiceRequest
from invoice_generator import generate_invoice_pdf
import io

INVOICES_DIR = "invoices"
os.makedirs(INVOICES_DIR, exist_ok=True)

app = FastAPI(title="Factur-X Invoice Generator")

# Enable CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Frontend
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def read_root():
    return RedirectResponse(url="/static/index.html")

@app.post("/invoices", responses={200: {"content": {"application/pdf": {}}}})
async def create_invoice(invoice_data: InvoiceRequest):
    try:
        pdf_bytes, xml_content = generate_invoice_pdf(invoice_data)
        
        # Save files
        # Sanitize invoice number to avoid path injection
        safe_filename = "".join([c for c in invoice_data.invoice_number if c.isalnum() or c in ('-', '_')])
        if not safe_filename:
             safe_filename = "invoice"
             
        base_path = os.path.join(INVOICES_DIR, safe_filename)
        with open(f"{base_path}.pdf", "wb") as f:
            f.write(pdf_bytes)
        with open(f"{base_path}.xml", "w", encoding="utf-8") as f:
            f.write(xml_content)
            
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/invoices/{invoice_number}")
async def get_invoice(invoice_number: str, accept: str = Header(default="application/pdf")):
    safe_filename = "".join([c for c in invoice_number if c.isalnum() or c in ('-', '_')])
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid invoice number")

    base_path = os.path.join(INVOICES_DIR, safe_filename)
    pdf_path = f"{base_path}.pdf"
    xml_path = f"{base_path}.xml"
    
    if not os.path.exists(pdf_path) or not os.path.exists(xml_path):
        raise HTTPException(status_code=404, detail="Invoice not found")

    if "xml" in accept:
        with open(xml_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="application/xml")
    else:
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"{invoice_number}.pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
