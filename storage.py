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
    def get_invoice_metadata(self, invoice_id: str) -> Optional[Dict]:
        """Returns metadata dict for a specific invoice"""
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

    def get_invoice_metadata(self, invoice_id: str) -> Optional[Dict]:
        _, _, meta_path = self._get_paths(invoice_id)
        if not os.path.exists(meta_path):
            return None
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def delete_invoice(self, invoice_id: str):
        pdf_path, xml_path, meta_path = self._get_paths(invoice_id)
        for p in [pdf_path, xml_path, meta_path]:
            if os.path.exists(p):
                os.remove(p)


def get_storage() -> InvoiceStorage:
    # Always use LocalStorage as GCS support has been removed
    return LocalStorage()
