import os
import sys
from fastapi import FastAPI

from fastapi import APIRouter, HTTPException

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.remote.data_service import DataService


router = APIRouter()


@router.get("/geolocation/")
async def get_geolocation(api_name: str, address: str):
    try:
        data_service = DataService()
        result = data_service.process_address(api_name, address)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error en la solicitud a la API externa"
        )


app = FastAPI()
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
