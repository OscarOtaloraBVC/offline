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

# Copiar build
COPY --from=builder /usr/src/app/build /usr/share/nginx/html

# Configurar Nginx para SPA y API proxy
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass http://localhost:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]