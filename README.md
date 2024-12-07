 
# Proyecto de Geolocalización con PostgreSQL y FastAPI

Este proyecto procesa un CSV con direcciones, lo estructura y guarda en PostgreSQL usando SQLAlchemy. La estructura es hexagonal y separa lógica, repositorios y consultas SQL.

## URL DE EJEMPLO

http://localhost:8000/geolocation/?api_name=google&address=VALPARA%C3%8DSO%20VI%C3%91A%20DEL%20MAR%201%20NORTE%204468,%20VI%C3%91A%20DEL%20MAR,%20VALPARA%C3%8DSO,%20Chile

## Estructura del Proyecto

- **core/**: Modelos de base de datos.
- **repositories/**: Repositorios y consultas SQL.
- **services/**: Lógica para procesamiento de datos.
- **entrypoints/**: Punto de entrada principal.

## Instrucciones

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt


Para subir el servidor :

 uvicorn api.main:app --host 0.0.0.0 --port 8000
