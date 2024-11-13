from repositories.database import get_session
from sqlalchemy import create_engine, text


def fetch_address_details(address_value):
    query = text(
        """
        SELECT 
            a.id AS id_address,
            a.full_address,
            MAX(CASE WHEN score.quality_label = 'CargaCSV' THEN score.score END) AS CargaCSV,
            MAX(CASE WHEN score.quality_label = 'Google' THEN score.score END) AS Google_score,
            MAX(CASE WHEN score.quality_label = 'Nominatim' THEN score.score END) AS Nominatim_score,
            MAX(CASE WHEN api.name = 'Google' AND arv.attribute_name = 'latitud' THEN CAST(arv.attribute_value AS TEXT) END) AS Google_latitud,
            MAX(CASE WHEN api.name = 'Google' AND arv.attribute_name = 'longitude' THEN CAST(arv.attribute_value AS TEXT) END) AS Google_longitude,
            MAX(CASE WHEN api.name = 'Google' AND arv.attribute_name = 'address' THEN arv.attribute_value END) AS Google_address,
            MAX(CASE WHEN api.name = 'Nominatim' AND arv.attribute_name = 'latitud' THEN CAST(arv.attribute_value AS TEXT) END) AS Nominatim_latitud,
            MAX(CASE WHEN api.name = 'Nominatim' AND arv.attribute_name = 'longitude' THEN CAST(arv.attribute_value AS TEXT) END) AS Nominatim_longitude,
            MAX(CASE WHEN api.name = 'Nominatim' AND arv.attribute_name = 'address' THEN arv.attribute_value END) AS Nominatim_address
        FROM 
            address a
        LEFT JOIN 
            address_score score ON score.address_id = a.id
        LEFT JOIN 
            api_response_values arv ON arv.address_id = a.id
        LEFT JOIN 
            type_api_geocord api ON api.id = arv.type_api_id
        WHERE 
            a.full_address = :address_value
        GROUP BY 
            a.id, a.full_address;
    """
    )

    # Iniciar la sesión y ejecutar la consulta
    with get_session() as session:
        result = session.execute(query, {"address_value": address_value}).fetchone()

    # Si obtenemos un resultado, lo convertimos en un diccionario
    if result:
        result_dict = dict(result._asdict())  # Convierte el resultado a diccionario
        return result_dict
    else:
        return None
