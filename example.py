# Ejemplo para crear una factura electrónica
import requests
import json

# Datos de la factura
invoice_data = {
    "seller_info": {
        "name": "Mi Empresa S.A.",
        "tax_code": "0123456789",
        "address": "123 Nguyen Hue St, District 1, Ho Chi Minh City",
        "phone": "+84 28 1234 5678",
        "email": "contacto@miempresa.vn"
    },
    "buyer_info": {
        "name": "Cliente Ejemplo Ltd.",
        "tax_code": "9876543210",
        "address": "456 Le Loi St, District 3, Ho Chi Minh City",
        "phone": "+84 28 9876 5432",
        "email": "cliente@ejemplo.vn"
    },
    "items": [
        {
            "description": "Servicio de Consultoría IT",
            "quantity": 10,
            "unit_price": 500000
        },
        {
            "description": "Licencia de Software",
            "quantity": 1,
            "unit_price": 2000000
        }
    ],
    "payment_method": "Bank Transfer",
    "vat_rate": 0.10,
    "currency": "VND",
    "notes": "Pago a 30 días"
}

# Crear factura
response = requests.post(
    'http://localhost:5000/invoices/create',
    json=invoice_data,
    headers={'Content-Type': 'application/json'}
)

result = response.json()
print(f"Factura creada: {result['invoice_number']}")
print(f"Total: {result['total']} VND")
print(f"PDF generado: {result['pdf_path']}")
print(f"XML generado: {result['xml_path']}")
