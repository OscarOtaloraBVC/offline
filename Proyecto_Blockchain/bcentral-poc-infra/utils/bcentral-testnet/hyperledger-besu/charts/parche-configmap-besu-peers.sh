kubectl delete configmap besu-peers -n bcentral-testnet

PUBKEY1=$(kubectl get secret besu-node-validator-1-keys -n bcentral-testnet -o jsonpath='{.data.nodekey\.pub}' | base64 -d)
PUBKEY2=$(kubectl get secret besu-node-validator-2-keys -n bcentral-testnet -o jsonpath='{.data.nodekey\.pub}' | base64 -d)
PUBKEY3=$(kubectl get secret besu-node-validator-3-keys -n bcentral-testnet -o jsonpath='{.data.nodekey\.pub}' | base64 -d)
PUBKEY4=$(kubectl get secret besu-node-validator-4-keys -n bcentral-testnet -o jsonpath='{.data.nodekey\.pub}' | base64 -d)

kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: besu-peers
  namespace: bcentral-testnet
data:
  static-nodes.json: |
    [
      "enode://${PUBKEY1}@besu-node-validator-1.bcentral-testnet.svc.cluster.local:30303?discport=0",
      "enode://${PUBKEY2}@besu-node-validator-2.bcentral-testnet.svc.cluster.local:30303?discport=0",
      "enode://${PUBKEY3}@besu-node-validator-3.bcentral-testnet.svc.cluster.local:30303?discport=0",
      "enode://${PUBKEY4}@besu-node-validator-4.bcentral-testnet.svc.cluster.local:30303?discport=0"
    ]
EOF