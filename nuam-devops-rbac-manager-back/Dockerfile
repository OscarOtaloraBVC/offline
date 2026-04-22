# Dockerfile
FROM python:alpine3.23

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ARG APP_USER=appuser
ARG APP_UID=1000
ARG APP_GID=1000

# Crear usuario y grupo
RUN addgroup -g ${APP_GID} ${APP_USER} \
    && adduser -u ${APP_UID} -G ${APP_USER} -D ${APP_USER}

# Instalar dependencias del sistema (incluyendo gcc para compilación)
RUN apk update \
    && apk add --no-cache \
        curl \
        ca-certificates \
        sqlite \
        openssl \
        bash \
        gcc \
        musl-dev \
        python3-dev \
    && update-ca-certificates \
    && curl -LO https://dl.k8s.io/release/v1.32.0/bin/linux/amd64/kubectl \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/kubectl \
    && apk cache clean

WORKDIR /opt/rbac-manager

# Copiar requirements.txt primero (mejor caché de Docker)
COPY requirements.txt /opt/rbac-manager/backend/requirements.txt

# Actualizar pip y usar versiones compatibles con Alpine
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        fastapi>=0.104.0 \
        "uvicorn[standard]>=0.24.0" \
        pydantic>=2.5.0 \
        PyYAML>=6.0.2 \
        httpx>=0.27.0 \
        pytest>=7.4.3

# Copiar el resto del código
COPY . /opt/rbac-manager/backend/

# Crear directorio de datos
RUN mkdir -p /opt/rbac-manager/data

# Configurar permisos
RUN chown -R ${APP_USER}:${APP_USER} /opt/rbac-manager

# Hacer ejecutables los scripts
RUN chmod +x /opt/rbac-manager/backend/bin/*.sh

USER ${APP_USER}

EXPOSE 8000

# Comando de inicio
CMD ["/opt/rbac-manager/backend/bin/run-backend-prod.sh"]