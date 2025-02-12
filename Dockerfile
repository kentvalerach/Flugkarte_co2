# Usa una imagen oficial de Python
FROM python:3.10

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia todos los archivos del proyecto al contenedor
COPY . .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 8080 para Railway
EXPOSE 8080

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]
