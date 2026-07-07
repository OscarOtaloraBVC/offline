#!/bin/sh

VAULT_NAMESPACE="vault"
CONTAINER_NAME="vault"

UNSEAL_KEY_1="f+TGmZnm0UOf6mQmbg5zGl+feJfdNnfo7phZsFBQx3Ue"
UNSEAL_KEY_2="EkId4aZArAVq/6565qFQUOr3r1C1xZiUPoG3p8Qw297f"

KUBECTL=$(command -v kubectl)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

wait_running() {

    POD=$1

    while true
    do
        STATUS=$($KUBECTL get pod $POD -n $VAULT_NAMESPACE -o jsonpath='{.status.phase}' 2>/dev/null)

        READY=$($KUBECTL get pod $POD -n $VAULT_NAMESPACE \
            -o jsonpath='{.status.containerStatuses[0].ready}' 2>/dev/null)

        if [ "$STATUS" = "Running" ] && [ "$READY" = "true" ]; then
            log "$POD Running y Ready"
            break
        fi

        log "Esperando $POD... Status=$STATUS Ready=$READY"
        sleep 5
    done
}

restart_if_needed() {

    POD=$1

    STATUS=$($KUBECTL get pod $POD -n $VAULT_NAMESPACE -o jsonpath='{.status.phase}')

    if [ "$STATUS" != "Running" ]; then

        log "$POD está en $STATUS, reiniciando"

        $KUBECTL delete pod $POD -n $VAULT_NAMESPACE

        wait_running $POD
    fi
}

unseal_if_needed() {

    POD=$1

    STATUS=$($KUBECTL exec -n $VAULT_NAMESPACE $POD -- vault status 2>/dev/null)

    echo "$STATUS"

    if echo "$STATUS" | grep -q "Sealed.*true"; then

        log "$POD está SELLADO"

        $KUBECTL exec -n $VAULT_NAMESPACE $POD -- \
            vault operator unseal "$UNSEAL_KEY_1"

        sleep 2

        $KUBECTL exec -n $VAULT_NAMESPACE $POD -- \
            vault operator unseal "$UNSEAL_KEY_2"

        sleep 2

        log "Estado final de $POD"

        $KUBECTL exec -n $VAULT_NAMESPACE $POD -- vault status

    else

        log "$POD ya está UNSEALED"

    fi
}

main() {

    log "Listando pods"

    PODS=$($KUBECTL get pods -n $VAULT_NAMESPACE --no-headers \
        | awk '/^vault-/ {print $1}')

    for POD in $PODS
    do

        log "--------------------------------------"
        log "Procesando $POD"

        restart_if_needed $POD

        unseal_if_needed $POD

    done

    log "Proceso finalizado"

}

main