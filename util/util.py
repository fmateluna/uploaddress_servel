import os
import csv
from difflib import get_close_matches


# Diccionario básico para unidades, decenas y centenas
numeros = {
    "cero": 0, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
    "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciséis": 16, "diecisiete": 17,
    "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiuno": 21, "veintidós": 22, "veintitrés": 23, "veinticuatro": 24,
    "veinticinco": 25, "veintiséis": 26, "veintisiete": 27, "veintiocho": 28, "veintinueve": 29,
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90,
    "cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300, "cuatrocientos": 400, "quinientos": 500,
    "seiscientos": 600, "setecientos": 700, "ochocientos": 800, "novecientos": 900,
    "mil": 1000, "millón": 1000000, "millones": 1000000,
}

# Función para corregir palabras mal escritas
def corregir_palabra(palabra, opciones):
    similares = get_close_matches(palabra, opciones, n=1, cutoff=0.8)
    return similares[0] if similares else palabra

# Función para convertir texto a número
def texto_a_numero(texto):
    texto = texto.lower()  # Convertir a minúsculas
    palabras = texto.split()
    total = 0
    parcial = 0

    for palabra in palabras:
        palabra_corregida = corregir_palabra(palabra, numeros.keys())
        if palabra_corregida in numeros:
            valor = numeros[palabra_corregida]
            if valor >= 1000:
                parcial = max(1, parcial) * valor
                total += parcial
                parcial = 0
            elif valor >= 100:
                parcial *= valor
            else:
                parcial += valor
        else:
            continue

    return total + parcial


def traduce_direccion(direccion: str, abreviaciones_path: str, nombres_path: str) -> str:
    """
    Traduce una dirección usando abreviaciones y nombres definidos en archivos CSV.

    :param direccion: La dirección original como cadena.
    :param abreviaciones_path: Ruta al archivo CSV que contiene las abreviaciones.
    :param nombres_path: Ruta al archivo CSV que contiene las abreviaciones de nombres.
    :return: Dirección traducida como cadena.
    """
    try:
        # Cargar las abreviaciones generales desde el archivo CSV
        with open(abreviaciones_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            reemplazos = {row["a"].lower(): row["b"] for row in reader}

        # Cargar las abreviaciones de nombres desde el archivo CSV
        with open(nombres_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            nombres_reemplazos = {row["a"]: row["b"] for row in reader}

        # Eliminar los puntos de las abreviaciones antes de hacer la traducción
        direccion = direccion.replace(".", "")  # Eliminar puntos

        # Procesar la dirección palabra por palabra
        palabras = direccion.split()
        traducida = []
        for palabra in palabras:
            if palabra.istitle():  # Si la palabra comienza con mayúscula, buscar en nombres
                traducida.append(nombres_reemplazos.get(palabra, palabra))
            else:  # Si no, buscar en abreviaciones generales
                traducida.append(reemplazos.get(palabra.lower(), palabra))

        # Convertir palabras numéricas a números
        resultado = " ".join(
            str(texto_a_numero(p)) if p.lower() in numeros else p for p in traducida
        )

        return resultado
    except FileNotFoundError as e:
        return f"Error: No se encontró el archivo CSV: {e.filename}"
    except Exception as e:
        return f"Error al procesar la dirección: {str(e)}"


# Ejemplo de uso
base_path = os.path.join(os.path.dirname(__file__), "def")
abreviaciones_csv = os.path.join(base_path, "traducciones.csv")
nombres_csv = os.path.join(base_path, "nombres.csv")

# Dirección de ejemplo
direccion = "Fdo Tierras Blancas Zapallar Region De Valparaiso Chile"
resultado = traduce_direccion(direccion, abreviaciones_csv, nombres_csv)

# Imprimir el resultado
print(f"Dirección original: {direccion}")
print(f"Dirección traducida: {resultado}")
