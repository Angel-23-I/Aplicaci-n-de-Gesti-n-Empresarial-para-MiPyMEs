import os
import json
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import xml.etree.ElementTree as ET
from xml.dom import minidom

class InvoiceGenerator:
    """
    Generador de facturas electrónicas según legislación vietnamita
    Cumple con Decreto 70/2025/ND-CP y Circular 32/2025
    Formato: XML para autoridades + PDF para cliente
    """
    
    def __init__(self, invoice_folder):
        self.invoice_folder = invoice_folder
        self.metadata_file = os.path.join(invoice_folder, 'invoices_metadata.json')
        self._load_metadata()
    
    def _load_metadata(self):
        """Carga metadatos de facturas"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.invoices = json.load(f)
        else:
            self.invoices = {}
            self._save_metadata()
    
    def _save_metadata(self):
        """Guarda metadatos de facturas"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.invoices, f, indent=2, ensure_ascii=False)
    
    def create_invoice(self, data):
        """
        Crea factura electrónica en formato XML y PDF
        Cumple con requisitos del Decreto 70/2025/ND-CP
        """
        invoice_id = str(uuid.uuid4())
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{len(self.invoices) + 1:05d}"
        invoice_date = datetime.now()
        
        # Calcular totales
        subtotal = sum(item['quantity'] * item['unit_price'] for item in data['items'])
        vat_rate = data.get('vat_rate', 0.10)  # 10% VAT por defecto en Vietnam
        vat_amount = subtotal * vat_rate
        total = subtotal + vat_amount
        
        invoice_data = {
            'id': invoice_id,
            'invoice_number': invoice_number,
            'invoice_date': invoice_date.isoformat(),
            'seller_info': data['seller_info'],
            'buyer_info': data['buyer_info'],
            'items': data['items'],
            'subtotal': subtotal,
            'vat_rate': vat_rate,
            'vat_amount': vat_amount,
            'total': total,
            'currency': data.get('currency', 'VND'),
            'payment_method': data['payment_method'],
            'notes': data.get('notes', '')
        }
        
        # Generar XML (formato requerido por autoridades vietnamitas)
        xml_path = self._generate_xml(invoice_id, invoice_data)
        
        # Generar PDF (para el cliente)
        pdf_path = self._generate_pdf(invoice_id, invoice_data)
        
        # Guardar metadata
        self.invoices[invoice_id] = {
            **invoice_data,
            'xml_path': xml_path,
            'pdf_path': pdf_path,
            'status': 'generated',
            'created_at': invoice_date.isoformat()
        }
        self._save_metadata()
        
        return {
            'success': True,
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'xml_path': xml_path,
            'pdf_path': pdf_path,
            'total': total
        }
    
    def _generate_xml(self, invoice_id, data):
        """
        Genera factura en formato XML según estándares vietnamitas
        Formato basado en Decreto 123/2020/ND-CP y Decreto 70/2025/ND-CP
        """
        # Crear estructura XML
        invoice = ET.Element('Invoice')
        invoice.set('xmlns', 'http://www.gdt.gov.vn/einvoice')
        invoice.set('version', '2.0')
        
        # Información general
        general_info = ET.SubElement(invoice, 'GeneralInformation')
        ET.SubElement(general_info, 'InvoiceNumber').text = data['invoice_number']
        ET.SubElement(general_info, 'InvoiceDate').text = data['invoice_date']
        ET.SubElement(general_info, 'Currency').text = data['currency']
        ET.SubElement(general_info, 'ExchangeRate').text = '1'
        
        # Información del vendedor
        seller = ET.SubElement(invoice, 'Seller')
        seller_info = data['seller_info']
        ET.SubElement(seller, 'TaxCode').text = seller_info.get('tax_code', '')
        ET.SubElement(seller, 'LegalName').text = seller_info.get('name', '')
        ET.SubElement(seller, 'Address').text = seller_info.get('address', '')
        ET.SubElement(seller, 'Phone').text = seller_info.get('phone', '')
        ET.SubElement(seller, 'Email').text = seller_info.get('email', '')
        
        # Información del comprador
        buyer = ET.SubElement(invoice, 'Buyer')
        buyer_info = data['buyer_info']
        ET.SubElement(buyer, 'TaxCode').text = buyer_info.get('tax_code', '')
        ET.SubElement(buyer, 'Name').text = buyer_info.get('name', '')
        ET.SubElement(buyer, 'Address').text = buyer_info.get('address', '')
        ET.SubElement(buyer, 'Phone').text = buyer_info.get('phone', '')
        ET.SubElement(buyer, 'Email').text = buyer_info.get('email', '')
        
        # Detalle de productos/servicios
        items_section = ET.SubElement(invoice, 'Items')
        for idx, item in enumerate(data['items'], 1):
            item_elem = ET.SubElement(items_section, 'Item')
            ET.SubElement(item_elem, 'LineNumber').text = str(idx)
            ET.SubElement(item_elem, 'Description').text = item['description']
            ET.SubElement(item_elem, 'Quantity').text = str(item['quantity'])
            ET.SubElement(item_elem, 'UnitPrice').text = str(item['unit_price'])
            ET.SubElement(item_elem, 'Amount').text = str(item['quantity'] * item['unit_price'])
            ET.SubElement(item_elem, 'VATRate').text = str(data['vat_rate'] * 100)
        
        # Totales
        summary = ET.SubElement(invoice, 'Summary')
        ET.SubElement(summary, 'Subtotal').text = str(data['subtotal'])
        ET.SubElement(summary, 'VATAmount').text = str(data['vat_amount'])
        ET.SubElement(summary, 'Total').text = str(data['total'])
        
        # Información de pago
        payment = ET.SubElement(invoice, 'PaymentInformation')
        ET.SubElement(payment, 'PaymentMethod').text = data['payment_method']
        
        # Guardar XML formateado
        xml_string = minidom.parseString(ET.tostring(invoice)).toprettyxml(indent="  ")
        xml_path = os.path.join(self.invoice_folder, f"{invoice_id}.xml")
        
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_string)
        
        return xml_path
    
    def _generate_pdf(self, invoice_id, data):
        """Genera PDF de la factura para el cliente"""
        pdf_path = os.path.join(self.invoice_folder, f"{invoice_id}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        
        # Título
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "FACTURA ELECTRÓNICA / E-INVOICE")
        
        # Información de la factura
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 80, f"Número de Factura: {data['invoice_number']}")
        c.drawString(50, height - 95, f"Fecha: {datetime.fromisoformat(data['invoice_date']).strftime('%d/%m/%Y %H:%M')}")
        
        # Línea separadora
        c.line(50, height - 110, width - 50, height - 110)
        
        # Información del vendedor
        y_pos = height - 140
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_pos, "VENDEDOR:")
        c.setFont("Helvetica", 10)
        seller = data['seller_info']
        c.drawString(50, y_pos - 20, f"Nombre: {seller.get('name', '')}")
        c.drawString(50, y_pos - 35, f"NIT/Tax Code: {seller.get('tax_code', '')}")
        c.drawString(50, y_pos - 50, f"Dirección: {seller.get('address', '')}")
        c.drawString(50, y_pos - 65, f"Teléfono: {seller.get('phone', '')} | Email: {seller.get('email', '')}")
        
        # Información del comprador
        y_pos = y_pos - 100
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_pos, "CLIENTE:")
        c.setFont("Helvetica", 10)
        buyer = data['buyer_info']
        c.drawString(50, y_pos - 20, f"Nombre: {buyer.get('name', '')}")
        c.drawString(50, y_pos - 35, f"NIT/Tax Code: {buyer.get('tax_code', '')}")
        c.drawString(50, y_pos - 50, f"Dirección: {buyer.get('address', '')}")
        
        # Tabla de productos/servicios
        y_pos = y_pos - 90
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y_pos, "DETALLE DE PRODUCTOS/SERVICIOS:")
        
        # Encabezados de tabla
        y_pos -= 20
        c.drawString(50, y_pos, "#")
        c.drawString(80, y_pos, "Descripción")
        c.drawString(300, y_pos, "Cant.")
        c.drawString(350, y_pos, "Precio Unit.")
        c.drawString(450, y_pos, "Total")
        
        c.line(50, y_pos - 5, width - 50, y_pos - 5)
        
        # Items
        c.setFont("Helvetica", 9)
        y_pos -= 20
        for idx, item in enumerate(data['items'], 1):
            if y_pos < 150:  # Nueva página si es necesario
                c.showPage()
                y_pos = height - 50
            
            c.drawString(50, y_pos, str(idx))
            c.drawString(80, y_pos, item['description'][:30])
            c.drawString(300, y_pos, str(item['quantity']))
            c.drawString(350, y_pos, f"{item['unit_price']:,.2f}")
            c.drawString(450, y_pos, f"{item['quantity'] * item['unit_price']:,.2f}")
            y_pos -= 15
        
        # Línea antes de totales
        c.line(50, y_pos - 5, width - 50, y_pos - 5)
        
        # Totales
        y_pos -= 25
        c.setFont("Helvetica", 10)
        c.drawString(350, y_pos, "Subtotal:")
        c.drawString(450, y_pos, f"{data['subtotal']:,.2f} {data['currency']}")
        
        y_pos -= 20
        c.drawString(350, y_pos, f"IVA ({data['vat_rate']*100:.0f}%):")
        c.drawString(450, y_pos, f"{data['vat_amount']:,.2f} {data['currency']}")
        
        y_pos -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(350, y_pos, "TOTAL:")
        c.drawString(450, y_pos, f"{data['total']:,.2f} {data['currency']}")
        
        # Método de pago
        y_pos -= 40
        c.setFont("Helvetica", 10)
        c.drawString(50, y_pos, f"Método de Pago: {data['payment_method']}")
        
        # Notas
        if data.get('notes'):
            y_pos -= 30
            c.drawString(50, y_pos, f"Notas: {data['notes']}")
        
        # Pie de página
        c.setFont("Helvetica", 8)
        c.drawString(50, 50, "Factura Electrónica Válida según Decreto 70/2025/ND-CP de Vietnam")
        c.drawString(50, 35, f"ID de Factura: {invoice_id}")
        
        c.save()
        return pdf_path
    
    def get_invoice(self, invoice_id):
        """Obtiene información de una factura"""
        return self.invoices.get(invoice_id)
    
    def get_invoice_pdf_path(self, invoice_id):
        """Obtiene la ruta del PDF de una factura"""
        invoice = self.invoices.get(invoice_id)
        return invoice['pdf_path'] if invoice else None
    
    def get_invoice_xml_path(self, invoice_id):
        """Obtiene la ruta del XML de una factura"""
        invoice = self.invoices.get(invoice_id)
        return invoice['xml_path'] if invoice else None
    
    def list_all_invoices(self):
        """Lista todas las facturas"""
        return list(self.invoices.values())
    
    def get_invoice_count(self):
        """Obtiene el total de facturas"""
        return len(self.invoices)
