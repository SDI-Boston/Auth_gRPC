FROM python:3.9-slim

# Instala las dependencias del sistema necesarias
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de la aplicación
COPY . .

# Instala las dependencias de la aplicación manualmente
RUN pip install --no-cache-dir \
    blinker==1.7.0 \
    click==8.1.7 \
    colorama==0.4.6 \
    Flask==3.0.3 \
    greenlet==3.0.3 \
    grpcio==1.62.1 \
    grpcio-tools==1.62.1 \
    itsdangerous==2.1.2 \
    Jinja2==3.1.3 \
    MarkupSafe==2.1.5 \
    mysqlclient==2.2.4 \
    protobuf==4.25.3 \
    PyJWT==2.8.0 \
    setuptools==69.5.1 \
    SQLAlchemy==2.0.29 \
    typing_extensions==4.11.0 \
    Werkzeug==3.0.2

# Expone el puerto 50051
EXPOSE 50051

# Comando para ejecutar la aplicación
CMD ["python", "server.py"]
