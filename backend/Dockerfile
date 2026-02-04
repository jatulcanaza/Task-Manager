FROM python:3.12-slim
# Imagen base ligera de Python 3.12 (Debian slim) para reducir tamaño del contenedor

WORKDIR /app
# Define el directorio de trabajo dentro del contenedor (donde se ejecutarán comandos y se copiarán archivos)

COPY requirements.txt .
# Copia el archivo de dependencias a /app (se copia primero para aprovechar cache de Docker)

RUN pip install --no-cache-dir -r requirements.txt
# Instala dependencias Python indicadas en requirements.txt
# --no-cache-dir evita guardar caché de pip, reduciendo el tamaño final de la imagen

COPY app ./app
# Copia el código fuente de la aplicación al contenedor (carpeta app -> /app/app)

EXPOSE 8000
# Documenta que la aplicación expone el puerto 8000 (no publica el puerto por sí solo)

CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]
# Comando por defecto al iniciar el contenedor:
# - levanta Uvicorn apuntando a la instancia 'app' definida en app/main.py
# - host 0.0.0.0 para aceptar conexiones desde fuera del contenedor
# - puerto 8000 como puerto de escucha
