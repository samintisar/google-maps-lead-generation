# Lead Management Application - Backend

A modern, clean, and well-organized FastAPI backend for lead management with AI-powered enrichment capabilities.

## 🏗️ Architecture Overview

The backend follows a clean, modular architecture with clear separation of concerns:

```
backend/
├── app/                    # Main application package
│   ├── api/               # API layer (routers and endpoints)
│   │   └── v1/           # API version 1
│   │       ├── leads.py      # Lead management endpoints
│   │       ├── organizations.py
│   │       ├── users.py
│   │       └── campaigns.py
│   ├── core/             # Core application logic
│   │   ├── config.py         # Configuration management
│   │   └── logging.py        # Centralized logging
│   ├── db/               # Database layer
│   │   ├── database.py       # Database connection & session
│   │   ├── models.py         # SQLAlchemy models
│   │   └── schemas.py        # Pydantic schemas
│   ├── domains/          # Domain-driven design modules
│   │   └── lead_management/  # Lead domain
│   │       ├── models.py     # Lead-specific models
│   │       └── schemas.py    # Lead-specific schemas
│   └── shared/           # Shared utilities and services
├── dev-tools/            # Development and debugging tools
│   ├── dev_server.py         # Unified development server
│   └── [legacy test files]   # Moved from root
├── migrations/           # Database migrations
├── scripts/              # Utility scripts
│   └── init_db.py           # Database initialization
├── main.py              # FastAPI application entry point
├── Makefile             # Development commands
├── requirements.txt     # Python dependencies
└── Dockerfile          # Docker configuration
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- **PostgreSQL Database (Neon)**

### Development Setup

1. **Install dependencies:**
   ```bash
   make install
   # or
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   # Create .env file in project root with your Neon database URL
   DATABASE_URL=postgresql://username:password@host/database?sslmode=require
   ```

3. **Start development server:**
   ```bash
   make dev
   # or
   python dev-tools/dev_server.py server
   ```

4. **Access the API:**
   - API Documentation: http://localhost:18000/docs
   - Alternative Docs: http://localhost:18000/redoc
   - Health Check: http://localhost:18000/api/health

## 🛠️ Development Tools

### Development Commands

The backend includes comprehensive development tools for both Unix/Linux and Windows:

**For Unix/Linux/macOS (Makefile):**
```bash
# Setup & Installation
make install     # Install dependencies
make clean       # Clean up cache and temporary files

# Development
make dev         # Start development server with auto-reload
make run-prod    # Start production server
make test        # Run endpoint tests
make check-db    # Check database status
make full-test   # Run comprehensive test suite

# Code Quality
make lint        # Run linting checks
make format      # Format code with black

# Docker
make docker-build # Build Docker image
make docker-run   # Run Docker container

# Quick workflows
make quick-start  # clean + install + dev
make ci          # clean + install + lint + test
```

**For Windows (PowerShell):**
```powershell
# Setup & Installation
.\dev.ps1 install     # Install dependencies
.\dev.ps1 clean       # Clean up cache and temporary files

# Development
.\dev.ps1 dev         # Start development server with auto-reload
.\dev.ps1 run-prod    # Start production server
.\dev.ps1 test        # Run endpoint tests
.\dev.ps1 check-db    # Check database status
.\dev.ps1 full-test   # Run comprehensive test suite

# Code Quality
.\dev.ps1 lint        # Run linting checks
.\dev.ps1 format      # Format code with black

# Docker
.\dev.ps1 docker-build # Build Docker image
.\dev.ps1 docker-run   # Run Docker container

# Quick workflows
.\dev.ps1 quick-start  # clean + install + dev
.\dev.ps1 ci          # clean + install + lint + test
```

### Development Server Script

The `dev-tools/dev_server.py` script provides a unified interface for development tasks:

```bash
# Start development server
python dev-tools/dev_server.py server

# Test all endpoints
python dev-tools/dev_server.py test

# Check database status
python dev-tools/dev_server.py db-check

# Run comprehensive tests
python dev-tools/dev_server.py full-test
```

## 📊 Database Schema

### Core Entities

- **Organizations**: Main organization entity
- **Users**: User management with roles (authentication disabled)
- **Leads**: Lead management and tracking with enrichment fields
- **Campaigns**: Marketing campaign management

### Lead Enrichment Fields

The Lead model includes comprehensive enrichment capabilities:

```python
# Social Media Profiles
linkedin_profile: Optional[str]
twitter_profile: Optional[str]
facebook_profile: Optional[str]
instagram_profile: Optional[str]

# Business Intelligence
ideal_customer_profile: Optional[str]
pain_points: Optional[str]
key_goals: Optional[str]
company_description: Optional[str]
recent_news: Optional[str]
key_personnel: Optional[str]  # JSONB field for PostgreSQL

# Enrichment Metadata
enrichment_status: Optional[str]  # pending, completed, failed
enriched_at: Optional[datetime]
enrichment_confidence: Optional[float]  # 0.0 - 1.0
```

## 🔌 API Endpoints

### Core Endpoints

- `GET /` - Root endpoint with application info
- `GET /api/health` - Health check for monitoring

### Lead Management

- `GET /api/leads/` - List leads with filtering and pagination
- `GET /api/leads/{id}` - Get specific lead details
- `POST /api/leads/` - Create new lead
- `PUT /api/leads/{id}` - Update lead
- `DELETE /api/leads/{id}` - Delete lead
- `PATCH /api/leads/{id}/status` - Update lead status only

### Lead Enrichment

- `POST /api/leads/{id}/enrich` - Start lead enrichment process
- `GET /api/leads/{id}/enrichment-status` - Check enrichment status

### Query Parameters (GET /api/leads/)

- `skip`: Number of records to skip (pagination)
- `limit`: Maximum records to return (1-1000)
- `status`: Filter by lead status
- `source`: Filter by lead source
- `search`: Search in name, email, or company

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database (REQUIRED - PostgreSQL/Neon only)
DATABASE_URL=postgresql://username:password@host/database?sslmode=require

# API Keys (optional)
PERPLEXITY_API_KEY=your_perplexity_key
OPENAI_API_KEY=your_openai_key

# Application Settings (optional)
ENVIRONMENT=development
DEBUG=true
PORT=18000
LOG_LEVEL=INFO
```

### Configuration Management

The application uses a centralized configuration system in `app/core/config.py`:

- Environment variable support with validation
- Type validation with Pydantic
- Cached settings for performance
- PostgreSQL-only database support
- Development-friendly defaults

## 🔍 Logging

Centralized logging configuration in `app/core/logging.py`:

- Structured logging format
- Configurable log levels
- Reduced noise from SQLAlchemy and Uvicorn
- Environment-specific settings

## 🧪 Testing

### Automated Testing

```bash
# Test all endpoints
make test

# Check database connectivity
make check-db

# Run comprehensive test suite
make full-test
```

### Manual Testing

The development server script provides detailed endpoint testing:

```bash
python dev-tools/dev_server.py test
```

Output includes:
- ✅/❌ Status for each endpoint
- HTTP status codes
- Response sizes
- Error details if any

## 🐳 Docker Support

### Build and Run

```bash
# Build image
make docker-build

# Run container
make docker-run

# Or use Docker directly
docker build -t lma-backend .
docker run -p 18000:18000 lma-backend
```

### Docker Compose

The backend integrates with the main docker-compose.yml:

```yaml
backend:
  build: ./backend
  ports:
    - "18000:18000"
  environment:
    - DATABASE_URL=${DATABASE_URL}
    - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
```

## 🔧 Development Guidelines

### Code Organization

- **Routers**: Keep endpoint logic in `app/api/v1/`
- **Models**: Database models in `app/domains/*/models.py`
- **Schemas**: Pydantic schemas in `app/domains/*/schemas.py`
- **Services**: Business logic in `app/shared/services/`
- **Config**: Centralized in `app/core/config.py`

### Error Handling

- Use HTTPException for API errors
- Log errors with appropriate levels
- Return consistent error responses
- Include helpful error messages

### Logging Best Practices

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Use appropriate log levels
logger.info("Operation completed successfully")
logger.warning("Potential issue detected")
logger.error("Error occurred", exc_info=True)
```

## 🚀 Production Deployment

### Environment Setup

1. Set `ENVIRONMENT=production` in `.env`
2. Set `DEBUG=false`
3. Configure proper `DATABASE_URL` (PostgreSQL/Neon)
4. Set up API keys for enrichment services

### Running in Production

```bash
# Using the development script
python dev-tools/dev_server.py server --no-reload

# Or directly with uvicorn
uvicorn main:app --host 0.0.0.0 --port 18000 --workers 4
```

## 📈 Performance Considerations

- Database connection pooling configured for PostgreSQL
- Efficient query patterns with SQLAlchemy
- Pagination for large datasets
- Caching for configuration settings
- Optimized logging levels for production
- JSONB indexing for enrichment data

## 🔒 Security Notes

- CORS properly configured for frontend origins
- Input validation with Pydantic schemas
- SQL injection protection via SQLAlchemy ORM
- Environment variable protection for secrets
- SSL/TLS enforced for database connections

## 🤝 Contributing

1. Follow the established code organization
2. Use the provided development tools
3. Run tests before committing
4. Update documentation for new features
5. Follow logging and error handling patterns

## 📝 API Documentation

Once the server is running, comprehensive API documentation is available at:

- **Swagger UI**: http://localhost:18000/docs
- **ReDoc**: http://localhost:18000/redoc

These provide interactive documentation with request/response examples and the ability to test endpoints directly.

---

## 🔄 Recent Optimizations

This backend has been recently cleaned up and optimized with:

- ✅ Organized file structure with clear separation of concerns
- ✅ Centralized configuration and logging
- ✅ Comprehensive development tools and scripts
- ✅ Proper error handling and logging throughout
- ✅ Clean, well-documented API endpoints
- ✅ Efficient PostgreSQL database operations
- ✅ Development-friendly tooling and automation
- ✅ Production-ready configuration options
- ✅ **PostgreSQL-only database support (no SQLite fallback)**

The codebase is now much more maintainable, debuggable, and ready for further development with rock-solid PostgreSQL/Neon integration. 