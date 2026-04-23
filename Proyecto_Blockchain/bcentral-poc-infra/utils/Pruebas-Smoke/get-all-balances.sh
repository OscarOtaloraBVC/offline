#!/bin/bash

# URL del nodo Ethereum local (ajusta si usas otro puerto o IP)
NODE_URL="http://127.0.0.1:8545"

# --- Definir las 4 direcciones ---
ADDR1="0x"
ADDR2="0x"
ADDR3="0x"  
ADDR4="0x"  

# --- Función para obtener balance en ETH ---
get_balance_eth() {
    local addr=$1
    local balance_hex=$(curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"$addr\",\"latest\"],\"id\":1}" \
        "$NODE_URL" | jq -r '.result')
    
    # Si no hay respuesta válida, devolver 0
    if [[ -z "$balance_hex" || "$balance_hex" == "null" ]]; then
        echo "0"
    else
        python3 -c "print(int('$balance_hex', 16) / 10**18)"
    fi
}

# --- Obtener saldos ---
BALANCE1_ETH=$(get_balance_eth "$ADDR1")
BALANCE2_ETH=$(get_balance_eth "$ADDR2")
BALANCE3_ETH=$(get_balance_eth "$ADDR3")
BALANCE4_ETH=$(get_balance_eth "$ADDR4")

# --- Mostrar resultados ---
echo "=== Saldos en la red local ($NODE_URL) ==="
echo
echo "ADDRESS 1:"
echo "  Address: $ADDR1"
echo "  Balance: $BALANCE1_ETH testETH"
echo
echo "ADDRESS 2:"
echo "  Address: $ADDR2"
echo "  Balance: $BALANCE2_ETH testETH"
echo
echo "ADDRESS 3:"
echo "  Address: $ADDR3"
echo "  Balance: $BALANCE3_ETH testETH"
echo
echo "ADDRESS 4:"
echo "  Address: $ADDR4"
echo "  Balance: $BALANCE4_ETH testETH"
echo