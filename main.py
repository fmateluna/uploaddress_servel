import argparse
import os
from services.data_service import process_csv

def main(config_path):
    # Obtener la ruta absoluta del archivo de configuración
    file_path = os.path.abspath(config_path)
    
    # Verificar si el archivo existe
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No se pudo encontrar el archivo de configuración: {file_path}")

    # Llamar a la función process_csv con la ruta del archivo
    process_csv(file_path)

if __name__ == "__main__":    
    parser = argparse.ArgumentParser(
        description="Carga datos de dirección desde un CSV usando configuración JSON."
    )
    parser.add_argument(
        "-def", "--definition", required=True, help="Ruta al archivo de definición JSON"
    )    
    
    args = parser.parse_args()
    main(args.definition)  # Asegúrate de pasar 'args.definition'
