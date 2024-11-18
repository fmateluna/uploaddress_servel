from repositories.database import get_session
from sqlalchemy import create_engine, text

def fetch_report_by_process_id(process_id):
    query = text(
        """
        
        WITH
        address_scores AS (
            SELECT 
                address_id,
                MAX(CASE WHEN quality_label = 'CargaCSV' THEN score END) AS CargaCSV,
                MAX(CASE WHEN quality_label = 'Google' THEN score END) AS Google_score,
                MAX(CASE WHEN quality_label = 'Nominatim' THEN score END) AS Nominatim_score
            FROM address_score
            GROUP BY address_id
        ),
        api_google AS (
            SELECT 
                arv.address_id,
                MAX(CASE WHEN arv.attribute_name = 'latitud' THEN arv.attribute_value || '°' END) AS Google_latitud,
                MAX(CASE WHEN arv.attribute_name = 'longitude' THEN arv.attribute_value || '°' END) AS Google_longitude,
                MAX(CASE WHEN arv.attribute_name = 'address' THEN arv.attribute_value END) AS Google_address
            FROM api_response_values arv
            WHERE arv.type_api_id = (SELECT id FROM type_api_geocord WHERE name = 'Google')
            GROUP BY arv.address_id
        ),
        api_nominatim AS (
            SELECT 
                arv.address_id,
                MAX(CASE WHEN arv.attribute_name = 'latitud' THEN arv.attribute_value || '°' END) AS Nominatim_latitud,
                MAX(CASE WHEN arv.attribute_name = 'longitude' THEN arv.attribute_value || '°' END) AS Nominatim_longitude,
                MAX(CASE WHEN arv.attribute_name = 'address' THEN arv.attribute_value END) AS Nominatim_address
            FROM api_response_values arv
            WHERE arv.type_api_id = (SELECT id FROM type_api_geocord WHERE name = 'Nominatim')
            GROUP BY arv.address_id
        ),
        input_requests AS (
            SELECT 
                address_id,
                MAX(CASE WHEN attribute_name = 'run' THEN attribute_value END) AS run,
                MAX(CASE WHEN attribute_name = 'calle' THEN attribute_value END) AS calle,
                MAX(CASE WHEN attribute_name = 'numero' THEN attribute_value END) AS numero,
                MAX(CASE WHEN attribute_name = 'resto' THEN attribute_value END) AS resto,
                MAX(CASE WHEN attribute_name = 'comuna_iso' THEN attribute_value END) AS comuna_iso,
                MAX(CASE WHEN attribute_name = 'glosacomun' THEN attribute_value END) AS glosacomun,
                MAX(CASE WHEN attribute_name = 'glosa_regi' THEN attribute_value END) AS glosa_regi
            FROM input_request
            GROUP BY address_id
        )
        SELECT 
            a.id AS id_address,
            a.full_address,
            ir.run,
            ir.calle,
            ir.numero,
            ir.resto,
            ir.comuna_iso,
            ir.glosacomun,
            ir.glosa_regi,
            sc.CargaCSV,
            sc.Google_score,
            sc.Nominatim_score,
            g.Google_latitud,
            g.Google_longitude,
            g.Google_address,
            n.Nominatim_latitud,
            n.Nominatim_longitude,
            n.Nominatim_address
        FROM address a
        LEFT JOIN address_scores sc ON sc.address_id = a.id
        LEFT JOIN api_google g ON g.address_id = a.id
        LEFT JOIN api_nominatim n ON n.address_id = a.id
        LEFT JOIN input_requests ir ON ir.address_id = a.id
        WHERE sc.CargaCSV IS NOT NULL
        AND EXISTS (
            SELECT 1
            FROM address_origin_source aos
            WHERE aos.origin_source_id = :process_id
                AND aos.address_id = a.id
        )
        ORDER BY CAST(ir.run AS INTEGER);

        """
    )

    # Iniciar la sesión y ejecutar la consulta
    with get_session() as session:
        result = session.execute(query, {"process_id": process_id}).fetchall()  # fetchall() para obtener todos los resultados

    # Si obtenemos resultados, los convertimos en diccionarios
    if result:
        result_list = [dict(row._asdict()) for row in result]  # Convierte cada fila de resultado en un diccionario
        return result_list
    else:
        return None


def fetch_address_details(address_value):
    query = text(
        """
        SELECT 
            a.id AS id_address,
            a.full_address,
            -- Columnas de input_request pivotadas
            MAX(CASE WHEN ir.attribute_name = 'id' THEN ir.attribute_value END) AS input_id,
            MAX(CASE WHEN ir.attribute_name = 'calle' THEN ir.attribute_value END) AS calle,
            MAX(CASE WHEN ir.attribute_name = 'numero' THEN ir.attribute_value END) AS numero,
            MAX(CASE WHEN ir.attribute_name = 'resto' THEN ir.attribute_value END) AS resto,
            MAX(CASE WHEN ir.attribute_name = 'region' THEN ir.attribute_value END) AS region,
            MAX(CASE WHEN ir.attribute_name = 'comuna' THEN ir.attribute_value END) AS comuna,
            MAX(CASE WHEN ir.attribute_name = 'region2' THEN ir.attribute_value END) AS region2,
            MAX(CASE WHEN ir.attribute_name = 'comuna2' THEN ir.attribute_value END) AS comuna2,
            MAX(CASE WHEN ir.attribute_name = 'text_reg' THEN ir.attribute_value END) AS text_reg,
            MAX(CASE WHEN ir.attribute_name = 'text_com' THEN ir.attribute_value END) AS text_com,
            MAX(CASE WHEN ir.attribute_name = 'localidad' THEN ir.attribute_value END) AS localidad,
            MAX(CASE WHEN ir.attribute_name = 'direccion' THEN ir.attribute_value END) AS direccion,
            -- Columnas de address_score pivotadas
            MAX(CASE WHEN score.quality_label = 'CargaCSV' THEN score.score END) AS CargaCSV,
            MAX(CASE WHEN score.quality_label = 'Google' THEN score.score END) AS Google_score,
            MAX(CASE WHEN score.quality_label = 'Nominatim' THEN score.score END) AS Nominatim_score,
            -- Columnas de api_response_values para Google
            MAX(CASE WHEN api.name = 'Google' AND arv.attribute_name = 'latitud' THEN CAST(arv.attribute_value AS TEXT)||'°' END) AS Google_latitud,
            MAX(CASE WHEN api.name = 'Google' AND arv.attribute_name = 'longitude' THEN CAST(arv.attribute_value AS TEXT)||'°'END) AS Google_longitude,
            MAX(CASE WHEN api.name = 'Google' AND arv.attribute_name = 'address' THEN arv.attribute_value END) AS Google_address,
            -- Columnas de api_response_values para Nominatim
            MAX(CASE WHEN api.name = 'Nominatim' AND arv.attribute_name = 'latitud' THEN CAST(arv.attribute_value AS TEXT)||'°' END) AS Nominatim_latitud,
            MAX(CASE WHEN api.name = 'Nominatim' AND arv.attribute_name = 'longitude' THEN CAST(arv.attribute_value AS TEXT)||'°' END) AS Nominatim_longitude,
            MAX(CASE WHEN api.name = 'Nominatim' AND arv.attribute_name = 'address' THEN arv.attribute_value END) AS Nominatim_address
        FROM 
            address a
        LEFT JOIN 
            address_score score ON score.address_id = a.id
        LEFT JOIN 
            api_response_values arv ON arv.address_id = a.id
        LEFT JOIN 
            type_api_geocord api ON api.id = arv.type_api_id
        LEFT JOIN 
            input_request ir ON ir.address_id = a.id
        WHERE 
            score.score IS NOT NULL  
            and a.full_address = :address_value
        GROUP BY 
            a.id, a.full_address
        ORDER BY 
            a.id;
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
