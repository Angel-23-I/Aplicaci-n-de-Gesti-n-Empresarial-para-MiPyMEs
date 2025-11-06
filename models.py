from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class Document(Base):
    """
    Modelo de documento para gestión documental
    Almacena metadatos y referencias a archivos físicos
    """
    __tablename__ = 'documents'
    
    id = Column(String(36), primary_key=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default='general')
    description = Column(Text)
    tags = Column(Text)  # Almacenado como JSON string
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    file_hash = Column(String(64))  # SHA256 hash
    file_extension = Column(String(10))
    version = Column(Integer, default=1)
    created_by = Column(String(100))
    modified_date = Column(DateTime, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relación con versiones del documento
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'title': self.title,
            'category': self.category,
            'description': self.description,
            'tags': json.loads(self.tags) if self.tags else [],
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'file_extension': self.file_extension,
            'version': self.version,
            'created_by': self.created_by,
            'is_active': self.is_active
        }


class DocumentVersion(Base):
    """
    Modelo para control de versiones de documentos
    Mantiene historial de cambios
    """
    __tablename__ = 'document_versions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey('documents.id'), nullable=False)
    version_number = Column(Integer, nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_hash = Column(String(64))
    created_date = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    change_notes = Column(Text)
    
    # Relación con documento principal
    document = relationship("Document", back_populates="versions")
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'version_number': self.version_number,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'created_by': self.created_by,
            'change_notes': self.change_notes
        }


class Invoice(Base):
    """
    Modelo de factura electrónica
    Cumple con Decreto 70/2025/ND-CP de Vietnam
    """
    __tablename__ = 'invoices'
    
    id = Column(String(36), primary_key=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    invoice_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Información del vendedor
    seller_name = Column(String(255), nullable=False)
    seller_tax_code = Column(String(50), nullable=False)
    seller_address = Column(Text)
    seller_phone = Column(String(50))
    seller_email = Column(String(100))
    
    # Información del comprador
    buyer_name = Column(String(255), nullable=False)
    buyer_tax_code = Column(String(50))
    buyer_address = Column(Text)
    buyer_phone = Column(String(50))
    buyer_email = Column(String(100))
    
    # Montos
    subtotal = Column(Float, nullable=False)
    vat_rate = Column(Float, default=0.10)
    vat_amount = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    currency = Column(String(10), default='VND')
    
    # Información adicional
    payment_method = Column(String(100))
    notes = Column(Text)
    
    # Referencias a archivos
    xml_path = Column(String(500))
    pdf_path = Column(String(500))
    
    # Estado y firma
    status = Column(String(50), default='generated')
    is_signed = Column(Boolean, default=False)
    signature_id = Column(String(100))
    signature_timestamp = Column(DateTime)
    
    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    # Relación con items de factura
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'seller_info': {
                'name': self.seller_name,
                'tax_code': self.seller_tax_code,
                'address': self.seller_address,
                'phone': self.seller_phone,
                'email': self.seller_email
            },
            'buyer_info': {
                'name': self.buyer_name,
                'tax_code': self.buyer_tax_code,
                'address': self.buyer_address,
                'phone': self.buyer_phone,
                'email': self.buyer_email
            },
            'subtotal': self.subtotal,
            'vat_rate': self.vat_rate,
            'vat_amount': self.vat_amount,
            'total': self.total,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'notes': self.notes,
            'status': self.status,
            'is_signed': self.is_signed,
            'signature_timestamp': self.signature_timestamp.isoformat() if self.signature_timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items] if self.items else []
        }


class InvoiceItem(Base):
    """
    Modelo de item de factura
    Detalle de productos/servicios
    """
    __tablename__ = 'invoice_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(String(36), ForeignKey('invoices.id'), nullable=False)
    line_number = Column(Integer, nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    unit_of_measure = Column(String(50))
    
    # Relación con factura
    invoice = relationship("Invoice", back_populates="items")
    
    def to_dict(self):
        return {
            'id': self.id,
            'line_number': self.line_number,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'amount': self.amount,
            'unit_of_measure': self.unit_of_measure
        }


class DigitalSignature(Base):
    """
    Modelo de firma digital
    Cumple con Ley ETL No.20/2023/QH15
    """
    __tablename__ = 'digital_signatures'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    signature_id = Column(String(100), unique=True, nullable=False)
    document_path = Column(String(500), nullable=False)
    document_type = Column(String(50))  # 'invoice', 'document', etc.
    
    # Información del firmante
    signer_name = Column(String(255), nullable=False)
    signer_email = Column(String(100))
    signer_tax_code = Column(String(50))
    
    # Datos de la firma
    signature_data = Column(Text, nullable=False)  # Base64 encoded
    document_hash = Column(String(64), nullable=False)
    algorithm = Column(String(50), default='RSA-PSS-SHA256')
    key_size = Column(Integer, default=2048)
    
    # Información de certificado
    certificate_serial = Column(String(100))
    certificate_issuer = Column(String(255))
    
    # Estado y validez
    status = Column(String(50), default='valid')
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_until = Column(DateTime)
    
    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'signature_id': self.signature_id,
            'document_path': self.document_path,
            'document_type': self.document_type,
            'signer_name': self.signer_name,
            'signer_email': self.signer_email,
            'signer_tax_code': self.signer_tax_code,
            'algorithm': self.algorithm,
            'key_size': self.key_size,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None
        }


class AuditLog(Base):
    """
    Modelo de auditoría
    Registra todas las acciones del sistema
    """
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user = Column(String(100))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(String(36))
    details = Column(Text)
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user': self.user,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': self.details,
            'ip_address': self.ip_address
        }


# Función para inicializar la base de datos
def init_db(database_url='sqlite:///mipyme.db'):
    """
    Inicializa la base de datos con todas las tablas
    """
    engine = create_engine(database_url, echo=True)
    Base.metadata.create_all(engine)
    return engine


# Crear sesión de base de datos
def get_session(engine):
    """
    Crea y retorna una sesión de SQLAlchemy
    """
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == '__main__':
    # Inicializar base de datos
    engine = init_db()
    print("Base de datos inicializada correctamente")
    
    # Crear sesión de prueba
    session = get_session(engine)
    print("Sesión de base de datos creada")
