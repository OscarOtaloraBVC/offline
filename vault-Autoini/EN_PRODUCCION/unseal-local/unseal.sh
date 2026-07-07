#!/bin/sh

VAULT_NAMESPACE="${VAULT_NAMESPACE:-vault}"
CONTAINER_NAME="${CONTAINER_NAME:-vault}"
SECRET_NAME="${SECRET_NAME:-vault-unseal-keys}"

KUBECTL=$(command -v kubectl)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Función para obtener secretos de Kubernetes
get_secret() {
    local secret_key=$1
    $KUBECTL get secret "$SECRET_NAME" -n "$VAULT_NAMESPACE" -o jsonpath="{.data.$secret_key}" 2>/dev/null | base64 -d
}

# Función para obtener las claves de desbloqueo
get_unseal_keys() {
    log "Obteniendo claves de desbloqueo desde Kubernetes secrets..."
    
    UNSEAL_KEY_1=$(get_secret "unseal-key-1")
    UNSEAL_KEY_2=$(get_secret "unseal-key-2")
    
    if [ -z "$UNSEAL_KEY_1" ] || [ -z "$UNSEAL_KEY_2" ]; then
        log "ERROR: No se pudieron obtener las claves de desbloqueo"
        log "Verificando que el secreto existe..."
        $KUBECTL get secret "$SECRET_NAME" -n "$VAULT_NAMESPACE" 2>/dev/null || echo "Secret $SECRET_NAME no encontrado"
        return 1
    fi
    
    log "Claves obtenidas correctamente"
    return 0
}

wait_running() {
    POD=$1
    local MAX_RETRIES=30
    local RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        STATUS=$($KUBECTL get pod "$POD" -n "$VAULT_NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null)
        READY=$($KUBECTL get pod "$POD" -n "$VAULT_NAMESPACE" \
            -o jsonpath='{.status.containerStatuses[0].ready}' 2>/dev/null)
        
        if [ "$STATUS" = "Running" ] && [ "$READY" = "true" ]; then
            log "$POD Running y Ready"
            return 0
        fi
        
        log "Esperando $POD... Status=$STATUS Ready=$READY ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 5
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done
    
    log "ERROR: Tiempo de espera agotado para $POD"
    return 1
}

restart_if_needed() {
    POD=$1
    
    STATUS=$($KUBECTL get pod "$POD" -n "$VAULT_NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null)
    
    if [ "$STATUS" != "Running" ] && [ -n "$STATUS" ]; then
        log "$POD está en $STATUS, reiniciando"
        $KUBECTL delete pod "$POD" -n "$VAULT_NAMESPACE"
        wait_running "$POD"
        return $?
    elif [ -z "$STATUS" ]; then
        log "ERROR: No se pudo obtener estado de $POD"
        return 1
    fi
    
    return 0
}

unseal_if_needed() {
    POD=$1
    
    log "Verificando estado de Vault en $POD..."
    VAULT_STATUS=$($KUBECTL exec -n "$VAULT_NAMESPACE" "$POD" -c "$CONTAINER_NAME" -- vault status 2>/dev/null)
    
    if [ $? -ne 0 ] && [ -z "$VAULT_STATUS" ]; then
        log "ERROR: No se pudo obtener el estado de Vault en $POD"
        return 1
    fi
    
    echo "$VAULT_STATUS"
    
    if echo "$VAULT_STATUS" | grep -q "Sealed.*true"; then
        log "$POD está SELLADO - Iniciando desbloqueo..."
        
        if ! get_unseal_keys; then
            return 1
        fi
        
        log "Aplicando primera clave de desbloqueo..."
        $KUBECTL exec -n "$VAULT_NAMESPACE" "$POD" -c "$CONTAINER_NAME" -- vault operator unseal "$UNSEAL_KEY_1"
        
        sleep 2
        
        log "Aplicando segunda clave de desbloqueo..."
        $KUBECTL exec -n "$VAULT_NAMESPACE" "$POD" -c "$CONTAINER_NAME" -- vault operator unseal "$UNSEAL_KEY_2"
        
        sleep 2
        
        log "=== Estado final de $POD ==="
        $KUBECTL exec -n "$VAULT_NAMESPACE" "$POD" -c "$CONTAINER_NAME" -- vault status
    else
        log "$POD ya está UNSEALED o no se pudo determinar el estado"
    fi
    
    return 0
}

main() {
    log "========================================="
    log "Iniciando proceso de desbloqueo de Vault"
    log "Namespace: $VAULT_NAMESPACE"
    log "Secret: $SECRET_NAME"
    log "========================================="
    
    # Verificar que kubectl está disponible
    if [ -z "$KUBECTL" ]; then
        log "ERROR: kubectl no encontrado en el PATH"
        exit 1
    fi
    
    # Verificar que el secret existe
    log "Verificando existencia del Secret..."
    if ! $KUBECTL get secret "$SECRET_NAME" -n "$VAULT_NAMESPACE" &>/dev/null; then
        log "ERROR: Secret $SECRET_NAME no existe en namespace $VAULT_NAMESPACE"
        $KUBECTL get secrets -n "$VAULT_NAMESPACE" 2>/dev/null || echo "No se pudieron listar secrets"
        exit 1
    fi
    
    log "Listando pods de Vault..."
    PODS=$($KUBECTL get pods -n "$VAULT_NAMESPACE" --no-headers 2>/dev/null | awk '/^vault-/ {print $1}')
    
    if [ -z "$PODS" ]; then
        log "ERROR: No se encontraron pods de Vault en namespace $VAULT_NAMESPACE"
        log "Pods disponibles:"
        $KUBECTL get pods -n "$VAULT_NAMESPACE" 2>/dev/null || echo "No se pudieron listar pods"
        exit 1
    fi
    
    for POD in $PODS; do
        log ""
        log "--------------------------------------"
        log "Procesando $POD"
        log "--------------------------------------"
        
        restart_if_needed "$POD"
        if [ $? -ne 0 ]; then
            log "WARNING: No se pudo verificar/reiniciar $POD, continuando..."
            continue
        fi
        
        unseal_if_needed "$POD"
        if [ $? -ne 0 ]; then
            log "WARNING: No se pudo desbloquear $POD"
        fi
    done
    
    log ""
    log "========================================="
    log "Proceso de desbloqueo finalizado"
    log "========================================="
}

main