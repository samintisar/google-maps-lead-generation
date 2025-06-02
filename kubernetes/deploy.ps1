#!/usr/bin/env pwsh

# LMA Kubernetes Deployment Script
# This script deploys the Lead Management Automation Platform to Kubernetes

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("deploy", "delete", "status", "logs")]
    [string]$Action = "deploy",
    
    [Parameter(Mandatory=$false)]
    [string]$Namespace = "lma"
)

Write-Host "LMA Kubernetes Deployment Script" -ForegroundColor Green
Write-Host "Action: $Action" -ForegroundColor Cyan
Write-Host "Namespace: $Namespace" -ForegroundColor Cyan
Write-Host ""

function Test-KubernetesConnection {
    try {
        kubectl cluster-info | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Deploy-LMA {
    Write-Host "Deploying LMA to Kubernetes..." -ForegroundColor Yellow
    
    # Check if Kubernetes is available
    if (-not (Test-KubernetesConnection)) {
        Write-Host "Error: Cannot connect to Kubernetes cluster." -ForegroundColor Red
        Write-Host "Please ensure Docker Desktop Kubernetes is enabled or minikube is running." -ForegroundColor Red
        exit 1
    }
    
    # Apply Kubernetes manifests in order
    Write-Host "Creating namespace and configuration..." -ForegroundColor Cyan
    kubectl apply -f kubernetes/namespace.yaml
    kubectl apply -f kubernetes/secrets.yaml
    kubectl apply -f kubernetes/storage.yaml
    
    Write-Host "Deploying backend service..." -ForegroundColor Cyan
    kubectl apply -f kubernetes/backend-deployment.yaml
    
    Write-Host "Deploying frontend service..." -ForegroundColor Cyan
    kubectl apply -f kubernetes/frontend-deployment.yaml
    
    Write-Host "Setting up ingress..." -ForegroundColor Cyan
    kubectl apply -f kubernetes/ingress.yaml
    
    Write-Host ""
    Write-Host "Deployment complete! Waiting for pods to be ready..." -ForegroundColor Green
    kubectl wait --for=condition=ready pod -l app=lma-backend -n $Namespace --timeout=300s
    kubectl wait --for=condition=ready pod -l app=lma-frontend -n $Namespace --timeout=300s
    
    Write-Host ""
    Write-Host "Getting service information..." -ForegroundColor Green
    kubectl get services -n $Namespace
}

function Remove-LMA {
    Write-Host "Removing LMA from Kubernetes..." -ForegroundColor Yellow
    
    kubectl delete -f kubernetes/ingress.yaml --ignore-not-found=true
    kubectl delete -f kubernetes/frontend-deployment.yaml --ignore-not-found=true
    kubectl delete -f kubernetes/backend-deployment.yaml --ignore-not-found=true
    kubectl delete -f kubernetes/storage.yaml --ignore-not-found=true
    kubectl delete -f kubernetes/secrets.yaml --ignore-not-found=true
    kubectl delete -f kubernetes/namespace.yaml --ignore-not-found=true
    
    Write-Host "LMA removed from Kubernetes." -ForegroundColor Green
}

function Get-LMAStatus {
    Write-Host "LMA Kubernetes Status:" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Namespace:" -ForegroundColor Cyan
    kubectl get namespace $Namespace 2>$null
    
    Write-Host ""
    Write-Host "Pods:" -ForegroundColor Cyan
    kubectl get pods -n $Namespace 2>$null
    
    Write-Host ""
    Write-Host "Services:" -ForegroundColor Cyan
    kubectl get services -n $Namespace 2>$null
    
    Write-Host ""
    Write-Host "Ingress:" -ForegroundColor Cyan
    kubectl get ingress -n $Namespace 2>$null
}

function Get-LMALogs {
    Write-Host "LMA Application Logs:" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Backend logs:" -ForegroundColor Cyan
    kubectl logs -l app=lma-backend -n $Namespace --tail=20
    
    Write-Host ""
    Write-Host "Frontend logs:" -ForegroundColor Cyan
    kubectl logs -l app=lma-frontend -n $Namespace --tail=20
}

# Main execution
switch ($Action) {
    "deploy" { Deploy-LMA }
    "delete" { Remove-LMA }
    "status" { Get-LMAStatus }
    "logs" { Get-LMALogs }
    default { 
        Write-Host "Invalid action: $Action" -ForegroundColor Red
        Write-Host "Valid actions: deploy, delete, status, logs" -ForegroundColor Yellow
    }
}
