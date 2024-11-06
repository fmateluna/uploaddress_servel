 
import psycopg2
from repositories.database import DB_CONFIG, load_query

from sqlalchemy.orm import Session

insert_input_request_query = load_query("insert_input_request.sql")

def insert_input_request(db: Session, request_data):
    db.execute(insert_input_request_query, request_data)
    db.commit()

def insert_into_input_request(address_id, input_type_id, attributes):
    connInsert = psycopg2.connect(**DB_CONFIG)
    cursorInsertInputRequest = connInsert.cursor()
    request_ids = []
    for attribute_name, attribute_value in attributes.items():
        cursorInsertInputRequest.execute(insert_input_request_query,
            (input_type_id, address_id, attribute_name, attribute_value),
        )
        request_ids.append(cursorInsertInputRequest.fetchone()[0])
    connInsert.commit()
    connInsert.close()
    return request_ids
