# set some variables
$CLUSTER_NAME = 'AzLocalAKS'
$RESOURCE_GROUP = 'AzureLocal'


# Initial setup, 
# ssh into the k8s vm, and set up local admin for your user:
sudo kubectl create clusterrolebinding clusterUser_AzureLocal_AzLocalAKS --clusterrole cluster-admin --user=blaine@jimmielifed.onmicrosoft.us --kubeconfig=/etc/kubernetes/admin.conf

# Get the AAD entity ID of the signed-in user to assign local cluster-admin role to the user
$AAD_ENTITY_ID=$(az ad signed-in-user show --query userPrincipalName -o tsv)
kubectl create clusterrolebinding clusterUser_AzureLocal_AzLocalAKS --clusterrole cluster-admin --user=$AAD_ENTITY_ID
kubectl create clusterrolebinding $AAD_ENTITY_ID --clusterrole cluster-admin --user=$AAD_ENTITY_ID


# Now you can get into the cluster from your local machine

Connect-AzAccount -UseDeviceAuthentication -environment AzureUSGovernment

# start a proxy to get the kubeconfig file
az connectedk8s proxy --name $CLUSTER_NAME --resource-group $RESOURCE_GROUP --file ./aks-arc-kube-config

$AAD_ENTITY_OBJECT=$(az ad signed-in-user show --query id -o tsv)
kubectl create token $AAD_ENTITY_OBJECT -n default --kubeconfig ./aks-arc-kube-config

$env:KUBECONFIG = "$(Get-Location)\aks-arc-kube-config"

az connectedk8s show --name $CLUSTER_NAME --resource-group $RESOURCE_GROUP --file ./aks-arc-kube-config
