$CLUSTER_NAME = 'AzLocalAKS'
$RESOURCE_GROUP = 'AzureLocal'

az connectedk8s proxy --name $CLUSTER_NAME --resource-group $RESOURCE_GROUP --file ./aks-arc-kube-config

$privateKeyFile= "local_key.pem"
az ssh arc --subscription "eb4b1bb2-61af-40ed-9c88-b176853ce3e6" --resource-group "AzureLocal" --name "AzLHost1" --local-user $username --private-key-file $privateKeyFile


# Get the AAD entity ID of the signed-in user to assign local cluster-admin role
$AAD_ENTITY_ID=$(az ad signed-in-user show --query userPrincipalName -o tsv)
kubectl create clusterrolebinding demo-user-binding --clusterrole cluster-admin --user=$AAD_ENTITY_ID


$env:KUBECONFIG = "$(Get-Location)\aks-arc-kube-config"

az aks get-credentials --resource-group $RESOURCE_GROUP --name $CLUSTER_NAME --admin