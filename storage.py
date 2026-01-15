import os
import json
import abc
from datetime import datetime
from typing import List, Optional, Tuple, Dict
from models import InvoiceRequest

class InvoiceStorage(abc.ABC):
    @abc.abstractmethod
    def save_invoice(self, invoice_id: str, pdf_bytes: bytes, xml_content: str, metadata: dict):
        pass

    @abc.abstractmethod
    def get_invoice(self, invoice_id: str) -> Tuple[bytes, str]:
        """Returns (pdf_bytes, xml_content)"""
        pass

    @abc.abstractmethod
    def list_invoices(self) -> List[Dict]:
        """Returns list of invoice metadata dicts"""
        pass

    @abc.abstractmethod
    def delete_invoice(self, invoice_id: str):
        pass

class LocalStorage(InvoiceStorage):
    def __init__(self, directory: str = "invoices"):
        self.directory = directory
        os.makedirs(self.directory, exist_ok=True)

    def _get_paths(self, invoice_id: str):
        safe_id = "".join([c for c in invoice_id if c.isalnum() or c in ('-', '_')])
        if not safe_id:
             raise ValueError("Invalid invoice ID")
        base = os.path.join(self.directory, safe_id)
        return f"{base}.pdf", f"{base}.xml", f"{base}.meta.json"

    def save_invoice(self, invoice_id: str, pdf_bytes: bytes, xml_content: str, metadata: dict):
        pdf_path, xml_path, meta_path = self._get_paths(invoice_id)
        
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
            
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, default=str)

    def get_invoice(self, invoice_id: str) -> Tuple[bytes, str]:
        pdf_path, xml_path, _ = self._get_paths(invoice_id)
        if not os.path.exists(pdf_path) or not os.path.exists(xml_path):
            return None
            
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
            
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()
            
        return pdf_bytes, xml_content

    def list_invoices(self) -> List[Dict]:
        invoices = []
        if not os.path.exists(self.directory):
            return []
            
        for filename in os.listdir(self.directory):
            if filename.endswith(".meta.json"):
                try:
                    with open(os.path.join(self.directory, filename), "r") as f:
                        meta = json.load(f)
                        invoices.append(meta)
                except Exception:
                    continue # Skip broken files
        return invoices

    def delete_invoice(self, invoice_id: str):
        pdf_path, xml_path, meta_path = self._get_paths(invoice_id)
        for p in [pdf_path, xml_path, meta_path]:
            if os.path.exists(p):
                os.remove(p)

class GCSStorage(InvoiceStorage):
    def __init__(self, bucket_name: str):
        from google.cloud import storage
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def save_invoice(self, invoice_id: str, pdf_bytes: bytes, xml_content: str, metadata: dict):
        # We store PDF as the main object and attach metadata to it
        blob_pdf = self.bucket.blob(f"{invoice_id}.pdf")
        blob_pdf.upload_from_string(pdf_bytes, content_type="application/pdf")
        
        # Determine if we want to store metadata on the PDF object or separate JSON
        # Storing on object metadata is cheaper but harder to query efficiently if we had millions.
        # But for "listing", GCS list_blobs(include_metadata=True) works.
        # HOWEVER, metadata values must be strings.
        
        # Let's save a sidecar JSON for metadata to avoid string serialization limits/issues and for consistency
        blob_meta = self.bucket.blob(f"{invoice_id}.meta.json")
        blob_meta.upload_from_string(json.dumps(metadata, default=str), content_type="application/json")
        
        blob_xml = self.bucket.blob(f"{invoice_id}.xml")
        blob_xml.upload_from_string(xml_content, content_type="application/xml")

    def get_invoice(self, invoice_id: str) -> Tuple[bytes, str]:
        blob_pdf = self.bucket.blob(f"{invoice_id}.pdf")
        blob_xml = self.bucket.blob(f"{invoice_id}.xml")
        
        if not blob_pdf.exists() or not blob_xml.exists():
            return None
            
        pdf_bytes = blob_pdf.download_as_bytes()
        xml_content = blob_xml.download_as_text()
        return pdf_bytes, xml_content

    def list_invoices(self) -> List[Dict]:
        # To list efficiently without iterating all PDFs, we list all .meta.json files
        blobs = self.bucket.list_blobs(match_glob="*.meta.json")
        invoices = []
        for blob in blobs:
            try:
                content = blob.download_as_text()
                invoices.append(json.loads(content))
            except Exception:
                continue
        return invoices

    def delete_invoice(self, invoice_id: str):
        self.bucket.blob(f"{invoice_id}.pdf").delete(quiet=True)
        self.bucket.blob(f"{invoice_id}.xml").delete(quiet=True)
        self.bucket.blob(f"{invoice_id}.meta.json").delete(quiet=True)

def get_storage() -> InvoiceStorage:
    storage_type = os.getenv("STORAGE_TYPE", "LOCAL").upper()
    if storage_type == "GCS":
        bucket = os.getenv("GCS_BUCKET_NAME")
        if not bucket:
            raise ValueError("GCS_BUCKET_NAME environment variable is required for GCS storage")
        return GCSStorage(bucket)
    return LocalStorage()
