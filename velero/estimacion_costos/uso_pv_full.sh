#!/bin/bash
# genera una tabla con PV, NAMESPACE, PVC, CAPACITY, USED, AVAILABLE, USE% y POD.
# Función para convertir a GiB
convert_to_gib() {
    local value=$1
    local numeric=$(echo "$value" | sed 's/[^0-9.]*//g')
    local unit=$(echo "$value" | sed 's/[0-9.]*//g' | tr '[:lower:]' '[:upper:]')
    
    if [ -z "$numeric" ]; then
        echo "0"
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
    if [ -z "$bytes" ] || [ "$bytes" = "0" ]; then
        echo "0"
        return
    fi
    echo "scale=2; $bytes / 1024 / 1024 / 1024" | bc
}

# Función para calcular porcentaje de uso
calculate_usage_percent() {
    local used=$1
    local total=$2
    
    if [ -z "$used" ] || [ -z "$total" ] || [ "$total" = "0" ]; then
        echo "0.00"
        return
    fi
    
    # Convertir a números para cálculo
    used_num=$(echo "$used" | sed 's/[^0-9.]*//g')
    total_num=$(echo "$total" | sed 's/[^0-9.]*//g')
    
    if [ -z "$used_num" ] || [ -z "$total_num" ] || [ "$total_num" = "0" ]; then
        echo "0.00"
        return
    fi
    
    echo "scale=2; ($used_num / $total_num) * 100" | bc
}

# Encabezado
printf "%-35s | %-20s | %-35s | %-10s | %-10s | %-10s | %-7s | %-30s\n" \
    "PV" "NAMESPACE" "PVC" "CAPACITY" "USED" "AVAILABLE" "USE%" "POD"
printf "%-35s-+-%-20s-+-%-35s-+-%-10s-+-%-10s-+-%-10s-+-%-7s-+-%-30s\n" \
    "$(printf '%0.s-' {1..35})" "$(printf '%0.s-' {1..20})" \
    "$(printf '%0.s-' {1..35})" "$(printf '%0.s-' {1..10})" \
    "$(printf '%0.s-' {1..10})" "$(printf '%0.s-' {1..10})" \
    "$(printf '%0.s-' {1..7})" "$(printf '%0.s-' {1..30})"

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

    used="0"
    available="0"
    usage_percent="0.00"
    pod_name=""

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
            pod_name="$pod"
            
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

                    # Obtener estadísticas del volumen montado
                    df_output=$(kubectl exec -n "$namespace" "$pod" -- \
                        df -B1 "$mount_path" 2>/dev/null | awk 'NR==2 {print $2, $3, $4}')
                    
                    if [ -n "$df_output" ]; then
                        total_bytes=$(echo "$df_output" | awk '{print $1}')
                        used_bytes=$(echo "$df_output" | awk '{print $2}')
                        available_bytes=$(echo "$df_output" | awk '{print $3}')
                        
                        # Convertir a GiB
                        used=$(convert_bytes_to_gib "$used_bytes")
                        available=$(convert_bytes_to_gib "$available_bytes")
                        total_gib=$(convert_bytes_to_gib "$total_bytes")
                        
                        # Calcular porcentaje de uso
                        usage_percent=$(calculate_usage_percent "$used" "$total_gib")
                    fi
                    
                    break
                fi
            done

        else
            pod_name="Unassigned"
        fi
    fi

    # Convertir capacidad a GiB
    capacity_gib=$(convert_to_gib "$capacity")

    printf "%-35s | %-20s | %-35s | %-10s | %-10s | %-10s | %7s%% | %-30s\n" \
        "$pv" "$namespace" "$claim" "${capacity_gib}Gi" "${used}Gi" "${available}Gi" "$usage_percent" "$pod_name"

done