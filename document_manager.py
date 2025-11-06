import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import hashlib

class DocumentManager:
    """
    Gestión documental centralizada para MiPyMEs
    Funcionalidades: almacenamiento, búsqueda, categorización y control de versiones
    """
    
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.metadata_file = os.path.join(upload_folder, 'metadata.json')
        self.allowed_extensions = {
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 
            'txt', 'jpg', 'jpeg', 'png', 'zip'
        }
        self._load_metadata()
    
    def _load_metadata(self):
        """Carga metadatos de documentos"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
        else:
            self.documents = {}
            self._save_metadata()
    
    def _save_metadata(self):
        """Guarda metadatos de documentos"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, indent=2, ensure_ascii=False)
    
    def _allowed_file(self, filename):
        """Verifica si el archivo tiene extensión permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _calculate_hash(self, file_path):
        """Calcula hash SHA256 del archivo para integridad"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def upload_document(self, file, metadata):
        """Sube un documento con metadatos"""
        if not file or file.filename == '':
            return {'error': 'No file selected'}
        
        if not self._allowed_file(file.filename):
            return {'error': 'File type not allowed'}
        
        # Generar ID único
        doc_id = str(uuid.uuid4())
        
        # Guardar archivo con nombre seguro
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        new_filename = f"{doc_id}.{file_extension}"
        file_path = os.path.join(self.upload_folder, new_filename)
        
        file.save(file_path)
        
        # Calcular hash para integridad
        file_hash = self._calculate_hash(file_path)
        
        # Guardar metadatos
        self.documents[doc_id] = {
            'id': doc_id,
            'original_filename': original_filename,
            'stored_filename': new_filename,
            'title': metadata.get('title', original_filename),
            'category': metadata.get('category', 'general'),
            'description': metadata.get('description', ''),
            'tags': metadata.get('tags', []),
            'upload_date': datetime.now().isoformat(),
            'file_size': os.path.getsize(file_path),
            'file_hash': file_hash,
            'file_extension': file_extension,
            'version': 1
        }
        
        self._save_metadata()
        
        return {
            'success': True,
            'document_id': doc_id,
            'message': 'Document uploaded successfully'
        }
    
    def get_document(self, doc_id):
        """Obtiene información de un documento"""
        return self.documents.get(doc_id)
    
    def get_document_path(self, doc_id):
        """Obtiene la ruta física del documento"""
        doc = self.documents.get(doc_id)
        if doc:
            return os.path.join(self.upload_folder, doc['stored_filename'])
        return None
    
    def list_all_documents(self):
        """Lista todos los documentos"""
        return list(self.documents.values())
    
    def search_documents(self, query, category=''):
        """Busca documentos por texto o categoría"""
        results = []
        query_lower = query.lower()
        
        for doc in self.documents.values():
            match = False
            
            # Buscar en título, descripción y tags
            if (query_lower in doc['title'].lower() or
                query_lower in doc['description'].lower() or
                any(query_lower in tag.lower() for tag in doc['tags'])):
                match = True
            
            # Filtrar por categoría si se especifica
            if category and doc['category'] != category:
                match = False
            
            if match:
                results.append(doc)
        
        return results
    
    def delete_document(self, doc_id):
        """Elimina un documento"""
        doc = self.documents.get(doc_id)
        if doc:
            file_path = self.get_document_path(doc_id)
            if os.path.exists(file_path):
                os.remove(file_path)
            del self.documents[doc_id]
            self._save_metadata()
            return {'success': True}
        return {'error': 'Document not found'}
    
    def get_document_count(self):
        """Obtiene el total de documentos"""
        return len(self.documents)
