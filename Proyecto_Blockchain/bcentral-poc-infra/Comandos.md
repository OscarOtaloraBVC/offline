# Comandos adicionales infra

## Desplegar contour 
> Ruta del archivo contour.yaml E:\WSL 

```bash
# ruta
cd /mnt/e/WSL/  
# despliega contour (ingress)
kubectl apply -f contour.yaml  

#verificar  (se requiere acceso del aks como network contributor en vnet)
kubectl get svc -n projectcontour

```

# Generar certifciados


```bash
# Para grafana
# Considerar haber creado el grafana.labbcch.local.cfg
openssl req -new -nodes -out grafana.labbcch.local.csr -keyout grafana.labbcch.local-orig.key -config grafana.labbcch.local.cfg
 

## NOTAS.
# dominios para BESU
# UI para los bloques
etablockscoutbc.labbcch.local

# Metamak
etadnodesapi.labbcch.local

# App front
etadwebcontratos.labbcch.local

# Vault
# Es a criterio de rodrigo


# para generar los certificados
# ejecutar desde /mnt/e/WSL/bcentral-poc-infra/utils/00-terraform/cert
openssl req -new -nodes -out etablockscoutbc.labbcch.local.csr -keyout etablockscoutbc.labbcch.local-orig.key -config etablockscoutbc.labbcch.local.cfg

openssl req -new -nodes -out etadnodesapi.labbcch.local.csr -keyout etadnodesapi.labbcch.local-orig.key -config etadnodesapi.labbcch.local.cfg

openssl req -new -nodes -out etadwebcontratos.labbcch.local.csr -keyout etadwebcontratos.labbcch.local-orig.key -config etadwebcontratos.labbcch.local.cfg

```
