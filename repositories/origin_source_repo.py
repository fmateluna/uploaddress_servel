import psycopg2
from datetime import datetime
from repositories.database import DB_CONFIG, load_query

# Cargar las consultas SQL
insert_origin_source_query = load_query("insert_origin_source.sql")
insert_address_origin_source_query = load_query("insert_address_origin_source.sql")


def insert_origin_source(file_name):
    """Inserta un nuevo registro en la tabla origin_source."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    load_time = datetime.now()

    # Insertar en origin_source
    cursor.execute(insert_origin_source_query, (file_name, load_time))
    origin_source_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return origin_source_id


def link_address_to_origin_source(address_id, origin_source_id):
    """Inserta un nuevo registro en la tabla address_origin_source."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Insertar en address_origin_source
    cursor.execute(insert_address_origin_source_query, (address_id, origin_source_id))

    conn.commit()
    cursor.close()
    conn.close()
