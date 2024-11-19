import json
import pandas as pd
import psycopg2
from psycopg2 import sql
import sys
import argparse

from repositories.database import DB_CONFIG, load_query

create_input_type_query = load_query("insert_input_type.sql")
get_input_type_query = load_query("get_input_type.sql")


def get_or_create_input_type(input_type_name):
    conn_insert = psycopg2.connect(**DB_CONFIG)
    cursor_insert_input_type = conn_insert.cursor()
    cursor_insert_input_type.execute(get_input_type_query, (input_type_name,))
    result = cursor_insert_input_type.fetchone()
    if result:
        conn_insert.close()
        return result[0]
    else:
        cursor_insert_input_type.execute(create_input_type_query, (input_type_name,))
        conn_insert.commit()
        print("Se ha creado un nuevo typo de input " + input_type_name + "\n")
        return cursor_insert_input_type.fetchone()[0]
