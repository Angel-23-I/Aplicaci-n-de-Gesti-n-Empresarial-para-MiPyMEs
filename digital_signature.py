import os
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
import base64
import json

class DigitalSignature:
    """
    Módulo de firma digital según legislación vietnamita
    Cumple con Ley de Transacciones Electrónicas No.20/2023/QH15
    y Decreto No.130/2018/ND-CP
    Simula firma digital tipo 2 (Public digital signature)
    """

    def __init__(self):
        self.keys_folder = 'digital_keys'
        os.makedirs(self.keys_folder, exist_ok=True)
        self.signatures_file = os.path.join(self.keys_folder, 'signatures.json')
        self._load_signatures()

        # Generar par de claves si no existen
        self.private_key_path = os.path.join(self.keys_folder, 'private_key.pem')
        self.public_key_path = os.path.join(self.keys_folder, 'public_key.pem')
        self.certificate_path = os.path.join(self.keys_folder, 'certificate.pem')

        if not os.path.exists(self.private_key_path):
            self._generate_keys()

    def _load_signatures(self):
        """Carga registro de firmas"""
        if os.path.exists(self.signatures_file):
            with open(self.signatures_file, 'r', encoding='utf-8') as f:
                self.signatures = json.load(f)
        else:
            self.signatures = {}
            self._save_signatures()

    def _save_signatures(self):
        """Guarda registro de firmas"""
        with open(self.signatures_file, 'w', encoding='utf-8') as f:
            json.dump(self.signatures, f, indent=2, ensure_ascii=False)

    def _generate_keys(self):
        """
        Genera par de claves RSA y certificado autofirmado
        Simulación de certificado digital vietnamita
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        with open(self.private_key_path, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        public_key = private_key.public_key()
        with open(self.public_key_path, 'wb') as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "VN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Hanoi"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Hanoi"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MiPyME Demo"),
            x509.NameAttribute(NameOID.COMMON_NAME, "demo.mipyme.vn"),
        ])
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            public_key
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(private_key, hashes.SHA256(), default_backend())
        with open(self.certificate_path, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

    def _load_private_key(self):
        """Carga la clave privada"""
        with open(self.private_key_path, 'rb') as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )

    def _load_public_key(self):
        """Carga la clave pública"""
        with open(self.public_key_path, 'rb') as f:
            return serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )

    def sign_document(self, document_path, signer_info):
        """
        Firma digitalmente un documento
        Tipo 2: Firma digital pública según ETL 2023
        """
        if not os.path.exists(document_path):
            return {'error': 'Document not found'}

        # Leer contenido del documento
        with open(document_path, 'rb') as f:
            document_data = f.read()

        # Calcular hash del documento
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(document_data)
        document_hash = digest.finalize()

        # Firmar el hash con la clave privada
        private_key = self._load_private_key()
        signature = private_key.sign(
            document_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Codificar firma en base64
        signature_b64 = base64.b64encode(signature).decode('utf-8')

        # Guardar información de la firma
        signature_id = f"SIG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        signature_data = {
            'signature_id': signature_id,
            'document_path': os.path.normpath(document_path),
            'signer_name': signer_info.get('name', ''),
            'signer_email': signer_info.get('email', ''),
            'signer_tax_code': signer_info.get('tax_code', ''),
            'signature': signature_b64,
            'document_hash': base64.b64encode(document_hash).decode('utf-8'),
            'timestamp': datetime.now().isoformat(),
            'algorithm': 'RSA-PSS-SHA256',
            'key_size': 2048,
            'status': 'valid'
        }
        self.signatures[signature_id] = signature_data
        self._save_signatures()

        return {
            'success': True,
            'signature_id': signature_id,
            'signature': signature_b64,
            'timestamp': signature_data['timestamp'],
            'signer': signer_info.get('name', ''),
            'message': 'Document signed successfully with Vietnamese digital signature standard'
        }

    def verify_signature(self, signed_document_path):
        """
        Verifica una firma digital
        Valida integridad y autenticidad según estándares vietnamitas
        """
        normalized_path = os.path.normpath(signed_document_path)
        signature_data = None
        for sig_id, sig in self.signatures.items():
            if os.path.normpath(sig['document_path']) == normalized_path:
                signature_data = sig
                break

        if not signature_data:
            return {
                'valid': False,
                'error': 'No signature found for this document'
            }

        # Leer contenido del documento
        with open(signed_document_path, 'rb') as f:
            document_data = f.read()

        # Calcular hash del documento actual
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(document_data)
        current_hash = digest.finalize()

        # Comparar con hash almacenado
        stored_hash = base64.b64decode(signature_data['document_hash'])

        if current_hash != stored_hash:
            return {
                'valid': False,
                'error': 'Document has been modified after signing',
                'integrity': 'compromised'
            }

        # Verificar firma con clave pública
        try:
            signature = base64.b64decode(signature_data['signature'])
            public_key = self._load_public_key()
            public_key.verify(
                signature,
                current_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return {
                'valid': True,
                'signature_id': signature_data['signature_id'],
                'signer': signature_data['signer_name'],
                'timestamp': signature_data['timestamp'],
                'algorithm': signature_data['algorithm'],
                'integrity': 'intact',
                'message': 'Signature is valid and complies with Vietnamese digital signature standards'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Signature verification failed: {str(e)}',
                'integrity': 'invalid'
            }

    def sign_xml_invoice(self, xml_path):
        """
        Firma específicamente una factura XML
        Cumple con requisitos de facturación electrónica vietnamita
        """
        signer_info = {
            'name': 'Sistema de Facturación MiPyME',
            'email': 'facturacion@mipyme.vn',
            'tax_code': 'DEMO-TAX-CODE'
        }
        return self.sign_document(xml_path, signer_info)

    def get_pending_count(self):
        """Simula documentos pendientes de firma"""
        return 0
