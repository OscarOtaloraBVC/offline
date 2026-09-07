#!/bin/bash
# Script simplificado para copiar archivos y ejecutar importación
# Uso: ./import_realm_k8s_simple.sh /ruta/local/al/reino

if [ $# -eq 0 ]; then
    echo "Uso: $0 <ruta_del_reino>"
    exit 1
fi

LOCAL_PATH="$1"
REALM_NAME=$(basename "$LOCAL_PATH")

echo "📂 Copiando archivos de $REALM_NAME al pod..."

# Crear directorio
kubectl exec -it -n keycloak keycloak-nuam-0 -- mkdir -p /tmp/keycloak-import/$REALM_NAME

# Copiar cada archivo JSON
for file in "$LOCAL_PATH"/*.json; do
    filename=$(basename "$file")
    echo "  Copiando $filename..."
    cat "$file" | kubectl exec -i -n keycloak keycloak-nuam-0 -- tee /tmp/keycloak-import/$REALM_NAME/$filename > /dev/null
done

echo "✅ Archivos copiados. Ahora ejecuta dentro del pod:"
echo ""
echo "kubectl exec -it -n keycloak keycloak-nuam-0 -- /bin/bash"
echo "cd /opt/keycloak/bin"
echo "./kcadm.sh config credentials --server http://localhost:8081 --realm master --user ootalora --password CFT6yhn234"
echo ""
echo "# Para importar el reino:"
echo "./kcadm.sh create realms -f /tmp/keycloak-import/$REALM_NAME/realm.json"
echo "./kcadm.sh create clients -r $REALM_NAME -f /tmp/keycloak-import/$REALM_NAME/clients.json"
echo "./kcadm.sh create roles -r $REALM_NAME -f /tmp/keycloak-import/$REALM_NAME/roles.json"
echo "./kcadm.sh create groups -r $REALM_NAME -f /tmp/keycloak-import/$REALM_NAME/groups.json"
echo "./kcadm.sh create client-scopes -r $REALM_NAME -f /tmp/keycloak-import/$REALM_NAME/client-scopes.json"
echo "./kcadm.sh create users -r $REALM_NAME -f /tmp/keycloak-import/$REALM_NAME/users.json"