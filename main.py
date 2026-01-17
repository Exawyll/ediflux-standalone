import os
from fastapi import FastAPI, HTTPException, Response, Header, Depends, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

from models import InvoiceRequest
from invoice_generator import generate_invoice_pdf
from storage import get_storage, InvoiceStorage
from invoice_sender import send_invoice_task
from xml_processor import extract_xml_from_pdf, validate_cii_xml, extract_metadata_from_xml, create_placeholder_pdf
from typing import List
from datetime import datetime

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

if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def read_root():
    if os.path.exists("frontend/index.html"):
        return RedirectResponse(url="/static/index.html")
    return {"message": "Factur-X Generator API"}

@app.post("/invoices", responses={200: {"content": {"application/pdf": {}}}})
async def create_invoice(invoice_data: InvoiceRequest):
    try:
        pdf_bytes, xml_content = generate_invoice_pdf(invoice_data)
        
        # Prepare metadata
        total_ht = sum(item.quantity * item.unit_price for item in invoice_data.items)
        # Approximate tax calculation for metadata display (simplified)
        total_ttc = sum(item.quantity * item.unit_price * (1 + item.vat_rate/100) for item in invoice_data.items)

        metadata = {
            "id": invoice_data.invoice_number,
            "date": str(invoice_data.date),
            "seller_name": invoice_data.seller.name,
            "buyer_name": invoice_data.buyer.name,
            "total_ht": round(total_ht, 2),
            "total_ttc": round(total_ttc, 2),
            "currency": invoice_data.currency,
            "created_at": str(invoice_data.date) 
        }

        storage = get_storage()
        storage.save_invoice(invoice_data.invoice_number, pdf_bytes, xml_content, metadata)
            
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/invoices/upload")
async def upload_invoice(file: UploadFile = File(...)):
    """
    Upload a Factur-X PDF or CII XML invoice file.

    - For PDF files: Extracts the embedded Factur-X XML
    - For XML files: Validates CII structure and creates a placeholder PDF

    Returns the extracted metadata on success.
    """
    # Validate file extension
    filename = file.filename or ""
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''

    if ext not in ('pdf', 'xml'):
        raise HTTPException(
            status_code=400,
            detail="Type de fichier invalide. Formats acceptes: PDF (Factur-X), XML (CII/EN16931)"
        )

    # Read file content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Fichier vide")

    xml_content = None
    pdf_bytes = None

    if ext == 'pdf':
        # Extract XML from PDF
        try:
            xml_content = extract_xml_from_pdf(content)
            if not xml_content:
                raise HTTPException(
                    status_code=422,
                    detail="Impossible d'extraire le XML Factur-X du PDF. Le fichier n'est peut-etre pas un PDF Factur-X valide."
                )
            pdf_bytes = content
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="La bibliotheque facturx n'est pas installee. Impossible de traiter les PDF."
            )
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Erreur lors de l'extraction XML: {str(e)}")

    else:  # XML file
        # Decode XML content
        try:
            xml_content = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                xml_content = content.decode('iso-8859-1')
            except Exception:
                raise HTTPException(status_code=422, detail="Impossible de decoder le fichier XML")

        # Validate CII structure
        is_valid, error_msg = validate_cii_xml(xml_content)
        if not is_valid:
            raise HTTPException(
                status_code=422,
                detail=f"XML non conforme CII/EN16931: {error_msg}"
            )

    # Extract metadata from XML
    metadata = extract_metadata_from_xml(xml_content)

    # Validate that we extracted meaningful data
    if not metadata.get('_valid', False):
        missing_fields = []
        if not metadata.get('id'):
            missing_fields.append("numero de facture")
        if not metadata.get('seller_name'):
            missing_fields.append("nom du vendeur")
        if not metadata.get('buyer_name'):
            missing_fields.append("nom de l'acheteur")

        raise HTTPException(
            status_code=422,
            detail=f"Impossible d'extraire les donnees essentielles du XML: {', '.join(missing_fields)}. Verifiez que le fichier est bien un Factur-X/CII valide."
        )

    # Remove internal validation flag before saving
    metadata.pop('_valid', None)

    # Check for duplicate
    storage = get_storage()
    existing = storage.get_invoice_metadata(metadata['id'])
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Une facture avec le numero '{metadata['id']}' existe deja"
        )

    # For XML-only uploads, create a placeholder PDF
    if pdf_bytes is None:
        try:
            pdf_bytes = create_placeholder_pdf(xml_content, metadata)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de la creation du PDF: {str(e)}")

    # Save the invoice
    try:
        storage.save_invoice(metadata['id'], pdf_bytes, xml_content, metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde: {str(e)}")

    return JSONResponse(content=metadata)


@app.get("/invoices")
async def list_invoices():
    try:
        storage = get_storage()
        invoices = storage.list_invoices()
        return JSONResponse(content=invoices)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/invoices/{invoice_number}")
async def get_invoice(invoice_number: str, accept: str = Header(default="application/pdf")):
    storage = get_storage()
    result = storage.get_invoice(invoice_number)
    
    if not result:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    pdf_bytes, xml_content = result

    if "xml" in accept:
        return Response(content=xml_content, media_type="application/xml")
    else:
        return Response(content=pdf_bytes, media_type="application/pdf")

@app.delete("/invoices/{invoice_number}")
async def delete_invoice(invoice_number: str):
    storage = get_storage()
    metadata = storage.get_invoice_metadata(invoice_number)
    if not metadata:
        raise HTTPException(status_code=404, detail="Invoice not found")

    storage.delete_invoice(invoice_number)
    return Response(status_code=204)

@app.post("/invoices/{invoice_number}/send")
async def send_existing_invoice(invoice_number: str):
    storage = get_storage()
    metadata = storage.get_invoice_metadata(invoice_number)
    if not metadata:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Extract date
    try:
        # metadata['date'] is str(date) -> YYYY-MM-DD
        invoice_date = datetime.strptime(metadata['date'], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        # Fallback to current date if missing or malformed
        invoice_date = datetime.now().date()
    
    try:
        success = send_invoice_task(invoice_number, invoice_date, f"{invoice_number}.pdf")
        if success:
             return {"message": "Invoice sent successfully"}
        else:
             raise HTTPException(status_code=500, detail="Failed to send invoice (unknown error)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send invoice: {str(e)}")

@app.get("/documents/{invoice_number}")
async def get_invoice_document(invoice_number: str):
    """
    Endpoint exposed for remote integration to fetch the Factur-X XML.
    Returns Content-Type: application/xml
    """
    storage = get_storage()
    result = storage.get_invoice(invoice_number)
    
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
        
    _, xml_content = result
    return Response(content=xml_content, media_type="application/xml")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
