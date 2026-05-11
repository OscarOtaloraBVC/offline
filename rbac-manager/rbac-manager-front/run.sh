#!/bin/sh

echo "Initializing environment variables..."

# Cargar variables desde .env si existe
if [ -f .env ]; then
  export $(grep '^VITE_' .env | xargs)
fi

# Reemplazo de variables VITE_ en archivos estáticos
for var in $(env | grep '^VITE_' | cut -d= -f1); do
  value=$(printenv "$var")

  if [ ! -z "$value" ]; then
    echo "Replacing ENV occurrences $var"
    find /usr/share/nginx/html -type f -exec sed -i "s|$var|$value|g" {} \;
  fi
done

# Ejecutar scripts adicionales si existen
if [ -d "/docker-entrypoint.d/" ]; then
  for f in /docker-entrypoint.d/*; do
    case "$f" in
      *.envsh)
        [ -x "$f" ] && . "$f"
        ;;
      *.sh)
        [ -x "$f" ] && "$f"
        ;;
      *)
        echo "Ignoring $f"
        ;;
    esac
  done
fi

echo "Starting NGINX..."

exec nginx -g "daemon off;"