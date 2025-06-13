# Lead Management Application - Backend

## Project Structure

```
backend/
├── app/                    # Main application package
│   ├── api/               # API layer
│   │   └── v1/           # API version 1
│   │       ├── __init__.py
│   │       ├── organizations.py
│   │       ├── users.py
│   │       ├── leads.py
│   │       ├── campaigns.py
│   │       ├── activities.py
│   │       ├── workflows.py
│   │       ├── lead_scoring.py
│   │       └── integrations.py
│   ├── core/             # Core application logic
│   │   ├── __init__.py
│   │   └── config.py
│   ├── db/               # Database layer
│   │   ├── __init__.py
│   │   ├── database.py   # Database connection
│   │   ├── models.py     # SQLAlchemy models
│   │   └── schemas.py    # Pydantic schemas
│   └── tests/            # Test files
│       ├── __init__.py
│       └── pytest.ini
├── scripts/              # Utility scripts
│   └── init_db.py       # Database initialization
├── legacy/               # Legacy/old files (for reference)
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
└── Dockerfile          # Docker configuration
```

## Database Schema

Based on the simplified ER diagram with:

### Core Entities
- **Organizations**: Main organization entity
- **Users**: User management with roles
- **Leads**: Lead management and tracking
- **Campaigns**: Marketing campaign management

### Unified Systems
- **Activities**: Unified activity tracking (emails, calls, meetings, notes)
- **Workflows**: Simplified workflow system with JSON steps
- **Lead Scoring Rules**: Lead scoring with flexible conditions

### Junction Tables
- **Campaign Leads**: Many-to-many relationship between campaigns and leads

### Integration
- **Integrations**: External service configurations

## Getting Started

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Run development server
uvicorn main:app --host 0.0.0.0 --port 18000 --reload
```

### Docker
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:18000/docs
- ReDoc: http://localhost:18000/redoc

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `ENVIRONMENT`: development/production
- `PORT`: Server port (default: 8000) 