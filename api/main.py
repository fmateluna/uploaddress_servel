from fastapi import FastAPI, APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Any, Dict
import sys
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.remote.data_service import DataService

# Crear el router y la instancia de DataService
router = APIRouter()
data_service = DataService()

# Usar pathlib para obtener una ruta relativa
FRONTEND_PATH = Path(__file__).resolve().parent / "../front"


# Modelo para la respuesta de error
class ErrorResponse(BaseModel):
    detail: str
    code: int = 500


# Endpoint para obtener geolocalización
@router.get("/geolocation/", response_model=dict)
async def get_geolocation(api_name: str, address: str):
    try:
        # Procesa la dirección
        result = await data_service.process_address(api_name, address)
        # Convierte el resultado a dict excluyendo valores None
        return {k: v for k, v in result.items() if v is not None}
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=ErrorResponse(detail=str(e), code=400).dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail="Error en la solicitud a la API externa: " + str(e), code=500
            ).dict(),
        )


# Endpoint para obtener información de la dirección
@router.get("/info/", response_model=dict)
async def get_info(address: str):
    try:
        result = data_service.get_all_info_from_address(address)
        return {k: v for k, v in result.items() if v is not None}
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=ErrorResponse(detail=str(e), code=400).dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail="Error al obtener la información: " + str(e), code=500
            ).dict(),
        )


# Endpoint para crear información de la dirección
@router.get("/create/", response_model=dict)
async def create_info(request: Request, address: str):
    try:
        remote_ip = request.client.host
        result = await data_service.generate_info_address(address, remote_ip)
        return {k: v for k, v in result.items() if v is not None}
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=ErrorResponse(detail=str(e), code=400).dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail="Error al crear la data: " + str(e), code=500
            ).dict(),
        )


# Endpoint para servir configUpload.html
@router.get("/geo/upload/config", response_class=HTMLResponse)
async def upload_config():
    html_file_path = FRONTEND_PATH / "configUpload.html"
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)


# Configurar la aplicación principal
app = FastAPI()
app.include_router(router)

# Montar la carpeta 'front' como recursos estáticos
app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")

# Iniciar el servidor si se ejecuta como un script
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)