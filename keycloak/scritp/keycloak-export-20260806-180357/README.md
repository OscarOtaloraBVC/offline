# Exportación de Keycloak

## Información de la exportación

- **Fecha:** 2026-08-06 18:05:06
- **Namespace:** `keycloak`
- **Pod:** `keycloak-nuam-0`
- **Usuario:** `ootalora`
- **Servidor:** `http://localhost:8080`
- **Reinos excluidos:** `master, nuam`
- **Reinos exportados:** 2

## Estructura de archivos
```
keycloak-export-20260806-180357/
├── import-realms.sh     # Script para importar todos los reinos
├── README.md            # Este archivo
└── [reino]/             # Cada reino tiene su propia carpeta
    ├── realm.json        # Metadatos del reino
    ├── users.json        # Usuarios del reino
    ├── clients.json      # Clientes del reino
    ├── roles.json        # Roles del reino
    ├── groups.json       # Grupos del reino
    ├── client-scopes/    # Scopes de cliente detallados
    └── identity-providers.json # Proveedores de identidad
```

## Cómo importar los reinos

### 1. Copiar los archivos al pod destino:
```bash
kubectl cp keycloak-export-20260806-180357 -n <namespace-destino> <pod-destino>:/tmp/keycloak-import
```

### 2. Ejecutar el script de importación:
```bash
kubectl exec -it -n <namespace-destino> <pod-destino> -- /bin/bash -c "
  chmod +x /tmp/keycloak-import/import-realms.sh &&
  /tmp/keycloak-import/import-realms.sh
"
```

### 3. Para importar reinos individuales:
```bash
kubectl exec -it -n <namespace-destino> <pod-destino> -- /bin/bash -c "
  cd /opt/keycloak/bin &&
  ./kcadm.sh config credentials --server http://localhost:8080 --realm master --user admin --password admin &&
  ./kcadm.sh create realms -f /tmp/keycloak-import/<reino>/realm.json
"
```

## Notas importantes

1. **Usuarios:** Los usuarios se importan sin contraseñas (requieren reset de contraseña)
2. **IDs:** Verificar que los IDs no estén duplicados en el sistema destino
3. **Secretos:** Los secretos de clientes pueden cambiar, verificar después de la importación
4. **Dependencias:** Asegurar que los reinos dependientes estén importados primero
5. **Archivos vacíos:** Los archivos sin datos contienen `[]` o `{}` según corresponda

## Verificación de la importación

```bash
# Verificar reinos importados
kubectl exec -it -n <namespace> <pod> -- /bin/bash -c "
  cd /opt/keycloak/bin &&
  ./kcadm.sh config credentials --server http://localhost:8080 --realm master --user admin --password admin &&
  ./kcadm.sh get realms --fields realm,displayName,enabled
"
```