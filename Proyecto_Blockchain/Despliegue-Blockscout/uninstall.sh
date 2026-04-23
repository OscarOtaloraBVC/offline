NAMESPACE="blockscout"
RELEASE_NAME="explorer"

helm uninstall $RELEASE_NAME --namespace $NAMESPACE

kubectl delete namespace $NAMESPACE