NAMESPACE="bcentral-testnet"

helm dependency update besu-genesis
helm dependency update besu-node

kubectl create namespace $NAMESPACE # if the namespace does not exist already

# Pre-requisitos:
# Instalar Ambassador Edge Stack
kubectl apply -f https://app.getambassador.io/yaml/edge-stack/latest/aes-crds.yaml
kubectl apply -f ../../ambassador-mapping-access.yaml --namespace $NAMESPACE          #
kubectl apply -f ../../servicemonitors-access.yaml    --namespace $NAMESPACE          #
kubectl apply -f ../../storageclass-access.yaml

# Create the roottoken secret
kubectl -n $NAMESPACE create secret generic roottoken --from-literal=token="hvs.q7A5FNeQ4ape4l3EM1xnyjao"

# Instalación del chart de genesis
helm install genesis ./besu-genesis --namespace $NAMESPACE --values ./values/proxy-and-vault/genesis.yaml

# Instalación de nodos validadores
helm install validator-1 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml --set tls.enabled=false --set node.besu.p2p.discovery=true
helm install validator-2 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml --set tls.enabled=false --set node.besu.p2p.discovery=true
helm install validator-3 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml --set tls.enabled=false --set node.besu.p2p.discovery=true
helm install validator-4 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml --set tls.enabled=false --set node.besu.p2p.discovery=true
#helm install validator-1 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml #--set global.proxy.p2p=15011
#helm install validator-2 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml #--set global.proxy.p2p=15012
#helm install validator-3 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml #--set global.proxy.p2p=15013
#helm install validator-4 ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/validator.yaml #--set global.proxy.p2p=15014

# Instalación de nodos de transacciones (peers)
helm install peer-1      ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/txnode.yaml    #--set global.proxy.p2p=15015
helm install peer-2      ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/txnode.yaml    #--set global.proxy.p2p=15016
helm install peer-3      ./besu-node --namespace $NAMESPACE --values ./values/proxy-and-vault/txnode.yaml    #--set global.proxy.p2p=15017