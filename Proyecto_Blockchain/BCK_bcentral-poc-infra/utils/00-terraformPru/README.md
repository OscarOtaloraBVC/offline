## Before
- Quota: Update number of vcpu min. 10

## Deploy infrastructure of production on Azure

- Install azure cli:  https://learn.microsoft.com/en-us/cli/azure/install-azure-cli

- Login to azure
```
az login --use-device-code
```

- Deploy with terraform
```
cd tools/terraform

terraform init
terraform plan
terraform apply
```

- Checking cluster

```
az account set --subscription <id_of_subscription>
az aks get-credentials --resource-group BCC-Blockchain-group --name <name_of_aks> --overwrite-existing
kubectl get nodes
```
