# LMA Kubernetes Deployment

This directory contains Kubernetes manifests and deployment scripts for the Lead Management Automation Platform.

## Prerequisites

1. **Kubernetes Cluster**: You need access to a Kubernetes cluster. Options include:
   - Docker Desktop with Kubernetes enabled (recommended for local development)
   - Minikube
   - Cloud providers (EKS, GKE, AKS)

2. **kubectl**: Kubernetes command-line tool installed and configured

3. **Docker Images**: Build the Docker images first:
   ```bash
   # From the project root
   docker build -t lma-backend ./backend
   docker build -t lma-frontend ./frontend
   ```

## Quick Start

### Option 1: Using the PowerShell Script (Recommended)

```powershell
# Deploy the entire LMA stack
.\kubernetes\deploy.ps1 -Action deploy

# Check deployment status
.\kubernetes\deploy.ps1 -Action status

# View application logs
.\kubernetes\deploy.ps1 -Action logs

# Remove the deployment
.\kubernetes\deploy.ps1 -Action delete
```

### Option 2: Manual kubectl Commands

```bash
# Create namespace and configuration
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/storage.yaml

# Deploy services
kubectl apply -f kubernetes/backend-deployment.yaml
kubectl apply -f kubernetes/frontend-deployment.yaml

# Set up ingress
kubectl apply -f kubernetes/ingress.yaml

# Check status
kubectl get pods -n lma
kubectl get services -n lma
```

## Architecture

The Kubernetes deployment includes:

- **Namespace**: `lma` - Isolated environment for all LMA resources
- **Backend**: FastAPI application with 2 replicas, internal service
- **Frontend**: SvelteKit application with 2 replicas, LoadBalancer service
- **ConfigMaps**: Application configuration
- **Secrets**: Sensitive data (passwords, API keys)
- **Ingress**: HTTP routing and load balancing
- **Storage**: Persistent volumes for data

## Services

- **lma-backend-service**: Internal service for the FastAPI backend (port 8000)
- **lma-frontend-service**: LoadBalancer service for the SvelteKit frontend (port 3000)

## Configuration

### Environment Variables

Configuration is managed through ConfigMaps and Secrets:

- `lma-config`: Non-sensitive configuration
- `lma-secrets`: Sensitive data (base64 encoded)

### Scaling

To scale the deployment:

```bash
# Scale backend
kubectl scale deployment lma-backend --replicas=3 -n lma

# Scale frontend
kubectl scale deployment lma-frontend --replicas=3 -n lma
```

## Monitoring

Check pod health and logs:

```bash
# View all resources
kubectl get all -n lma

# Check pod details
kubectl describe pod <pod-name> -n lma

# View logs
kubectl logs -f deployment/lma-backend -n lma
kubectl logs -f deployment/lma-frontend -n lma
```

## Troubleshooting

### Common Issues

1. **Images not found**: Ensure Docker images are built and available
2. **Pods not starting**: Check resource constraints and image pull policies
3. **Service not accessible**: Verify service and ingress configurations

### Debug Commands

```bash
# Check cluster info
kubectl cluster-info

# Check node status
kubectl get nodes

# Describe problematic resources
kubectl describe pod <pod-name> -n lma
kubectl describe service <service-name> -n lma

# Get events
kubectl get events -n lma --sort-by='.lastTimestamp'
```

## Security Notes

- Secrets are base64 encoded but not encrypted by default
- For production, consider using external secret management
- Review and update resource limits based on actual usage
- Implement network policies for additional security

## Cloud Provider Specific Notes

### AWS EKS
- Use ALB Ingress Controller for better integration
- Consider using EFS for persistent storage

### Google GKE
- Use GKE Ingress for Google Cloud integration
- Consider using Google Cloud Storage for data

### Azure AKS
- Use Azure Application Gateway for ingress
- Consider using Azure Files for persistent storage
