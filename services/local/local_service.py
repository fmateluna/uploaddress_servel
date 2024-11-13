import pandas as pd
from repositories.address_score_repo import insert_or_update_address_score
from repositories.input_type_repo import get_or_create_input_type
from repositories.address_repo import save_address
from repositories.input_request_repo import (
    insert_into_input_request,
)

from repositories.models import InputType
import json

from repositories.origin_source_repo import (
    insert_origin_source,
    link_address_to_origin_source,
)


# build_address_components = Construir los componentes de dirección
# según la configuración JSON ,tambien da un porcentaje de aceptacion
# del atributo o score
def build_address_components(address_format, row):
    address_data = {}
    total_expected_attributes = 0  # Contador para el total de atributos esperados
    valid_attributes_count = 0  # Contador para los atributos válidos encontrados

    for column_name, components in address_format.items():
        # Usamos una lista para preservar el orden de los componentes,
        # importante para generar direcciones unicas por dato
        component_parts = []
        seen_values = set()  # Usamos un conjunto para evitar duplicados
        total_expected_attributes += len(
            components
        )  # Aumenta el total de atributos esperados

        for part in components:
            # Verifica si es un string literal, por ejemplo, 'Chile'
            if part.startswith("'") and part.endswith("'"):
                component_value = part.strip("'")
            else:
                key = str(part).lower()
                component_value = str(row.get(key, "")).strip()

            if component_value.replace(".", "", 1).isdigit():
                float_value = float(component_value)
                if float_value.is_integer():
                    component_value = str(int(float_value))

            # Ignora valores vacíos o nulos (NULL, NaN)
            if (
                component_value.lower() not in {"null", "nan", "s/n", ""}
                and component_value not in seen_values
            ):
                component_value = component_value.title()
                component_parts.append(component_value)
                seen_values.add(component_value)
                valid_attributes_count += (
                    1  # Incrementa el contador de atributos válidos
                )

        # Une los componentes únicos en el orden original y asigna al diccionario
        address_data[column_name] = " ".join(component_parts)

    # Calcula el porcentaje de atributos válidos
    acceptance_score = (
        (valid_attributes_count / total_expected_attributes) * 100
        if total_expected_attributes > 0
        else 0
    )

    return address_data, acceptance_score


def load_config(config_path):
    with open(config_path, "r") as file:
        config = json.load(file)
    return config


def process_csv(config_path):
    config = load_config(config_path)

    input_type = config["input_type"]
    input_attributes = config["input_atributes"]
    address_format = config["address_format"]
    csv_path = config["path_input"]

    origin_source_id = insert_origin_source(csv_path)

    data = pd.read_csv(csv_path)
    data.columns = data.columns.str.lower()
    input_attributes = [col.lower() for col in input_attributes]

    data.columns = data.columns.str.lower()
    data = data[input_attributes]

    input_type_id = get_or_create_input_type(input_type)

    for _, row in data.iterrows():
        address_data, score = build_address_components(address_format, row)

        print("[!] Calidad del dato :", score)

        # Generar columnas y valores dinámicamente en función de los datos disponibles en address_data
        # 1 - Nombres de columnas (ej., full_address, house_number)
        columns = ", ".join(address_data.keys())

        # 2 - Placeholder para valores
        values_placeholders = ", ".join([f"%({key})s" for key in address_data.keys()])

        # Añadir input_type_id manualmente a address_data y a los nombres de columnas y placeholders
        address_data["input_type_id"] = input_type_id
        columns += ", input_type_id"
        values_placeholders += ", %(input_type_id)s"
        try:
            # Insertar en la tabla address solo los campos que están presentes en address_data
            address_id = save_address(columns, values_placeholders, address_data)

            if address_id > -1:
                link_address_to_origin_source(address_id, origin_source_id)
                print("[" + address_data["full_address"] + "]  is OK \n")

                insert_or_update_address_score(address_id, "CargaCSV", score)

                # Insertar en input_request los atributos de la fila actual
                attributes = {
                    attr: row[attr] for attr in input_attributes if attr in row
                }
                insert_into_input_request(address_id, input_type_id, attributes)

                # Acá invocar a APIS para a partir de address_id enviar consultas a API
            else:
                print("[" + address_data["full_address"] + "]  is OK \n")

        except Exception as e:
            print("Error:", e)
