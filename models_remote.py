from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date

class DocumentMessageDTO(BaseModel):
    nom: str
    typeMime: Optional[str] = "application/pdf"
    url: Optional[str] = None
    urlV2: str
    dateEffet: Optional[date] = None
    origine: Optional[str] = None

class FluxExportDocument(BaseModel):
    numeroDossier: str = "32025"
    idDocument: str
    typeDocument: str = "FACTURE_CLIENT"
    origine: Optional[str] = "FACTUR-X-PYTHON"
    kanalyseActif: bool = True
    document: DocumentMessageDTO

class RabbitInfoMessage(BaseModel):
    contentType: str = "application/json"
    headers: Dict[str, Any] = {}
    payload: str # Stringified JSON of FluxExportDocument

class RabbitInjectionMessage(BaseModel):
    routingKey: str
    message: RabbitInfoMessage
