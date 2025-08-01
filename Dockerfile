# =================================================================
# DOCKERFILE PARA FAMILIA GASTRO
# =================================================================
# Imagen base de Python optimizada
FROM python:3.11-slim

# Configurar variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Crear usuario no root para seguridad
RUN groupadd -r familagastro && useradd -r -g familagastro familagastro

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    # Dependencias para PostgreSQL
    libpq-dev \
    # Dependencias para SQL Server
    curl \
    apt-transport-https \
    gnupg \
    # Dependencias para compilación
    gcc \
    g++ \
    # Dependencias para imágenes
    libjpeg-dev \
    libpng-dev \
    # Utilidades
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Instalar Microsoft ODBC Driver para SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Instalar dependencias adicionales para producción
RUN pip install --no-cache-dir \
    gunicorn==21.2.0 \
    whitenoise==6.6.0 \
    redis==5.0.1 \
    psycopg2-binary==2.9.9

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p logs staticfiles media/platos \
    && chown -R familagastro:familagastro /app

# Cambiar a usuario no root
USER familagastro

# Recopilar archivos estáticos
RUN python manage.py collectstatic --noinput --settings=mysitio.settings

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "mysitio.wsgi:application"]