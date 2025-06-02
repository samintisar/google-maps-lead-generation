# LMA Platform Deployment Script (PowerShell)
# This script automates the deployment of the Lead Management Automation platform

param(
    [Parameter(Position = 0)]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "development",
    
    [switch]$Build,
    [switch]$Pull,
    [switch]$Backup,
    [switch]$Rollback,
    [switch]$HealthCheck,
    [switch]$Help
)

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$ComposeFile = "docker-compose.yml"

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    Gray = "Gray"
}

# Logging functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

# Help function
function Show-Help {
    @"
LMA Platform Deployment Script (PowerShell)

Usage: .\deploy.ps1 [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
    development    Deploy for development (default)
    staging        Deploy for staging environment
    production     Deploy for production environment

OPTIONS:
    -Build         Force rebuild of Docker images
    -Pull          Pull latest images before deployment
    -Backup        Create database backup before deployment
    -Rollback      Rollback to previous deployment
    -HealthCheck   Perform health check after deployment
    -Help          Show this help message

Examples:
    .\deploy.ps1 development
    .\deploy.ps1 production -Build -Backup -HealthCheck
    .\deploy.ps1 staging -Pull

"@
}

# Show help if requested
if ($Help) {
    Show-Help
    exit 0
}

# Set compose file based on environment
switch ($Environment) {
    "production" {
        $ComposeFile = "docker-compose.prod.yml"
    }
    "staging" {
        $ComposeFile = "docker-compose.yml"
        $EnvFile = ".env.staging"
    }
    "development" {
        $ComposeFile = "docker-compose.yml"
        $EnvFile = ".env"
    }
}

Write-Info "Deploying LMA Platform for $Environment environment"

# Change to project root
Set-Location $ProjectRoot

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Error "Docker is not running. Please start Docker and try again."
    exit 1
}

# Check if docker-compose file exists
if (-not (Test-Path $ComposeFile)) {
    Write-Error "Docker compose file $ComposeFile not found"
    exit 1
}

# Create environment file if it doesn't exist
if (-not (Test-Path ".env") -and $Environment -eq "development") {
    Write-Warning "Environment file not found. Creating from example..."
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Info "Created .env from .env.example"
    } else {
        Write-Error "No .env.example file found. Please create .env manually."
        exit 1
    }
}

# Backup database if requested
if ($Backup) {
    Write-Info "Creating database backup..."
    $BackupDir = "backups\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    
    # Create PostgreSQL backup
    docker-compose -f $ComposeFile exec -T postgres pg_dump -U lma_user lma_db | Out-File "$BackupDir\lma_db_backup.sql"
    docker-compose -f $ComposeFile exec -T postgres pg_dump -U lma_user n8n_db | Out-File "$BackupDir\n8n_db_backup.sql"
    
    Write-Success "Database backup created in $BackupDir"
}

# Rollback if requested
if ($Rollback) {
    Write-Info "Rolling back to previous deployment..."
    
    # Stop current containers
    docker-compose -f $ComposeFile down
    
    # Find latest backup
    $LatestBackup = Get-ChildItem "backups" | Sort-Object CreationTime -Descending | Select-Object -First 1
    if ($LatestBackup) {
        Write-Info "Restoring from backup: $($LatestBackup.Name)"
        
        # Start database containers
        docker-compose -f $ComposeFile up -d postgres redis
        Start-Sleep 10
        
        # Restore databases
        Get-Content "backups\$($LatestBackup.Name)\lma_db_backup.sql" | docker-compose -f $ComposeFile exec -T postgres psql -U lma_user -d lma_db
        Get-Content "backups\$($LatestBackup.Name)\n8n_db_backup.sql" | docker-compose -f $ComposeFile exec -T postgres psql -U lma_user -d n8n_db
        
        Write-Success "Rollback completed"
    } else {
        Write-Error "No backup found for rollback"
        exit 1
    }
    exit 0
}

# Pull latest images if requested
if ($Pull) {
    Write-Info "Pulling latest images..."
    docker-compose -f $ComposeFile pull
}

# Stop existing containers gracefully
Write-Info "Stopping existing containers..."
docker-compose -f $ComposeFile down --remove-orphans

# Build and start containers
Write-Info "Starting LMA Platform containers..."
if ($Build) {
    Write-Info "Building images..."
    docker-compose -f $ComposeFile up -d --build
} else {
    docker-compose -f $ComposeFile up -d
}

# Wait for services to be ready
Write-Info "Waiting for services to start..."
Start-Sleep 30

# Health check if requested
if ($HealthCheck) {
    Write-Info "Performing health checks..."
    
    # Check PostgreSQL
    try {
        docker-compose -f $ComposeFile exec -T postgres pg_isready -U lma_user -d lma_db | Out-Null
        Write-Success "PostgreSQL is healthy"
    } catch {
        Write-Error "PostgreSQL health check failed"
        exit 1
    }
    
    # Check Redis
    try {
        docker-compose -f $ComposeFile exec -T redis redis-cli ping | Out-Null
        Write-Success "Redis is healthy"
    } catch {
        Write-Error "Redis health check failed"
        exit 1
    }
    
    # Check backend API
    try {
        Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Out-Null
        Write-Success "Backend API is healthy"
    } catch {
        Write-Error "Backend API health check failed"
        exit 1
    }
    
    # Check frontend
    try {
        Invoke-WebRequest -Uri "http://localhost:3000" -Method Head -UseBasicParsing | Out-Null
        Write-Success "Frontend is accessible"
    } catch {
        Write-Warning "Frontend health check failed (may still be starting)"
    }
    
    # Check n8n
    try {
        Invoke-WebRequest -Uri "http://localhost:5678" -UseBasicParsing | Out-Null
        Write-Success "n8n workflow engine is accessible"
    } catch {
        Write-Warning "n8n health check failed (may still be starting)"
    }
}

# Show container status
Write-Info "Container status:"
docker-compose -f $ComposeFile ps

# Show access URLs
Write-Host ""
Write-Success "LMA Platform deployed successfully!"
Write-Host ""
Write-Host "Access URLs:"
Write-Host "  Frontend:    http://localhost:3000"
Write-Host "  Backend API: http://localhost:8000"
Write-Host "  n8n:         http://localhost:5678"
Write-Host "  API Docs:    http://localhost:8000/docs"
Write-Host ""

# Show useful commands
Write-Host "Useful commands:"
Write-Host "  View logs:     docker-compose -f $ComposeFile logs -f"
Write-Host "  Stop all:      docker-compose -f $ComposeFile down"
Write-Host "  Restart:       docker-compose -f $ComposeFile restart"
Write-Host "  Shell access:  docker-compose -f $ComposeFile exec [service] bash"
Write-Host ""

Write-Success "Deployment completed!" 