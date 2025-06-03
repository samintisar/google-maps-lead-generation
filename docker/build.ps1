# Build all Docker images for the LMA Platform

param(
    [string]$Target = "development",
    [switch]$NoBuild,
    [switch]$Clean
)

Write-Host "Building Lead Management Automation Platform - Docker Images" -ForegroundColor Green
Write-Host "Target: $Target" -ForegroundColor Yellow

# Clean up if requested
if ($Clean) {
    Write-Host "Cleaning up existing containers and images..." -ForegroundColor Yellow
    docker-compose down --volumes --remove-orphans
    docker system prune -f
}

# Set compose file based on target
$ComposeFile = if ($Target -eq "production") { "docker-compose.prod.yml" } else { "docker-compose.yml" }

Write-Host "Using compose file: $ComposeFile" -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please update .env file with your configuration before running again." -ForegroundColor Red
    exit 1
}

# Build images if not skipped
if (-not $NoBuild) {
    Write-Host "Building Docker images..." -ForegroundColor Cyan
    docker-compose -f $ComposeFile build --no-cache
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker build failed!" -ForegroundColor Red
        exit 1
    }
}

# Start services
Write-Host "Starting services..." -ForegroundColor Cyan
docker-compose -f $ComposeFile up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully started LMA Platform!" -ForegroundColor Green
    Write-Host "Services available at:" -ForegroundColor Cyan
    Write-Host "  - Frontend: http://localhost:5173 (dev) / http://localhost:5174 (prod)" -ForegroundColor White
    Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
    Write-Host "  - n8n: http://localhost:5678" -ForegroundColor White
    Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
    
    Write-Host "`nTo view logs: docker-compose -f $ComposeFile logs -f" -ForegroundColor Yellow
    Write-Host "To stop: docker-compose -f $ComposeFile down" -ForegroundColor Yellow
} else {
    Write-Host "Failed to start services!" -ForegroundColor Red
    exit 1
}
