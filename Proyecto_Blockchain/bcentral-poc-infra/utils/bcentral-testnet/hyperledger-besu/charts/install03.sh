NAMESPACE="bcentral-testnet"

echo "> Actualizar dependencias ..."
helm dependency update besu-genesis
helm dependency update besu-node

kubectl create namespace $NAMESPACE # if the namespace does not exist already

# Pre-requisitos:
# Instalar Ambassador Edge Stack
echo "> Instalar Ambassador Edge Stack ..."
kubectl apply -f https://app.getambassador.io/yaml/edge-stack/latest/aes-crds.yaml
#kubectl apply -f ../../aes-crds.yaml
kubectl apply -f ../../ambassador-mapping-access.yaml --namespace $NAMESPACE          #
kubectl apply -f ../../servicemonitors-access.yaml    --namespace $NAMESPACE          #
kubectl apply -f ../../storageclass-access.yaml

# Create the roottoken secret
echo "> Creando roottoken secret ..."
kubectl -n $NAMESPACE create secret generic roottoken --from-literal=token="hvs.<root_token>"       #bcentral

# Instalación del chart de genesis
echo "> Instalación de chart de genesis ..."
helm install genesis ./besu-genesis --namespace $NAMESPACE --values ./values/proxy-and-vault/genesis.yaml

# Instalación de nodos validadores
echo "> Instalación de nodos validadores ..."
helm install validator-1 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml
helm install validator-2 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml
helm install validator-3 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml
helm install validator-4 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml

# Instalación de nodos de transacciones (peers)
echo "> Instalación de nodos de transacciones (peers) ..."
helm install peer-1      ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/txnode.yaml
helm install peer-2      ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/txnode.yaml
helm install peer-3      ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/txnode.yaml

echo "> Instalación completa."