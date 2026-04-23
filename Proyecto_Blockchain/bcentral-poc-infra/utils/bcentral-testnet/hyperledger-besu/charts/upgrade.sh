NAMESPACE="bcentral-testnet"

# Instalación de nodos validadores
echo "> Upgrade de nodos validadores ..."
helm upgrade validator-1 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml --set tls.enabled=false --set node.besu.p2p.discovery=true
helm upgrade validator-2 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml --set tls.enabled=false --set node.besu.p2p.discovery=true
helm upgrade validator-3 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml --set tls.enabled=false --set node.besu.p2p.discovery=true
helm upgrade validator-4 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml --set tls.enabled=false --set node.besu.p2p.discovery=true

# Instalación de nodos de transacciones (peers)
echo "> Upgrade de nodos de transacciones (peers) ..."
helm upgrade peer-1 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/txnode.yaml --set tls.enabled=false --set node.besu.p2p.discovery=true
helm upgrade peer-2 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/txnode.yaml --set tls.enabled=false --set node.besu.p2p.discovery=true
helm upgrade peer-3 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/txnode.yaml --set tls.enabled=false --set node.besu.p2p.discovery=true

echo "> Upgrade completo."