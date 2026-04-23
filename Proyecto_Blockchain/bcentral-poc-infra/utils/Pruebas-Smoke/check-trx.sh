#!/bin/bash

# Uso: ./check-tx.sh <transaction_hash> [rpc_url]
TX_HASH=$1
RPC_URL=${2:-"http://localhost:8545"}

if [ -z "$TX_HASH" ]; then
   echo "Uso.   : $0 <transaction_hash> [rpc_url]"
   echo "Ejemplo: $0 0x6c76c86166f26fa2bdfdb689d75b4ef4006261f33c6b2aecb016444628058965"
   exit 1
fi

# Add 0x prefix if not present
if [[ $TX_HASH != 0x* ]]; then
   TX_HASH="0x$TX_HASH"
fi

echo "Chequeando transacción: $TX_HASH"
echo "RPC URL: $RPC_URL"
echo "----------------------------------------"

# Get transaction receipt
RESPONSE=$(curl -s -X POST \
 -H "Content-Type: application/json" \
 -d "{
   \"jsonrpc\": \"2.0\",
   \"method\": \"eth_getTransactionReceipt\",
   \"params\": [\"$TX_HASH\"],
   \"id\": 1
 }" \
 $RPC_URL)

RESULT=$(echo $RESPONSE | jq -r '.result')

if [ "$RESULT" = "null" ]; then
   echo "❌ Transacción no encontrada o aún pendiente"
   echo "Esto podría significar:"
   echo "  - La transacción aún está en mempool (pendiente)"
   echo "  - El hash de la transacción no existe"
   echo "  - Problemas de conexión RPC"
else
   STATUS=$(echo $RESULT | jq -r '.status')
   BLOCK_NUMBER=$(echo $RESULT | jq -r '.blockNumber')
   BLOCK_HASH=$(echo $RESULT | jq -r '.blockHash')
   GAS_USED=$(echo $RESULT | jq -r '.gasUsed')
   FROM=$(echo $RESULT | jq -r '.from')
   TO=$(echo $RESULT | jq -r '.to')
  
   # Convert hex to decimal for block number and gas
   BLOCK_NUMBER_DEC=$((BLOCK_NUMBER))
   GAS_USED_DEC=$((GAS_USED))

   echo "✅ Transacción confirmada!"
   echo "Estado: $([ "$STATUS" = "0x1" ] && echo "SUCCESS ✅" || echo "FAILED ❌")"
   echo "Block Number: $BLOCK_NUMBER_DEC ($BLOCK_NUMBER)"
   echo "Block Hash: $BLOCK_HASH"
   echo "From: $FROM"
   echo "To: $TO"
   echo "Gas Used: $GAS_USED_DEC ($GAS_USED)"
fi

