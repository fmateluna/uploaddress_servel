import psycopg2
from psycopg2 import sql, DatabaseError
from repositories.database import DB_CONFIG, load_query
from datetime import date, datetime
from sqlalchemy.orm import Session
from .models import Address

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


class AddressRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_address_by_id(self, address_id: int):
        """Recupera una dirección de la tabla Address por su ID."""
        return self.db_session.query(Address).filter(Address.id == address_id).first()

    def get_address_by_full_address(self, full_address: str):
        """Recupera una dirección de la tabla Address por su full_address."""
        return (
            self.db_session.query(Address)
            .filter(Address.full_address == full_address)
            .first()
        )

    def update_geolocation(self, address_id: int, geolocation_data: dict):
        """Actualiza los datos de geolocalización de una dirección existente."""
        address = self.get_address_by_id(address_id)
        if address:
            address.normalized_address = geolocation_data.get("normalized_address")
            address.latitude = geolocation_data.get("latitude")
            address.longitude = geolocation_data.get("longitude")
            address.last_update = datetime.now()
            self.db_session.commit()
            return True
        return False
