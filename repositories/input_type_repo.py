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
    connInsert = psycopg2.connect(**DB_CONFIG)
    cursorInsertInputType = connInsert.cursor()
    cursorInsertInputType.execute(get_input_type_query, (input_type_name,))
    result = cursorInsertInputType.fetchone()
    if result:
        connInsert.close()
        return result[0]
    else:
        cursorInsertInputType.execute(create_input_type_query, (input_type_name,))
        connInsert.commit()
        print("Se ha creado un nuevo typo de input " + input_type_name + "\n")
        return cursorInsertInputType.fetchone()[0]
