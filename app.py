from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import os
from document_manager import DocumentManager
from invoice_generator import InvoiceGenerator
from digital_signature import DigitalSignature

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['INVOICE_FOLDER'] = 'invoices'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Crear directorios necesarios
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['INVOICE_FOLDER'], exist_ok=True)

# Inicializar módulos
doc_manager = DocumentManager(app.config['UPLOAD_FOLDER'])
invoice_gen = InvoiceGenerator(app.config['INVOICE_FOLDER'])
digital_sig = DigitalSignature()

@app.route('/')
def index():
    """Página principal del sistema"""
    stats = {
        'total_documents': doc_manager.get_document_count(),
        'total_invoices': invoice_gen.get_invoice_count(),
        'pending_signatures': digital_sig.get_pending_count()
    }
    return render_template('index.html', stats=stats)

# ============== MÓDULO DE GESTIÓN DOCUMENTAL ==============

@app.route('/documents', methods=['GET'])
def documents_page():
    """Página principal de gestión documental"""
    return render_template('documents.html')

@app.route('/documents/list', methods=['GET'])
def list_documents():
    """API: Lista todos los documentos (JSON)"""
    documents = doc_manager.list_all_documents()
    return jsonify({'documents': documents})

@app.route('/documents/upload', methods=['POST'])
def upload_document():
    """Sube un nuevo documento"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    metadata = {
        'title': request.form.get('title', ''),
        'category': request.form.get('category', 'general'),
        'description': request.form.get('description', ''),
        'tags': request.form.get('tags', '').split(',')
    }
    
    result = doc_manager.upload_document(file, metadata)
    return jsonify(result)

@app.route('/documents/<doc_id>', methods=['GET'])
def get_document(doc_id):
    """Obtiene un documento específico"""
    document = doc_manager.get_document(doc_id)
    if document:
        return jsonify(document)
    return jsonify({'error': 'Document not found'}), 404

@app.route('/documents/<doc_id>/download', methods=['GET'])
def download_document(doc_id):
    """Descarga un documento"""
    file_path = doc_manager.get_document_path(doc_id)
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'Document not found'}), 404

@app.route('/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Elimina un documento"""
    result = doc_manager.delete_document(doc_id)
    return jsonify(result)

@app.route('/documents/search', methods=['GET'])
def search_documents():
    """Busca documentos por criterios"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    results = doc_manager.search_documents(query, category)
    return jsonify({'results': results})

# ============== MÓDULO DE FACTURACIÓN ELECTRÓNICA ==============

@app.route('/invoices', methods=['GET'])
def invoices_page():
    """Página principal de facturación electrónica"""
    return render_template('invoices.html')

@app.route('/invoices/list', methods=['GET'])
def list_invoices():
    """API: Lista todas las facturas (JSON)"""
    invoices = invoice_gen.list_all_invoices()
    return jsonify({'invoices': invoices})

@app.route('/invoices/create', methods=['POST'])
def create_invoice():
    """Crea una nueva factura electrónica según Decreto 70/2025/ND-CP"""
    data = request.json
    
    # Validar datos requeridos según legislación vietnamita
    required_fields = ['seller_info', 'buyer_info', 'items', 'payment_method']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Generar factura en formato XML y PDF
    invoice_data = invoice_gen.create_invoice(data)
    
    # Firmar digitalmente la factura
    xml_path = invoice_data['xml_path']
    signed_xml = digital_sig.sign_xml_invoice(xml_path)
    
    invoice_data['signed'] = True
    invoice_data['signature_timestamp'] = datetime.now().isoformat()
    
    return jsonify(invoice_data)

@app.route('/invoices/<invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    """Obtiene una factura específica"""
    invoice = invoice_gen.get_invoice(invoice_id)
    if invoice:
        return jsonify(invoice)
    return jsonify({'error': 'Invoice not found'}), 404

@app.route('/invoices/<invoice_id>/pdf', methods=['GET'])
def download_invoice_pdf(invoice_id):
    """Descarga el PDF de una factura"""
    pdf_path = invoice_gen.get_invoice_pdf_path(invoice_id)
    if pdf_path and os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return jsonify({'error': 'Invoice PDF not found'}), 404

@app.route('/invoices/<invoice_id>/xml', methods=['GET'])
def download_invoice_xml(invoice_id):
    """Descarga el XML de una factura (formato requerido por autoridades)"""
    xml_path = invoice_gen.get_invoice_xml_path(invoice_id)
    if xml_path and os.path.exists(xml_path):
        return send_file(xml_path, as_attachment=True, mimetype='application/xml')
    return jsonify({'error': 'Invoice XML not found'}), 404

# ============== MÓDULO DE FIRMA DIGITAL ==============

@app.route('/signature', methods=['GET'])
def signature_page():
    """Página principal de firma digital"""
    return render_template('signature.html')

@app.route('/signature/sign', methods=['POST'])
def sign_document():
    """Firma digitalmente un documento según Ley de Transacciones Electrónicas"""
    data = request.json
    document_path = data.get('document_path')
    signer_info = data.get('signer_info')
    
    if not document_path or not os.path.exists(document_path):
        return jsonify({'error': 'Document not found'}), 404
    
    signature_result = digital_sig.sign_document(document_path, signer_info)
    return jsonify(signature_result)

@app.route('/signature/verify', methods=['POST'])
def verify_signature():
    """Verifica una firma digital"""
    data = request.json
    signed_document_path = data.get('document_path')
    
    verification_result = digital_sig.verify_signature(signed_document_path)
    return jsonify(verification_result)

@app.route('/signature/list', methods=['GET'])
def list_signatures():
    """Lista todas las firmas digitales"""
    signatures = list(digital_sig.signatures.values())
    return jsonify({'signatures': signatures})

@app.route('/signature/document/<doc_id>', methods=['POST'])
def sign_specific_document(doc_id):
    """Firma un documento específico del sistema de gestión documental"""
    document_path = doc_manager.get_document_path(doc_id)
    
    if not document_path:
        return jsonify({'error': 'Document not found'}), 404
    
    # Obtener información del documento
    doc = doc_manager.get_document(doc_id)
    
    # Información del firmante (puede venir del request o usar valores por defecto)
    data = request.json or {}
    signer_info = {
        'name': data.get('signer_name', 'Usuario del Sistema'),
        'email': data.get('signer_email', 'usuario@mipyme.vn'),
        'tax_code': data.get('signer_tax_code', 'TAX-CODE-001')
    }
    
    signature_result = digital_sig.sign_document(document_path, signer_info)
    
    if signature_result.get('success'):
        signature_result['document_info'] = {
            'title': doc['title'],
            'category': doc['category'],
            'original_filename': doc['original_filename']
        }
    
    return jsonify(signature_result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
