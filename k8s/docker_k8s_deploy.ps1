# Enhanced Kubernetes deployment script with error handling and proper setup

# Set error action preference to stop on errors
$ErrorActionPreference = "Stop"

Write-Host "=== Kubernetes Deployment Script ===" -ForegroundColor Green

# Check if we're in the right directory
$currentDir = Get-Location
$expectedPath = "AzureLocal-Demo-streamlit-kafka-PostgreSQL"
if ($currentDir.Path -notlike "*$expectedPath*") {
    Write-Host "Warning: Make sure you're running this from the project root directory" -ForegroundColor Yellow
    Write-Host "Current directory: $currentDir" -ForegroundColor Yellow
}

# Step 1: Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Cyan

# Check if kubectl is available
try {
    kubectl version --client --short
    Write-Host "✓ kubectl is available" -ForegroundColor Green
} catch {
    Write-Host "✗ kubectl is not available or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if Docker is available
try {
    docker --version
    Write-Host "✓ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not available or not in PATH" -ForegroundColor Red
    exit 1
}

# Check current kubectl context
Write-Host "Current kubectl context:" -ForegroundColor Cyan
kubectl config current-context

# Step 2: Build the Docker image
Write-Host "`n=== Building Docker Image ===" -ForegroundColor Green
Write-Host "Building streamlit-kafka-app:latest..." -ForegroundColor Cyan

try {
    # Build the image from the project root
    docker build -t streamlit-kafka-app:latest .
    Write-Host "✓ Docker image built successfully" -ForegroundColor Green
    
    # Also tag it with the bcperry prefix for compatibility with existing manifests
    docker tag streamlit-kafka-app:latest bcperry/streamlit-kafka-app:latest
    Write-Host "✓ Image tagged as bcperry/streamlit-kafka-app:latest" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to build Docker image" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# For minikube users, load the image
$k8sContext = kubectl config current-context
if ($k8sContext -like "*minikube*") {
    Write-Host "Detected minikube context. Loading image into minikube..." -ForegroundColor Cyan
    try {
        minikube image load streamlit-kafka-app:latest
        minikube image load bcperry/streamlit-kafka-app:latest
        Write-Host "✓ Images loaded into minikube" -ForegroundColor Green
    } catch {
        Write-Host "! Warning: Failed to load image into minikube. Continuing anyway..." -ForegroundColor Yellow
    }
}

# Step 3: Deploy Kubernetes resources
Write-Host "`n=== Deploying Kubernetes Resources ===" -ForegroundColor Green

# Function to apply manifest and check result
function Apply-Manifest {
    param($manifestFile, $description)
    
    Write-Host "Applying $description..." -ForegroundColor Cyan
    try {
        kubectl apply -f $manifestFile
        Write-Host "✓ $description applied successfully" -ForegroundColor Green
    } catch {
        Write-Host "✗ Failed to apply $description" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        throw
    }
}

# Function to wait for deployment
function Wait-ForDeployment {
    param($deploymentName, $namespace, $description)
    
    Write-Host "Waiting for $description to be ready..." -ForegroundColor Cyan
    try {
        kubectl wait --for=condition=available --timeout=300s deployment/$deploymentName -n $namespace
        Write-Host "✓ $description is ready" -ForegroundColor Green
    } catch {
        Write-Host "! Warning: $description may not be ready yet. Checking pod status..." -ForegroundColor Yellow
        kubectl get pods -n $namespace | Where-Object { $_ -like "*$deploymentName*" }
    }
}

try {
    # Apply manifests in order
    Apply-Manifest "k8s/namespace.yaml" "Namespace and ConfigMap"
    Apply-Manifest "k8s/secrets.yaml" "Secrets"
    Apply-Manifest "k8s/storage.yaml" "Storage (PV/PVC)"
    Apply-Manifest "k8s/zookeeper.yaml" "ZooKeeper"
    
    Wait-ForDeployment "zookeeper" "kafka-demo" "ZooKeeper"
    
    Apply-Manifest "k8s/kafka.yaml" "Kafka"
    
    Wait-ForDeployment "kafka" "kafka-demo" "Kafka"
    
    Apply-Manifest "k8s/postgres.yaml" "PostgreSQL"
    
    Wait-ForDeployment "postgres" "kafka-demo" "PostgreSQL"
    
    # Deploy applications
    Apply-Manifest "k8s/kafka-producer.yaml" "Kafka Producer"
    Apply-Manifest "k8s/kafka-to-postgres.yaml" "Kafka to PostgreSQL Consumer"
    Apply-Manifest "k8s/streamlit.yaml" "Streamlit Dashboard"
    Apply-Manifest "k8s/kafka-ui.yaml" "Kafka UI"
    
    Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
    
} catch {
    Write-Host "`n✗ Deployment failed. Check the error messages above." -ForegroundColor Red
    exit 1
}

# Step 4: Show deployment status
Write-Host "`n=== Deployment Status ===" -ForegroundColor Green

Write-Host "Checking pod status..." -ForegroundColor Cyan
kubectl get pods -n kafka-demo

Write-Host "`nChecking services..." -ForegroundColor Cyan
kubectl get services -n kafka-demo

Write-Host "`n=== Access Information ===" -ForegroundColor Green
Write-Host "Streamlit Dashboard: http://localhost:30001" -ForegroundColor Cyan
Write-Host "Kafka UI: http://localhost:30002" -ForegroundColor Cyan

Write-Host "`nAlternatively, use port forwarding:" -ForegroundColor Yellow
Write-Host "kubectl port-forward service/streamlit-service 8501:8501 -n kafka-demo" -ForegroundColor Yellow
Write-Host "kubectl port-forward service/kafka-ui-service 8080:8080 -n kafka-demo" -ForegroundColor Yellow

Write-Host "`n=== Monitoring Commands ===" -ForegroundColor Green
Write-Host "Check logs:" -ForegroundColor Cyan
Write-Host "kubectl logs -f deployment/kafka-producer -n kafka-demo" -ForegroundColor White
Write-Host "kubectl logs -f deployment/streamlit-dashboard -n kafka-demo" -ForegroundColor White
Write-Host "kubectl logs -f deployment/kafka-to-postgres -n kafka-demo" -ForegroundColor White

Write-Host "`nTo cleanup everything:" -ForegroundColor Cyan
Write-Host "kubectl delete namespace kafka-demo" -ForegroundColor White

Write-Host "`n=== Deployment Script Completed ===" -ForegroundColor Green