
1 - Inicializar SOLO vault-0

kubectl exec -n vault-raft vault-0 -- vault operator init

Unseal Key 1: JT4bxm2UDtkQ/RTnctEi4knb/dUIu8LEoWqdTwxCP0Rh
Unseal Key 2: XyJwfnPp0O7yxOUnCZCB24rJYXxwlVZoWVkxUw2LJmEC
Unseal Key 3: dWESPYionzQA4qkdtsk65qF8aTxLDKh+q7lVx13bXN3p
Unseal Key 4: So8khxfoHhuvsROD/KCswvfMevM+ccQYn3qSj9Ri0/A4
Unseal Key 5: VX/6ChbVscYPGSJpcLqx9DwtuCxJKrppLw4BtZAkJGlU

Initial Root Token: hvs.ZOGivdFyeOyIcCDYslDQiqIO

Unseal vault-0

kubectl exec -n vault-raft vault-0 -- vault operator unseal JT4bxm2UDtkQ/RTnctEi4knb/dUIu8LEoWqdTwxCP0Rh
kubectl exec -n vault-raft vault-0 -- vault operator unseal XyJwfnPp0O7yxOUnCZCB24rJYXxwlVZoWVkxUw2LJmEC
kubectl exec -n vault-raft vault-0 -- vault operator unseal dWESPYionzQA4qkdtsk65qF8aTxLDKh+q7lVx13bXN3p

2- Unseal nodos secundarios (Para nodos 1 y 2)

kubectl exec -n vault-raft vault-1 & 2 -- vault operator unseal JT4bxm2UDtkQ/RTnctEi4knb/dUIu8LEoWqdTwxCP0Rh
kubectl exec -n vault-raft vault-1 & 2 -- vault operator unseal XyJwfnPp0O7yxOUnCZCB24rJYXxwlVZoWVkxUw2LJmEC
kubectl exec -n vault-raft vault-1 & 2 -- vault operator unseal dWESPYionzQA4qkdtsk65qF8aTxLDKh+q7lVx13bXN3p

3 - Validar cluster

kubectl exec -n vault-raft vault-0 -- vault login hvs.ZOGivdFyeOyIcCDYslDQiqIO
kubectl exec -n vault-raft vault-0 -- vault operator raft list-peers
kubectl exec -n vault-raft vault-1 -- vault status