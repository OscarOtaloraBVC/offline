NAMESPACE="bcentral-testnet"

helm uninstall --namespace $NAMESPACE validator-1
helm uninstall --namespace $NAMESPACE validator-2
helm uninstall --namespace $NAMESPACE validator-3
helm uninstall --namespace $NAMESPACE validator-4
helm uninstall --namespace $NAMESPACE peer-1
helm uninstall --namespace $NAMESPACE peer-2
helm uninstall --namespace $NAMESPACE peer-3