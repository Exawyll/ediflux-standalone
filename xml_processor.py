"""
XML Processor module for extracting and validating Factur-X/CII XML from invoices.
Supports both PDF Factur-X files (with embedded XML) and standalone CII XML files.
"""
from lxml import etree
from typing import Optional, Tuple
from io import BytesIO

# Factur-X uses the facturx library for PDF/XML extraction
try:
    from facturx import get_xml_from_pdf
except ImportError:
    get_xml_from_pdf = None

# CII XML namespaces
NAMESPACES = {
    'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
    'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
    'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100',
    'qdt': 'urn:un:unece:uncefact:data:standard:QualifiedDataType:100',
}


def extract_xml_from_pdf(pdf_bytes: bytes) -> Optional[str]:
    """
    Extract embedded Factur-X XML from a PDF file.

    Args:
        pdf_bytes: The PDF file content as bytes

    Returns:
        The XML content as string, or None if extraction failed
    """
    if get_xml_from_pdf is None:
        raise ImportError("facturx library is required for PDF extraction")

    try:
        result = get_xml_from_pdf(BytesIO(pdf_bytes))

        if result is None:
            return None

        # get_xml_from_pdf returns (filename, xml_bytes) tuple
        if isinstance(result, tuple) and len(result) >= 2:
            xml_data = result[1]  # XML content is the second element
        else:
            xml_data = result

        if isinstance(xml_data, bytes):
            return xml_data.decode('utf-8')
        elif isinstance(xml_data, str):
            return xml_data
        else:
            return None

    except Exception:
        return None


def validate_cii_xml(xml_content: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that the XML content is a valid CII/EN16931 invoice.
    Performs structural validation (not schema validation).

    Args:
        xml_content: The XML content as string

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        root = etree.fromstring(xml_content.encode('utf-8'))

        # Check root element is CrossIndustryInvoice
        if not root.tag.endswith('CrossIndustryInvoice'):
            return False, "Root element is not CrossIndustryInvoice"

        # Check for required CII structure elements
        required_elements = [
            '//rsm:ExchangedDocumentContext',
            '//rsm:ExchangedDocument',
            '//rsm:SupplyChainTradeTransaction',
        ]

        for xpath in required_elements:
            if root.xpath(xpath, namespaces=NAMESPACES) is None or len(root.xpath(xpath, namespaces=NAMESPACES)) == 0:
                return False, f"Missing required element: {xpath}"

        # Check for invoice ID
        invoice_id = root.xpath('//rsm:ExchangedDocument/ram:ID/text()', namespaces=NAMESPACES)
        if not invoice_id:
            return False, "Missing invoice ID (ExchangedDocument/ID)"

        # Check for seller and buyer
        seller = root.xpath('//ram:SellerTradeParty/ram:Name/text()', namespaces=NAMESPACES)
        buyer = root.xpath('//ram:BuyerTradeParty/ram:Name/text()', namespaces=NAMESPACES)

        if not seller:
            return False, "Missing seller name"
        if not buyer:
            return False, "Missing buyer name"

        return True, None

    except etree.XMLSyntaxError as e:
        return False, f"XML syntax error: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def extract_metadata_from_xml(xml_content: str) -> dict:
    """
    Extract invoice metadata from CII XML content.

    Args:
        xml_content: The XML content as string

    Returns:
        Dictionary with extracted metadata
    """
    try:
        # Handle both bytes and string input
        if isinstance(xml_content, bytes):
            xml_bytes = xml_content
        else:
            xml_bytes = xml_content.encode('utf-8')

        root = etree.fromstring(xml_bytes)

        # Get namespaces from the document itself
        nsmap = root.nsmap.copy()
        # Handle default namespace
        if None in nsmap:
            del nsmap[None]

        # Merge with our known namespaces, preferring document's
        namespaces = {**NAMESPACES, **nsmap}

        def get_text(xpath: str, default: str = '') -> str:
            result = root.xpath(xpath, namespaces=namespaces)
            if result and len(result) > 0:
                return str(result[0]).strip()
            return default

        def get_float(xpath: str, default: float = 0.0) -> float:
            text = get_text(xpath)
            if text:
                try:
                    return float(text)
                except ValueError:
                    pass
            return default

        # Extract invoice ID
        invoice_id = get_text('//rsm:ExchangedDocument/ram:ID/text()')

        # Extract date - try multiple formats
        date_str = get_text('//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString/text()')
        # Convert YYYYMMDD to YYYY-MM-DD if needed
        if date_str and len(date_str) == 8 and date_str.isdigit():
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        elif not date_str:
            # Try alternative date location
            date_str = get_text('//ram:IssueDateTime/udt:DateTimeString/text()')
            if date_str and len(date_str) == 8 and date_str.isdigit():
                date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

        # Extract seller and buyer names - they are under ApplicableHeaderTradeAgreement
        seller_name = get_text('//ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty/ram:Name/text()')
        if not seller_name:
            seller_name = get_text('//ram:SellerTradeParty/ram:Name/text()')

        buyer_name = get_text('//ram:ApplicableHeaderTradeAgreement/ram:BuyerTradeParty/ram:Name/text()')
        if not buyer_name:
            buyer_name = get_text('//ram:BuyerTradeParty/ram:Name/text()')

        # Extract currency - under ApplicableHeaderTradeSettlement
        currency = get_text('//ram:ApplicableHeaderTradeSettlement/ram:InvoiceCurrencyCode/text()')
        if not currency:
            currency = get_text('//ram:InvoiceCurrencyCode/text()', 'EUR')

        # Extract totals from SpecifiedTradeSettlementHeaderMonetarySummation
        total_ht = get_float('//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxBasisTotalAmount/text()')
        if total_ht == 0:
            total_ht = get_float('//ram:TaxBasisTotalAmount/text()')

        total_ttc = get_float('//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:GrandTotalAmount/text()')
        if total_ttc == 0:
            total_ttc = get_float('//ram:GrandTotalAmount/text()')

        total_tax = get_float('//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxTotalAmount/text()')
        if total_tax == 0:
            total_tax = get_float('//ram:TaxTotalAmount/text()')

        # Extract seller address - under ApplicableHeaderTradeAgreement/SellerTradeParty
        seller_street = get_text('//ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty/ram:PostalTradeAddress/ram:LineOne/text()')
        if not seller_street:
            seller_street = get_text('//ram:SellerTradeParty/ram:PostalTradeAddress/ram:LineOne/text()')

        seller_city = get_text('//ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty/ram:PostalTradeAddress/ram:CityName/text()')
        if not seller_city:
            seller_city = get_text('//ram:SellerTradeParty/ram:PostalTradeAddress/ram:CityName/text()')

        seller_zip = get_text('//ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty/ram:PostalTradeAddress/ram:PostcodeCode/text()')
        if not seller_zip:
            seller_zip = get_text('//ram:SellerTradeParty/ram:PostalTradeAddress/ram:PostcodeCode/text()')

        seller_country = get_text('//ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty/ram:PostalTradeAddress/ram:CountryID/text()')
        if not seller_country:
            seller_country = get_text('//ram:SellerTradeParty/ram:PostalTradeAddress/ram:CountryID/text()')

        seller_vat = get_text('//ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty/ram:SpecifiedTaxRegistration/ram:ID/text()')
        if not seller_vat:
            seller_vat = get_text('//ram:SellerTradeParty/ram:SpecifiedTaxRegistration/ram:ID/text()')

        seller_address_parts = [p for p in [seller_street, f"{seller_zip} {seller_city}".strip(), seller_country] if p]
        seller_address = ', '.join(seller_address_parts) if seller_address_parts else ''

        # Extract buyer address - under ApplicableHeaderTradeAgreement/BuyerTradeParty
        buyer_street = get_text('//ram:ApplicableHeaderTradeAgreement/ram:BuyerTradeParty/ram:PostalTradeAddress/ram:LineOne/text()')
        if not buyer_street:
            buyer_street = get_text('//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:LineOne/text()')

        buyer_city = get_text('//ram:ApplicableHeaderTradeAgreement/ram:BuyerTradeParty/ram:PostalTradeAddress/ram:CityName/text()')
        if not buyer_city:
            buyer_city = get_text('//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:CityName/text()')

        buyer_zip = get_text('//ram:ApplicableHeaderTradeAgreement/ram:BuyerTradeParty/ram:PostalTradeAddress/ram:PostcodeCode/text()')
        if not buyer_zip:
            buyer_zip = get_text('//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:PostcodeCode/text()')

        buyer_country = get_text('//ram:ApplicableHeaderTradeAgreement/ram:BuyerTradeParty/ram:PostalTradeAddress/ram:CountryID/text()')
        if not buyer_country:
            buyer_country = get_text('//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:CountryID/text()')

        buyer_vat = get_text('//ram:ApplicableHeaderTradeAgreement/ram:BuyerTradeParty/ram:SpecifiedTaxRegistration/ram:ID/text()')
        if not buyer_vat:
            buyer_vat = get_text('//ram:BuyerTradeParty/ram:SpecifiedTaxRegistration/ram:ID/text()')

        buyer_address_parts = [p for p in [buyer_street, f"{buyer_zip} {buyer_city}".strip(), buyer_country] if p]
        buyer_address = ', '.join(buyer_address_parts) if buyer_address_parts else ''

        metadata = {
            'id': invoice_id,
            'date': date_str,
            'seller_name': seller_name,
            'seller_address': seller_address,
            'seller_vat': seller_vat,
            'buyer_name': buyer_name,
            'buyer_address': buyer_address,
            'buyer_vat': buyer_vat,
            'currency': currency,
            'total_ht': round(total_ht, 2),
            'total_ttc': round(total_ttc, 2),
            'total_tax': round(total_tax, 2),
            'created_at': date_str,
            'source': 'upload'
        }

        # Mark as valid only if we got essential fields
        metadata['_valid'] = bool(invoice_id and seller_name and buyer_name)

        return metadata

    except Exception:
        return {
            'id': '',
            'date': '',
            'seller_name': '',
            'buyer_name': '',
            'currency': 'EUR',
            'total_ht': 0,
            'total_ttc': 0,
            'source': 'upload',
            '_valid': False
        }


def create_placeholder_pdf(xml_content: str, metadata: dict) -> bytes:
    """
    Create a placeholder PDF for XML-only uploads.
    Uses WeasyPrint to generate a simple PDF displaying invoice metadata.

    Args:
        xml_content: The original XML content
        metadata: Extracted metadata dictionary

    Returns:
        PDF bytes
    """
    from jinja2 import Environment, FileSystemLoader
    from weasyprint import HTML
    import os

    # Setup Jinja2 environment
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(templates_dir))

    try:
        template = env.get_template('upload-placeholder.html')
        html_content = template.render(metadata=metadata)
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except Exception:
        # Fallback to a very simple PDF
        simple_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Invoice {metadata.get('id', 'Unknown')}</title></head>
        <body>
            <h1>Invoice {metadata.get('id', 'Unknown')}</h1>
            <p>Date: {metadata.get('date', 'N/A')}</p>
            <p>Seller: {metadata.get('seller_name', 'N/A')}</p>
            <p>Buyer: {metadata.get('buyer_name', 'N/A')}</p>
            <p>Total HT: {metadata.get('total_ht', 0)} {metadata.get('currency', 'EUR')}</p>
            <p>Total TTC: {metadata.get('total_ttc', 0)} {metadata.get('currency', 'EUR')}</p>
            <hr>
            <p><em>Document imported from CII XML</em></p>
        </body>
        </html>
        """
        return HTML(string=simple_html).write_pdf()
