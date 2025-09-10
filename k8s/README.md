# Kubernetes Deployment Guide

## Prerequisites
- Kubernetes cluster running locally (Docker Desktop with Kubernetes enabled, minikube, etc.)
- kubectl configured to point to your local cluster
- Docker installed for building the application image

## Important Notes

- **Single Docker Image**: All services (kafka-producer, kafka-to-postgres, streamlit-dashboard) use the same Docker image `streamlit-kafka-app:latest` built from the single Dockerfile
- **Different Commands**: Each service runs different Python scripts using the `args` parameter in Kubernetes (equivalent to Docker Compose's `command` override)
- **Entrypoint Script**: The Docker image uses `/app/docker-entrypoint.sh` which waits for Kafka to be ready before starting the application

## Step 1: Build the Application Image

**IMPORTANT**: The Kubernetes deployments for kafka-producer, kafka-to-postgres, and streamlit-dashboard all depend on a custom Docker image that needs to be built first.

```bash
# Build the image (run this from the project root directory)
docker build -t streamlit-kafka-app:latest .

# Verify the image was built successfully
docker images | grep streamlit-kafka-app
```

### For Different Kubernetes Environments:

**Docker Desktop with Kubernetes:**
```bash
# Image should be automatically available to Kubernetes
# No additional steps needed
```

**Minikube:**
```bash
# Load the image into minikube's Docker daemon
minikube image load streamlit-kafka-app:latest

# Verify the image is loaded
minikube image ls | grep streamlit-kafka-app
```

**Kind (Kubernetes in Docker):**
```bash
# Load the image into kind cluster
kind load docker-image streamlit-kafka-app:latest

# If using a specific cluster name
kind load docker-image streamlit-kafka-app:latest --name <cluster-name>
```

**Other Local Kubernetes:**
```bash
# You may need to push to a local registry or use the appropriate method
# for your specific Kubernetes setup
```

## Step 2: Deploy to Kubernetes

Deploy in the following order to ensure dependencies are met:

```bash
# Make sure kubectl is pointing to your local cluster
kubectl config current-context

# Apply all the manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/storage.yaml
kubectl apply -f k8s/zookeeper.yaml

# Wait for ZooKeeper to be ready
kubectl wait --for=condition=available --timeout=300s deployment/zookeeper -n kafka-demo

# Deploy Kafka
kubectl apply -f k8s/kafka.yaml

# Wait for Kafka to be ready
kubectl wait --for=condition=available --timeout=300s deployment/kafka -n kafka-demo

# Deploy PostgreSQL
kubectl apply -f k8s/postgres.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n kafka-demo

# Deploy the applications
kubectl apply -f k8s/kafka-producer.yaml
kubectl apply -f k8s/kafka-to-postgres.yaml
kubectl apply -f k8s/streamlit.yaml
kubectl apply -f k8s/kafka-ui.yaml
```

## Step 3: Access Your Applications

```bash
# Check if all pods are running
kubectl get pods -n kafka-demo

# Access applications via NodePort services:
# Streamlit Dashboard: http://localhost:30001
# Kafka UI: http://localhost:30002

# Alternative: Use port forwarding
kubectl port-forward service/streamlit-service 8501:8501 -n kafka-demo
kubectl port-forward service/kafka-ui-service 8080:8080 -n kafka-demo
```

## Step 4: Monitor and Debug

```bash
# Check pod status
kubectl get pods -n kafka-demo

# Check logs for specific services
kubectl logs -f deployment/kafka-producer -n kafka-demo
kubectl logs -f deployment/streamlit-dashboard -n kafka-demo
kubectl logs -f deployment/kafka-to-postgres -n kafka-demo

# Check services
kubectl get services -n kafka-demo

# Describe a problematic pod
kubectl describe pod <pod-name> -n kafka-demo
```

## Cleanup

```bash
# Delete everything
kubectl delete namespace kafka-demo

# Or delete individual components
kubectl delete -f k8s/
```

## Troubleshooting

1. **ImagePullBackOff errors for kafka-producer, kafka-to-postgres, or streamlit-dashboard**: 
   - This means the `streamlit-kafka-app:latest` image wasn't built or isn't available to Kubernetes
   - Solution: Make sure you've built the Docker image first:
   ```bash
   docker build -t streamlit-kafka-app:latest .
   docker images | grep streamlit-kafka-app
   ```
   - For minikube users, load the image:
   ```bash
   minikube image load streamlit-kafka-app:latest
   ```
   - Then restart the failed deployments:
   ```bash
   kubectl rollout restart deployment/kafka-producer -n kafka-demo
   kubectl rollout restart deployment/kafka-to-postgres -n kafka-demo
   kubectl rollout restart deployment/streamlit-dashboard -n kafka-demo
   ```
   - Or reapply the updated configurations:
   ```bash
   kubectl apply -f k8s/kafka-producer.yaml
   kubectl apply -f k8s/kafka-to-postgres.yaml
   kubectl apply -f k8s/streamlit.yaml
   ```

2. **Pods stuck in Pending state**: Check if PersistentVolumes are correctly created
   ```bash
   kubectl get pv
   kubectl get pvc -n kafka-demo
   ```

3. **Services not accessible**: Verify NodePort services are created
   ```bash
   kubectl get services -n kafka-demo
   ```

4. **Application crashes**: Check logs and ensure the Docker image was built correctly
   ```bash
   kubectl logs <pod-name> -n kafka-demo
   ```

5. **Image pull errors**: Make sure the image is available in your local registry
   ```bash
   docker images | grep streamlit-kafka-app
   ```
