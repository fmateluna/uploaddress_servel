 
# Usa una imagen de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos necesarios
COPY . /app

# Instala las dependencias
RUN pip install -r requirements.txt

# Comando de ejecución por defecto
CMD ["python", "entrypoints/main.py", "config.json"]
