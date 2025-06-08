#!/usr/bin/env pwsh
# Start Local N8N Development Environment
# This script sets up and starts the LMA system with local n8n workflows

Write-Host "🚀 Starting LMA Lead Management Analytics with Local N8N" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan

# Check if Docker is running
try {
    $dockerVersion = docker version --format '{{.Client.Version}}' 2>$null
    if (-not $dockerVersion) {
        throw "Docker not found"
    }
    Write-Host "✅ Docker is running (version: $dockerVersion)" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running or not installed. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Stop any existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down -v 2>$null

# Clean up any orphaned containers
Write-Host "🧹 Cleaning up orphaned containers..." -ForegroundColor Yellow
docker-compose down --remove-orphans 2>$null

# Pull latest images
Write-Host "📥 Pulling latest Docker images..." -ForegroundColor Yellow
docker-compose pull

# Build and start services
Write-Host "🔨 Building and starting services..." -ForegroundColor Yellow
docker-compose up -d --build

# Wait for services to be ready
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check service health
Write-Host "🔍 Checking service health..." -ForegroundColor Cyan

$services = @{
    "PostgreSQL" = "localhost:15432"
    "Redis" = "localhost:6379" 
    "Backend API" = "http://localhost:8000/health"
    "Frontend" = "http://localhost:15173"
    "N8N" = "http://localhost:5678"
    "Grafana" = "http://localhost:13001"
    "Prometheus" = "http://localhost:19090"
}

foreach ($service in $services.GetEnumerator()) {
    $name = $service.Key
    $endpoint = $service.Value
    
    try {
        if ($endpoint.StartsWith("http")) {
            $response = Invoke-WebRequest -Uri $endpoint -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ $name is running" -ForegroundColor Green
            } else {
                Write-Host "⚠️  $name responded with status: $($response.StatusCode)" -ForegroundColor Yellow
            }
        } else {
            # For non-HTTP services, just check if port is open
            $host, $port = $endpoint -split ":"
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $connected = $tcpClient.ConnectAsync($host, $port).Wait(3000)
            if ($connected) {
                Write-Host "✅ $name is running" -ForegroundColor Green
            } else {
                Write-Host "❌ $name is not responding" -ForegroundColor Red
            }
            $tcpClient.Close()
        }
    } catch {
        Write-Host "❌ $name is not responding" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🎉 LMA Development Environment Started!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔗 Service URLs:" -ForegroundColor Yellow
Write-Host "   Frontend:    http://localhost:15173" -ForegroundColor White
Write-Host "   Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "   N8N:         http://localhost:5678 (admin/admin123)" -ForegroundColor White
Write-Host "   Grafana:     http://localhost:13001 (admin/admin)" -ForegroundColor White
Write-Host "   Prometheus:  http://localhost:19090" -ForegroundColor White
Write-Host ""
Write-Host "📊 Database Info:" -ForegroundColor Yellow
Write-Host "   PostgreSQL:  localhost:15432" -ForegroundColor White
Write-Host "   Username:    lma_user" -ForegroundColor White
Write-Host "   Database:    lma_db" -ForegroundColor White
Write-Host "   N8N DB:      n8n_db" -ForegroundColor White
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Open N8N: http://localhost:5678" -ForegroundColor White
Write-Host "   2. Import workflow: n8n-workflows/Lead_Scoring_CORRECTED.json" -ForegroundColor White
Write-Host "   3. Test workflows: cd tests && python test_complete_workflow.py" -ForegroundColor White
Write-Host "   4. Open frontend: http://localhost:15173" -ForegroundColor White
Write-Host ""
Write-Host "🛠️  Commands:" -ForegroundColor Yellow
Write-Host "   View logs:   docker-compose logs -f [service_name]" -ForegroundColor White
Write-Host "   Stop all:    docker-compose down" -ForegroundColor White
Write-Host "   Restart:     docker-compose restart [service_name]" -ForegroundColor White
Write-Host ""
Write-Host "✨ Happy developing!" -ForegroundColor Green 