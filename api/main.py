import asyncio
import datetime
from fastapi import (
    FastAPI,
    APIRouter,
    File,
    HTTPException,
    Request,
    UploadFile,
    BackgroundTasks,
)
from pydantic import BaseModel
from typing import Any, Dict
import sys
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

import json
import pandas as pd
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories.address_repo import save_address
from repositories.address_score_repo import insert_or_update_address_score
from repositories.input_request_repo import insert_into_input_request
from repositories.input_type_repo import get_or_create_input_type
from repositories.origin_source_repo import (
    insert_origin_source,
    link_address_to_origin_source,
)
from services.local.local_service import build_address_components
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


# Endpoint para obtener información de la dirección
from typing import List


@router.get(
    "/report/{process_id}", response_model=List[dict]
)  # Usar List[dict] para aceptar múltiples registros
async def get_info(process_id: str):
    try:
        result = data_service.report(process_id)
        if result:
            return result  # Devolver la lista de resultados
        else:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron resultados para este process_id",
            )
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
        result = await data_service.generate_info_address(address, remote_ip, True)
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


# Endpoint para servir configUpload.html
@router.get("/geo/upload/report/{process_id}", response_class=HTMLResponse)
async def upload_config(process_id: str):
    html_file_path = FRONTEND_PATH / "report.html"

    # Leer el archivo HTML
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Inyectar el process_id en el HTML
    html_content = html_content.replace("{{process_id}}", process_id)

    return HTMLResponse(content=html_content, status_code=200)


# Endpoint para subir los archivos CSV y JSON
@router.post("/process_csv/")
async def process_csv_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    csv_file: UploadFile = File(...),
    json_file: UploadFile = File(...),
):
    ip = request.client.host  # Obtener la IP remota
    try:
        # Leer el archivo JSON
        json_content = await json_file.read()
        config = json.loads(json_content)

        # Leer el archivo CSV
        csv_content = await csv_file.read()

        fecha_hora_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        id_process = insert_origin_source(
            "Via Web : " + fecha_hora_actual + " desde " + ip
        )

        # Llamar a la función process_csv en segundo plano
        background_tasks.add_task(
            process_csv_from_web, config, csv_content.decode("utf-8"), ip, id_process
        )

        return {"message": f"Procesado con el ID: {str(id_process)}", "id": id_process}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al procesar los archivos: {str(e)}"
        )


# Función para generar un ID de proceso (puedes ajustarlo según lo que necesites)
def generate_process_id(ip):
    return f"process_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{ip}"


# Función para procesar el CSV en segundo plano
async def process_csv_from_web(config, csv_content, ip, origin_source_id):
    try:
        # Cargar los datos del CSV en un DataFrame
        from io import StringIO

        data = pd.read_csv(StringIO(csv_content))

        input_type = config["input_type"]
        input_attributes = config["input_atributes"]
        address_format = config["address_format"]

        data.columns = data.columns.str.lower()
        input_attributes = [col.lower() for col in input_attributes]

        data = data[input_attributes]

        input_type_id = get_or_create_input_type(input_type)

        for _, row in data.iterrows():
            address_data, score = build_address_components(address_format, row)

            address_data["api_flag"] = int(score) > 50

            print("[!] Calidad del dato :", score)

            # Generar columnas y valores dinámicamente en función de los datos disponibles en address_data
            columns = ", ".join(address_data.keys())
            values_placeholders = ", ".join(
                [f"%({key})s" for key in address_data.keys()]
            )

            # Añadir input_type_id manualmente a address_data
            address_data["input_type_id"] = input_type_id
            columns += ", input_type_id"
            values_placeholders += ", %(input_type_id)s"

            # Guardar en la tabla address
            address_id = save_address(columns, values_placeholders, address_data)

            if address_id > -1:
                link_address_to_origin_source(address_id, origin_source_id)
                print("[" + address_data["full_address"] + "]  is OK \n")
                insert_or_update_address_score(address_id, "CargaCSV", score)
                attributes = {
                    attr: row[attr] for attr in input_attributes if attr in row
                }
                insert_into_input_request(address_id, input_type_id, attributes)

            await data_service.generate_info_address(
                address_data["full_address"], ip, False
            )
            print("[" + address_data["full_address"] + "]  process api coords \n")
    except Exception as e:
        print("Error al procesar CSV:", e)


# Configurar la aplicación principal
app = FastAPI()
app.include_router(router)

# Montar la carpeta 'front' como recursos estáticos
app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")

# Iniciar el servidor si se ejecuta como un script
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
