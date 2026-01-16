import os
import json
import logging
from datetime import date
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


from api.secure_client import SecureAPIClient
from models_remote import FluxExportDocument, DocumentMessageDTO, RabbitInjectionMessage, RabbitInfoMessage

logger = logging.getLogger(__name__)

class InvoiceSender:
    def __init__(self):
        self.remote_api_url = os.environ.get("REMOTE_API_URL", "https://maintenance.example.com") # User should set this
        self.app_base_url = os.environ.get("APP_BASE_URL", "http://localhost:8000")
        self.routing_key = os.environ.get("RABBITMQ_ROUTING_KEY", "facture.entrant") # Default guess
        
        # Initialize Secure Client
        # Note: AuthToken inside SecureAPIClient will look for KEYCLOAK_* env vars
        self.client = SecureAPIClient(base_url=self.remote_api_url)

    def send_invoice(self, invoice_number: str, invoice_date: date, pdf_filename: str):
        """
        Send invoice metadata to the remote RabbitMQ via API.
        """
        # 1. Construct the inner DTO (FluxExportDocument)
        # URL to get the PDF. The remote service calls GET {urlV2} to retrieve the file.
        # Assuming our GET /invoices/{id} returns PDF by default or based on accept header.
        # Ideally we provide a direct link.
        download_url = f"{self.app_base_url}/invoices/{invoice_number}"

        document_dto = DocumentMessageDTO(
            nom=pdf_filename,
            typeMime="application/pdf",
            url=download_url, # v1
            urlV2=download_url, # v2
            dateEffet=invoice_date,
            origine="GENERATED"
        )

        flux_export = FluxExportDocument(
            numeroDossier="100602", # Default as per requirements
            idDocument=invoice_number,
            typeDocument="FACTURE_CLIENT", # Sales invoice
            origine="FACTUR-X-PYTHON",
            kanalyseActif=True,
            document=document_dto
        )

        # 2. Serialize FluxExportDocument to JSON string
        payload_str = flux_export.model_dump_json()

        # 3. Construct the outer Wrapper (RabbitInjectionMessage)
        rabbit_message = RabbitInjectionMessage(
            routingKey=self.routing_key,
            message=RabbitInfoMessage(
                payload=payload_str
            )
        )

        # 4. Send to API
        logger.info(f"Sending invoice {invoice_number} to remote API...")
        try:
            response = self.client.post(
                endpoint="/api/messages?type=nouveau",
                json_data=rabbit_message.model_dump()
            )
            response.raise_for_status()
            logger.info("Invoice sent successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send invoice: {e}")
            raise e

# Helper instantiation
sender_service = InvoiceSender()

def send_invoice_task(invoice_number: str, invoice_date: date, pdf_filename: str):
    """
    Wrapper function to be called from API or background task.
    """
    return sender_service.send_invoice(invoice_number, invoice_date, pdf_filename)
