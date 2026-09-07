#!/bin/bash
# listar todos los pv
# kubectl get pvc --all-namespaces
# Función para convertir a GiB
convert_to_gib() {
    local value=$1
    local numeric=$(echo "$value" | sed 's/[^0-9.]*//g')
    local unit=$(echo "$value" | sed 's/[0-9.]*//g' | tr '[:lower:]' '[:upper:]')
    
    if [ -z "$numeric" ]; then
        echo "N/A"
        return
    fi
    
    case "$unit" in
        "KI"|"K")
            echo "scale=2; $numeric / 1024 / 1024" | bc
            ;;
        "MI"|"M")
            echo "scale=2; $numeric / 1024" | bc
            ;;
        "GI"|"G"|"")
            echo "$numeric"
            ;;
        "TI"|"T")
            echo "scale=2; $numeric * 1024" | bc
            ;;
        *)
            echo "$numeric"
            ;;
    esac
}

# Función para convertir bytes a GiB
convert_bytes_to_gib() {
    local bytes=$1
    if [ "$bytes" = "N/A" ] || [ -z "$bytes" ]; then
        echo "N/A"
        return
    fi
    echo "scale=2; $bytes / 1024 / 1024 / 1024" | bc
}

# Encabezado
printf "%-35s %-20s %-35s %-12s %-12s\n" \
    "PV" "NAMESPACE" "CLAIM" "CAPACITY(Gi)" "USED(Gi)"
printf "%-35s %-20s %-35s %-12s %-12s\n" \
    "$(printf '%0.s-' {1..35})" "$(printf '%0.s-' {1..20})" \
    "$(printf '%0.s-' {1..35})" "$(printf '%0.s-' {1..12})" "$(printf '%0.s-' {1..12})"

kubectl get pv -o json |
jq -r '
  .items[] |
  [
    .metadata.name,
    .spec.capacity.storage,
    (.spec.claimRef.name // ""),
    (.spec.claimRef.namespace // "")
  ] | @tsv
' |
while IFS=$'\t' read -r pv capacity claim namespace; do

    used="N/A"

    if [ -n "$claim" ] && [ -n "$namespace" ]; then

        # Buscar Pod Running que utilice el PVC
        pod=$(kubectl get pods -n "$namespace" -o json 2>/dev/null |
            jq -r --arg pvc "$claim" '
                .items[]
                | select(.status.phase == "Running")
                | select(
                    any(.spec.volumes[]?;
                        .persistentVolumeClaim.claimName == $pvc
                    )
                )
                | .metadata.name
            ' |
            head -n 1)

        if [ -n "$pod" ]; then

            # Obtener los volume names asociados al PVC
            volumes=$(kubectl get pod "$pod" -n "$namespace" -o json |
                jq -r --arg pvc "$claim" '
                    .spec.volumes[]
                    | select(.persistentVolumeClaim.claimName == $pvc)
                    | .name
                ')

            for volume in $volumes; do

                # Obtener mountPath
                mount_path=$(kubectl get pod "$pod" -n "$namespace" -o json |
                    jq -r --arg volume "$volume" '
                        .spec.containers[]
                        | .volumeMounts[]
                        | select(.name == $volume)
                        | .mountPath
                    ' |
                    head -n 1)

                if [ -n "$mount_path" ]; then

                    # Obtener uso en bytes y convertir a GiB
                    used_bytes=$(kubectl exec -n "$namespace" "$pod" -- \
                        df -B1 "$mount_path" 2>/dev/null |
                        awk 'NR==2 {print $3}')
                    
                    if [ -n "$used_bytes" ]; then
                        used=$(convert_bytes_to_gib "$used_bytes")
                    else
                        used="N/A"
                    fi
                    
                    break
                fi
            done

        else
            used="Unassigned"
        fi
    fi

    # Convertir capacidad a GiB
    capacity_gib=$(convert_to_gib "$capacity")

    printf "%-35s %-20s %-35s %-12s %-12s\n" \
        "$pv" "$namespace" "$claim" "$capacity_gib" "$used"

done