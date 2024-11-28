import psycopg2
from repositories.database import DB_CONFIG, load_query

# Cargar las consultas SQL
get_address_score_query = load_query("get_address_score.sql")
insert_address_score_query = load_query("insert_address_score.sql")
update_address_score_query = load_query("update_address_score.sql")


def insert_or_update_address_score(address_id, quality_label, score):
    # Conectar a la base de datos

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        # Verificar si existe una puntuación para el address_id y quality_label
        cursor.execute(get_address_score_query, (address_id, quality_label))
        result = cursor.fetchone()

        if result:
            # Actualizar el registro existente
            cursor.execute(
                update_address_score_query, (score, address_id, quality_label)
            )
            conn.commit()
            print(f"Puntaje Actualizado {address_id} {quality_label} {score}")
        else:
            # Insertar un nuevo registro de puntuación
            cursor.execute(
                insert_address_score_query, (address_id, quality_label, score)
            )
            conn.commit()
            # print(f"Nuevo Puntaje {address_id} {quality_label} {score}")

        # Cerrar la conexión
        cursor.close()
        conn.close()
    except psycopg2.DatabaseError as e:
        conn.rollback()
        print(f"Error al insertar o actualizar la dirección: {e}")
        return -1
    finally:
        cursor.close()
        conn.close()
