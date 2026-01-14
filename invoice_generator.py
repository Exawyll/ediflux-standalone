from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from facturx import generate_from_file
from models import InvoiceRequest
import os
import tempfile
from datetime import datetime

# Setup Jinja2 environment
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(loader=FileSystemLoader(templates_dir))

from typing import Tuple

def generate_invoice_pdf(invoice: InvoiceRequest) -> Tuple[bytes, str]:
    # 1. Render HTML
    template = env.get_template('invoice.html')
    
    # Calculate totals
    total_tax_basis = sum(item.quantity * item.unit_price for item in invoice.items)
    # Group by VAT rate for simple calculation
    vat_amounts = {}
    for item in invoice.items:
        line_total = item.quantity * item.unit_price
        vat_amount = line_total * (item.vat_rate / 100)
        if item.vat_rate not in vat_amounts:
            vat_amounts[item.vat_rate] = 0
        vat_amounts[item.vat_rate] += vat_amount
    
    total_vat = sum(vat_amounts.values())
    total_with_tax = total_tax_basis + total_vat

    context = {
        "invoice": invoice,
        "total_tax_basis": total_tax_basis,
        "total_vat": total_vat,
        "total_with_tax": total_with_tax,
        "vat_amounts": vat_amounts
    }
    
    html_content = template.render(**context)
    
    # 2. Generate PDF
    # We write to a temporary file because factur-x usually expects file paths or reading bytes
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    # 3. Add Factur-X XML
    xml_content = generate_facturx_xml(invoice, total_tax_basis, total_vat, total_with_tax, vat_amounts)
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f_pdf:
            f_pdf.write(pdf_bytes)
            f_pdf_path = f_pdf.name
            
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False, mode='w', encoding='utf-8') as f_xml:
            f_xml.write(xml_content)
            f_xml_path = f_xml.name
            
        output_path = f_pdf_path + "_fx.pdf"
        generate_from_file(f_pdf_path, f_xml_path, output_pdf_file=output_path)
        
        with open(output_path, "rb") as f_out:
            final_pdf = f_out.read()
            
        # Cleanup
        os.remove(f_pdf_path)
        os.remove(f_xml_path)
        os.remove(output_path)
        
        return final_pdf, xml_content
        
    except Exception as e:
        print(f"Error generating Factur-X: {e}")
        # Fallback to just PDF if XML fails (or re-raise)
        return pdf_bytes, xml_content
        
    except Exception as e:
        print(f"Error generating Factur-X: {e}")
        # Fallback to just PDF if XML fails (or re-raise)
        return pdf_bytes, xml_content

def generate_facturx_xml(invoice: InvoiceRequest, total_tax_basis, total_vat, total_with_tax, vat_amounts):
    # This is a VERY simplified XML generator for Factur-X Minimal/Basic profile
    # In a real app, use a proper templating engine or XML builder for CII
    
    # We will use Jinja2 for XML as well for simplicity
    template = env.get_template('factur-x.xml')
    
    context = {
        "invoice": invoice,
        "total_tax_basis": total_tax_basis,
        "total_vat": total_vat,
        "total_with_tax": total_with_tax,
        "vat_amounts": vat_amounts,
        "now": datetime.now()
    }
    return template.render(**context)
