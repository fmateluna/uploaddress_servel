 
# Proyecto de Geolocalización con PostgreSQL y FastAPI

Este proyecto procesa un CSV con direcciones, lo estructura y guarda en PostgreSQL usando SQLAlchemy. La estructura es hexagonal y separa lógica, repositorios y consultas SQL.

## Estructura del Proyecto

- **core/**: Modelos de base de datos.
- **repositories/**: Repositorios y consultas SQL.
- **services/**: Lógica para procesamiento de datos.
- **entrypoints/**: Punto de entrada principal.

## Instrucciones

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
