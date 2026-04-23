TOKEN=hvs.YTPXQ7A0Lv71DyAD6MyFNyh6
VAULT_SERVER=localhost:8200
NETWORK=testnet
RPC_URL=http://localhost:8545
CHAIN_ID=1337

RESP1=`curl -s -H "X-Vault-Token: $TOKEN" -X GET http://$VAULT_SERVER/v1/secretsv2/data/$NETWORK/besu-node-validator-1-keys`
RESP2=`curl -s -H "X-Vault-Token: $TOKEN" -X GET http://$VAULT_SERVER/v1/secretsv2/data/$NETWORK/besu-node-validator-2-keys`
RESP3=`curl -s -H "X-Vault-Token: $TOKEN" -X GET http://$VAULT_SERVER/v1/secretsv2/data/$NETWORK/besu-node-validator-3-keys`
RESP4=`curl -s -H "X-Vault-Token: $TOKEN" -X GET http://$VAULT_SERVER/v1/secretsv2/data/$NETWORK/besu-node-validator-4-keys`

ADDRESS1=`echo $RESP1 | jq -r '.data.data | "\(.accountAddress)"'`
PRIVATE1=`echo $RESP1 | jq -r '.data.data | "\(.accountPrivateKey)"'`

ADDRESS2=`echo $RESP2 | jq -r '.data.data | "\(.accountAddress)"'`
PRIVATE2=`echo $RESP2 | jq -r '.data.data | "\(.accountPrivateKey)"'`

ADDRESS3=`echo $RESP3 | jq -r '.data.data | "\(.accountAddress)"'`
PRIVATE3=`echo $RESP3 | jq -r '.data.data | "\(.accountPrivateKey)"'`

ADDRESS4=`echo $RESP4 | jq -r '.data.data | "\(.accountAddress)"'`
PRIVATE4=`echo $RESP4 | jq -r '.data.data | "\(.accountPrivateKey)"'`

PRIVATE_KEY=$PRIVATE2
FROM_ADDR=$ADDRESS2
TO_ADDR=$ADDRESS1
AMOUNT_ETH=1000

python3 transfer-eth.py $RPC_URL $PRIVATE_KEY $FROM_ADDR $TO_ADDR $AMOUNT_ETH $CHAIN_ID