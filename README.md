# Lead Management Automation Platform

An n8n-first automation platform with SvelteKit frontend and minimal FastAPI backend for advanced lead management and SaaS analytics.

## 🏗️ Architecture Overview

This platform is designed with an **n8n-first approach**, where 80% of business operations are handled through n8n workflows, ensuring scalability, maintainability, and ease of configuration.

### Technology Stack

- **Frontend**: SvelteKit + TypeScript + Tailwind CSS
- **Backend**: FastAPI (Python) - Analytics focus only
- **Automation**: n8n (Primary business logic layer)
- **Database**: PostgreSQL + Redis
- **Orchestration**: Kubernetes
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: GitHub Actions

### Project Structure

```
├── frontend/          # SvelteKit frontend application
├── backend/           # FastAPI analytics backend
├── n8n-workflows/     # n8n workflow templates and configurations
├── docker/            # Docker configurations for all services
├── kubernetes/        # Kubernetes manifests
├── ci-cd/             # CI/CD pipeline configurations
├── monitoring/        # Prometheus and Grafana configurations
├── docs/              # Project documentation
├── scripts/           # Project management and deployment scripts
└── tasks/             # Task Master task definitions
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- kubectl (for Kubernetes deployment)

### Development Setup

1. Clone the repository
2. Set up environment variables (copy `.env.example` to `.env`)
3. Start development services:

```bash
docker-compose up -d
```

4. Access the applications:
   - n8n: http://localhost:5678
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Documentation: http://localhost:8000/docs

## 📋 Core Features

### n8n Automation Layer (80% of operations)
- Lead scoring and enrichment workflows
- Multi-channel outreach automation
- CRM bidirectional synchronization
- Real-time lead routing and assignment
- Email and SMS campaign management

### SvelteKit Frontend
- High-performance reactive UI
- Real-time dashboard with SaaS metrics
- Lead management interface
- Team collaboration tools
- Mobile-responsive design

### FastAPI Analytics Backend
- SaaS metrics calculation (MRR, CAC, LTV)
- Advanced analytics and reporting
- Data aggregation and processing
- Authentication and authorization

## 🔧 Development

### Frontend Development (SvelteKit)

```bash
cd frontend
npm install
npm run dev
```

### Backend Development (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### n8n Workflow Development

1. Access n8n at http://localhost:5678
2. Import workflow templates from `n8n-workflows/`
3. Configure credentials and test workflows

## 🚢 Deployment

### Local Development
```bash
docker-compose up -d
```

### Production (Kubernetes)
```bash
kubectl apply -f kubernetes/
```

## 📊 Monitoring

- **Prometheus**: Metrics collection
- **Grafana**: Visualization and alerting
- **Logs**: Centralized logging with ELK stack

## 🧪 Testing

### Frontend Tests
```bash
cd frontend
npm run test
```

### Backend Tests
```bash
cd backend
pytest
```

### n8n Workflow Tests
- Use n8n's built-in testing capabilities
- Validate workflows with test data

## 📚 Documentation

- [API Documentation](docs/api.md)
- [n8n Workflows](docs/workflows.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guide](docs/contributing.md)

## 🔐 Security

- OAuth 2.0 authentication
- Role-based access control (RBAC)
- API rate limiting
- Secure credential management

## 📈 Roadmap

See [tasks/](tasks/) directory for detailed project tasks and progress tracking using Task Master.

## 🤝 Contributing

Please read our [Contributing Guide](docs/contributing.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
