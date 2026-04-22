
1 - Inicializar SOLO vault-0

kubectl exec -n vault-raft vault-0 -- vault operator init

Unseal Key 1: < key 1>
Unseal Key 2: < key 2>
Unseal Key 3: < key 3>
Unseal Key 4: < key 4>
Unseal Key 5: < key 5>

Initial Root Token: hvs.< token >

Unseal vault-0

kubectl exec -n vault-raft vault-0 -- vault operator unseal < key 1>
kubectl exec -n vault-raft vault-0 -- vault operator unseal < key 2>
kubectl exec -n vault-raft vault-0 -- vault operator unseal < key 3>

2- Unseal nodos secundarios (Para nodos 1 y 2)

kubectl exec -n vault-raft vault-1 & 2 -- vault operator unseal < key 1>
kubectl exec -n vault-raft vault-1 & 2 -- vault operator unseal < key 2>
kubectl exec -n vault-raft vault-1 & 2 -- vault operator unseal < key 3>

3 - Validar cluster

kubectl exec -n vault-raft vault-0 -- vault login hvs.< token >
kubectl exec -n vault-raft vault-0 -- vault operator raft list-peers
kubectl exec -n vault-raft vault-1 -- vault status