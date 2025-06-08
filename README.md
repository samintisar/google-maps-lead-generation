# LMA - Lead Management Analytics

A comprehensive lead management and analytics platform with automated workflow capabilities using FastAPI, SvelteKit, PostgreSQL, and n8n.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for testing)
- Node.js 18+ (for frontend development)

### Start Development Environment

```bash
# Windows PowerShell
.\scripts\start-local-n8n.ps1

# Or manually with Docker Compose
docker-compose up -d --build
```

## 🔗 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:15173 | test@example.com / testpassword123 |
| **Backend API** | http://localhost:8000 | - |
| **N8N Workflows** | http://localhost:5678 | admin / admin123 |
| **Grafana** | http://localhost:13001 | admin / admin |
| **Prometheus** | http://localhost:19090 | - |

## 📊 Database Access

- **PostgreSQL**: localhost:15432
- **Username**: lma_user
- **Password**: lma_password
- **Main Database**: lma_db
- **N8N Database**: n8n_db

## 🔧 Project Structure

```
lma/
├── backend/                 # FastAPI Python backend
├── frontend/               # SvelteKit frontend
├── n8n-workflows/         # N8N workflow definitions
├── tests/                 # Test scripts
├── scripts/               # Deployment and utility scripts
├── monitoring/            # Grafana, Prometheus configs
└── docker-compose.yml     # Local development setup
```

## 🤖 N8N Workflows

### Setting Up Workflows

1. Open N8N: http://localhost:5678
2. Login with: admin / admin123
3. Import workflow: `n8n-workflows/Lead_Scoring_CORRECTED.json`
4. Activate the workflow

### Available Workflows

- **Lead Scoring**: Automated lead scoring with temperature classification
- **Social Outreach**: LinkedIn and email outreach automation
- **CRM Sync**: Synchronization with external CRM systems

## 🧪 Testing

### Run API Tests
```bash
cd tests
python test_complete_workflow.py
```

### Test N8N Workflows
```bash
cd tests
python test_n8n_webhook_endpoints.py
```

### Create Test Data
```bash
cd scripts/test-data
python create_test_leads_for_scoring.py
```

## 📈 Lead Scoring System

The system automatically scores leads based on:

- **Demographic** (0-25 points): Job title, seniority level
- **Firmographic** (0-25 points): Company size, industry
- **Behavioral** (0-30 points): Website visits, page views
- **Engagement** (0-20 points): Email opens, clicks, downloads
- **Temporal** (0-10 points): Recent activity bonus

### Lead Temperature Classification

- **Hot** (80-100): Immediate sales contact required
- **Warm** (60-79): Personalized follow-up needed
- **Cold** (40-59): Nurturing sequence recommended
- **Frozen** (<40): Re-engagement campaign needed

## 🔄 Workflow Endpoints

### Working Endpoints (7/11)
- `POST /api/workflows/leads/create` - Create new leads
- `POST /api/workflows/leads/{id}/update-status` - Update lead status
- `GET /api/workflows/leads/social-outreach` - Get leads for outreach
- `POST /api/workflows/leads/{id}/social-outreach` - Log outreach activity
- `GET /api/workflows/leads/crm-sync` - Get leads for CRM sync
- `POST /api/workflows/leads/crm-sync` - Sync leads to CRM
- `GET /api/leads/dev?test_scoring=true` - Get leads with scoring

## 🛠️ Development Commands

```bash
# View service logs
docker-compose logs -f [service_name]

# Restart specific service
docker-compose restart [service_name]

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Clean restart (removes volumes)
docker-compose down -v && docker-compose up -d --build
```

## 📝 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Authentication

The system uses session-based authentication with test credentials:
- **Email**: test@example.com
- **Password**: testpassword123

## 🚨 Monitoring

- **Grafana Dashboards**: http://localhost:13001
- **Prometheus Metrics**: http://localhost:19090
- **Application Logs**: `docker-compose logs -f backend`

## 📋 Environment Variables

Key environment variables are configured in `docker-compose.yml`:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `N8N_BASE_URL`: N8N service URL for internal communication
- `N8N_WEBHOOK_URL`: N8N webhook URL for external access

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly using the test scripts
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Need Help?** Check the logs with `docker-compose logs -f` or open an issue on GitHub.
