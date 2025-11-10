Instalación

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Paso 1: Clonar el Repositorio


```
git clone https://github.com/tu-usuario/sistema-gestion-mipyme.git
cd sistema-gestion-mipyme
```

### Paso 2: Crear Entorno Virtual (Recomendado)

**En Windows:**

```
python -m venv venv
venv\Scripts\activate

```

**En Linux/Mac:**

```
python3 -m venv venv
source venv/bin/activate

```

### Paso 3: Instalar Dependencias


```
pip install -r requirements.txt

```

### Paso 4: Inicializar Base de Datos (Opcional)

Si deseas usar la base de datos SQLAlchemy:


```
python models.py

```

## ▶️ Ejecución

### Modo Desarrollo


```
python app.py

```

La aplicación estará disponible en: [**http://localhost:5000**](http://localhost:5000)
