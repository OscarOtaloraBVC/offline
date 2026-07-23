# frontend/Dockerfile
# Build stage
ARG node_version=20
FROM docker.io/node:${node_version}-alpine AS builder
WORKDIR /usr/src/app

# Copiar package files
COPY package*.json ./
RUN npm install --no-audit

# Copiar código fuente y construir
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Instalar envsubst para sustituir variables de entorno
RUN apk add --no-cache gettext

# Copiar build
COPY --from=builder /usr/src/app/build /usr/share/nginx/html

# Copiar template de configuración de nginx
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template

# Crear script de entrada personalizado
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'set -e' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo '# Configurar variables por defecto' >> /docker-entrypoint.sh && \
    echo 'export BACKEND_URL=${BACKEND_URL:-http://vault-unseal-backend.vault.svc.cluster.local:8000}' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo 'echo "🚀 Starting Vault Unseal Frontend"' >> /docker-entrypoint.sh && \
    echo 'echo "📡 Backend URL: $BACKEND_URL"' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo '# Sustituir variables en el template' >> /docker-entrypoint.sh && \
    echo 'envsubst '\''$BACKEND_URL'\'' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo '# Iniciar nginx' >> /docker-entrypoint.sh && \
    echo 'exec nginx -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]