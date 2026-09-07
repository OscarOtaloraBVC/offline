#!/bin/bash
# Script de importación para Keycloak
# Generado automáticamente el: 2026-08-06 18:05:06

echo "========================================="
echo "IMPORTANDO REINOS EN KEYCLOAK"
echo "========================================="

cd /opt/keycloak/bin

# Configurar credenciales
echo "Configurando credenciales..."
./kcadm.sh config credentials --server http://localhost:8081 --realm master --user ootalora --password CFT6yhn234
echo "Credenciales configuradas"

# Función para importar reino
import_realm() {
    local realm=$1
    echo ""
    echo "📦 Importando reino: $realm"
    echo "-----------------------------------------"
    
    # Verificar si el reino ya existe
    if ./kcadm.sh get realms/$realm > /dev/null 2>&1; then
        echo "⚠️ El reino $realm ya existe, omitiendo..."
        return 0
    fi
    
    # Importar metadatos del reino
    if [ -f "/tmp/keycloak-import/$realm/realm.json" ]; then
        echo "  Importando metadatos del reino..."
        ./kcadm.sh create realms -f /tmp/keycloak-import/$realm/realm.json
    fi
    
    # Importar componentes
    for component in clients roles groups client-scopes; do
        if [ -f "/tmp/keycloak-import/$realm/$component.json" ]; then
            echo "  Importando $component..."
            ./kcadm.sh create $component -r $realm -f /tmp/keycloak-import/$realm/$component.json
        fi
    done
    
    # Importar usuarios (sin contraseñas)
    if [ -f "/tmp/keycloak-import/$realm/users.json" ]; then
        echo "  Importando usuarios..."
        ./kcadm.sh create users -r $realm -f /tmp/keycloak-import/$realm/users.json
    fi
    
    echo "✅ $realm importado"
}

import_realm "tws-prod"

#import_realm "vericlear-preprod"

echo ""
echo "========================================="
echo "IMPORTACIÓN COMPLETADA"
echo "========================================="

echo "Resumen de importación:"
ls -la /tmp/keycloak-import/