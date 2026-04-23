NAMESPACE="bcentral-testnet"

helm uninstall --namespace $NAMESPACE genesis
helm uninstall --namespace $NAMESPACE validator-1
helm uninstall --namespace $NAMESPACE validator-2
helm uninstall --namespace $NAMESPACE validator-3
helm uninstall --namespace $NAMESPACE validator-4
helm uninstall --namespace $NAMESPACE peer-1
helm uninstall --namespace $NAMESPACE peer-2
helm uninstall --namespace $NAMESPACE peer-3

kubectl delete --namespace emissary-system -f https://app.getambassador.io/yaml/edge-stack/latest/aes-crds.yaml
kubectl delete --namespace $NAMESPACE -f ../../ambassador-mapping-access.yaml 
kubectl delete --namespace $NAMESPACE -f ../../servicemonitors-access.yaml
kubectl delete --namespace $NAMESPACE -f ../../storageclass-access.yaml

kubectl delete namespace $NAMESPACE