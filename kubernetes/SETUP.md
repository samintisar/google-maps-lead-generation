# Kubernetes Cluster Setup Guide

This guide provides instructions for setting up a Kubernetes cluster for the LMA Platform.

## Option 1: Docker Desktop Kubernetes (Recommended for Development)

### Windows with Docker Desktop

1. **Enable Kubernetes in Docker Desktop:**
   - Open Docker Desktop
   - Go to Settings → Kubernetes
   - Check "Enable Kubernetes"
   - Click "Apply & Restart"
   - Wait for Kubernetes to start (green indicator)

2. **Verify Installation:**
   ```powershell
   kubectl cluster-info
   kubectl get nodes
   ```

3. **Deploy LMA:**
   ```powershell
   .\kubernetes\deploy.ps1 -Action deploy
   ```

## Option 2: Minikube (Local Development)

### Install Minikube

1. **Install Minikube:**
   ```powershell
   # Using Chocolatey
   choco install minikube

   # Or download from: https://minikube.sigs.k8s.io/docs/start/
   ```

2. **Start Minikube:**
   ```powershell
   minikube start --driver=docker
   ```

3. **Verify Installation:**
   ```powershell
   kubectl cluster-info
   minikube status
   ```

4. **Deploy LMA:**
   ```powershell
   .\kubernetes\deploy.ps1 -Action deploy
   ```

5. **Access Services:**
   ```powershell
   # Get service URL
   minikube service lma-frontend-service -n lma --url
   ```

## Option 3: Cloud Providers

### AWS EKS

1. **Prerequisites:**
   - AWS CLI configured
   - eksctl installed

2. **Create Cluster:**
   ```bash
   eksctl create cluster --name lma-cluster --region us-west-2 --nodegroup-name standard-workers --node-type t3.medium --nodes 3
   ```

3. **Configure kubectl:**
   ```bash
   aws eks update-kubeconfig --region us-west-2 --name lma-cluster
   ```

### Google GKE

1. **Prerequisites:**
   - Google Cloud SDK installed
   - gcloud configured

2. **Create Cluster:**
   ```bash
   gcloud container clusters create lma-cluster --num-nodes=3 --machine-type=e2-medium
   ```

3. **Configure kubectl:**
   ```bash
   gcloud container clusters get-credentials lma-cluster
   ```

### Azure AKS

1. **Prerequisites:**
   - Azure CLI installed
   - Azure subscription

2. **Create Cluster:**
   ```bash
   az aks create --resource-group myResourceGroup --name lma-cluster --node-count 3 --enable-addons monitoring --generate-ssh-keys
   ```

3. **Configure kubectl:**
   ```bash
   az aks get-credentials --resource-group myResourceGroup --name lma-cluster
   ```

## Post-Installation Steps

1. **Verify Cluster:**
   ```powershell
   kubectl cluster-info
   kubectl get nodes
   ```

2. **Install NGINX Ingress Controller (if needed):**
   ```powershell
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
   ```

3. **Deploy LMA Platform:**
   ```powershell
   .\kubernetes\deploy.ps1 -Action deploy
   ```

4. **Check Deployment:**
   ```powershell
   .\kubernetes\deploy.ps1 -Action status
   ```

## Troubleshooting

### Common Issues

1. **Docker Desktop Kubernetes not starting:**
   - Restart Docker Desktop
   - Reset Kubernetes cluster in settings
   - Ensure sufficient system resources

2. **kubectl not found:**
   - Install kubectl: `choco install kubernetes-cli`
   - Or enable it in Docker Desktop settings

3. **Images not available in cluster:**
   - For Minikube: `eval $(minikube docker-env)` then rebuild images
   - For cloud: Push images to container registry

### Resource Requirements

- **Minimum**: 2 CPU cores, 4GB RAM
- **Recommended**: 4 CPU cores, 8GB RAM
- **Storage**: 10GB available disk space

## Next Steps

Once your Kubernetes cluster is running:

1. Build and deploy the LMA platform
2. Set up monitoring (Prometheus/Grafana)
3. Configure CI/CD pipeline
4. Set up persistent storage for production data
