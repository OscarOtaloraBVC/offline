NAMESPACE="bcentral-testnet"

# Instalación de nodos validadores
echo "> Instalación de nodos validadores ..."
helm install validator-1 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml
helm install validator-2 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml
helm install validator-3 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml
helm install validator-4 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml

# Instalación de nodos de transacciones (peers)
echo "> Instalación de nodos de transacciones (peers) ..."
helm install peer-1 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/txnode.yaml
helm install peer-2 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/txnode.yaml
helm install peer-3 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/txnode.yaml

echo "> Instalación completa."