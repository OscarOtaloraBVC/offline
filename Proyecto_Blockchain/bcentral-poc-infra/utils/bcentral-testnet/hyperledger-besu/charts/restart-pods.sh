# Reinicia los pods
# Reinicia los pods
kubectl delete pod \
    besu-node-validator-1-0 \
    besu-node-validator-2-0 \
    besu-node-validator-3-0 \
    besu-node-validator-4-0 \
    besu-node-peer-1-0 \
    besu-node-peer-2-0 \
    besu-node-peer-3-0 \
-n bcentral-testnet