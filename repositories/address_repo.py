from typing import LiteralString
import psycopg2
from psycopg2 import sql, DatabaseError
from repositories.database import DB_CONFIG, load_query
from datetime import date

# Cargar las consultas SQL para insertar y verificar
insert_address_query = load_query("insert_address.sql")
update_last_update_query = load_query("update_address.sql")
check_existing_query = load_query("find_full_address.sql")


def save_address(columns: str, values_placeholders: str, address_data: dict):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Verificar si ya existe un registro con el mismo full_address
        cursor.execute(check_existing_query, (address_data["full_address"],))
        existing_record = cursor.fetchone()

        if existing_record:
            # Si el registro existe, actualizamos el campo last_update
            address_id = existing_record[0]  # Recuperamos el ID del registro existente
            cursor.execute(update_last_update_query, (address_id,))
            print(
                f"Registro existente encontrado. Se actualiza 'last_update' para ID: {address_id}."
            )
        else:
            # Si el registro no existe, insertamos un nuevo registro
            query = sql.SQL(insert_address_query).format(
                columns=sql.SQL(columns),
                values_placeholders=sql.SQL(values_placeholders),
            )
            cursor.execute(query, address_data)
            address_id = cursor.fetchone()[0]
            print(f"Nuevo registro insertado con ID: {address_id}.")

        conn.commit()
        return address_id

    except DatabaseError as e:
        conn.rollback()
        print(f"Error al insertar o actualizar la dirección: {e}")
        return -1
    finally:
        cursor.close()
        conn.close()
