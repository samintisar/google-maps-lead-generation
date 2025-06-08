# How to Test LMA Workflows (Local N8N Setup)

This guide explains how to test the Lead Management Analytics workflows with the local n8n setup.

## 🚀 Quick Start

### 1. Start the Environment
```bash
# Windows PowerShell
.\scripts\start-local-n8n.ps1

# Or manually
docker-compose up -d --build
```

### 2. Verify Setup
```bash
cd tests
python test_n8n_local.py
```

## 🔧 N8N Setup

### Access N8N
- **URL**: http://localhost:5678
- **Username**: `admin`
- **Password**: `admin123`

### Import Workflow
1. Open N8N in browser
2. Click "Import from file" (or Ctrl+O)
3. Select `n8n-workflows/Lead_Scoring_CORRECTED.json`
4. Click "Import" and "Save"
5. **Activate the workflow** (toggle switch in top-right)

## 🧪 Testing Methods

### Method 1: Quick Setup Test
```bash
cd tests
python test_n8n_local.py
```

**What it tests**:
- ✅ All services are running
- ✅ Backend endpoints are working
- ✅ N8N webhook is responding
- ✅ Database connectivity

### Method 2: Complete Workflow Test
```bash
cd tests
python test_complete_workflow.py
```

**What it tests**:
- 🔄 Full lead lifecycle simulation
- 📊 Lead scoring calculations
- 🌡️ Temperature classification
- 📧 Social outreach logging
- 🔄 CRM synchronization

### Method 3: N8N Webhook Test
```bash
cd tests
python test_n8n_webhook_endpoints.py
```

**What it tests**:
- 🎯 Direct webhook calls to n8n
- 📊 Lead scoring workflow execution
- 📈 Response validation
- ⏱️ Performance timing

### Method 4: Manual N8N Testing

1. **Open N8N**: http://localhost:5678
2. **Open workflow** in editor
3. **Click "Execute Workflow"** button
4. **Check execution results** in the interface
5. **View node outputs** by clicking on nodes

## 📊 Test Data

### Create Test Leads
```bash
cd scripts/test-data
python create_test_leads_for_scoring.py
```

This creates sample leads with various characteristics for testing scoring algorithms.

### Test Lead Properties
- **Demographics**: Various job titles and seniority levels
- **Firmographics**: Different company sizes and industries
- **Behavioral**: Website visits, page views, downloads
- **Engagement**: Email opens, clicks, responses
- **Temporal**: Recent vs. old activity

## 🔍 Monitoring & Debugging

### Service Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f n8n
docker-compose logs -f postgres
```

### N8N Execution Logs
1. Open N8N: http://localhost:5678
2. Go to "Executions" tab
3. Click on any execution to see details
4. Check node outputs and error messages

### Backend API Logs
```bash
# Real-time backend logs
docker-compose logs -f backend

# Check for specific errors
docker-compose logs backend | grep ERROR
```

### Database Queries
```bash
# Connect to PostgreSQL
docker exec -it lma-postgres psql -U lma_user -d lma_db

# Check leads table
SELECT id, first_name, last_name, score, lead_temperature FROM leads LIMIT 10;

# Check workflow executions
SELECT * FROM workflow_executions ORDER BY started_at DESC LIMIT 5;
```

## 🎯 Specific Test Scenarios

### Test 1: Lead Scoring Webhook
```bash
curl -X POST http://localhost:5678/webhook/lead-activity \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 1,
    "activity": "website_visit",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
```

### Test 2: Batch Lead Scoring
The workflow runs automatically every hour, or you can trigger it manually in n8n.

### Test 3: Hot Lead Alert
1. Create a high-scoring lead
2. Trigger the workflow
3. Check for email alert (if configured)
4. Verify lead status update

### Test 4: CRM Sync
1. Update lead information
2. Trigger CRM sync workflow
3. Check sync status in logs
4. Verify data consistency

## 📈 Expected Results

### Successful Lead Scoring
- **Score Range**: 0-100 points
- **Temperature**: hot (80+), warm (60-79), cold (40-59), frozen (<40)
- **Status Updates**: Automatic status changes based on score
- **Activity Logging**: All actions recorded in database

### Workflow Execution
- **Response Time**: < 30 seconds for typical workflows
- **Success Rate**: > 95% for properly configured workflows
- **Error Handling**: Graceful failure with detailed error messages

### Database Updates
- **Lead Scores**: Updated in `leads` table
- **Score History**: Tracked in `lead_score_history` table
- **Activity Logs**: Recorded in `activity_logs` table
- **Workflow Executions**: Logged in `workflow_executions` table

## 🚨 Troubleshooting

### Common Issues

#### N8N Not Responding
```bash
# Check n8n container status
docker-compose ps n8n

# Restart n8n
docker-compose restart n8n

# Check n8n logs
docker-compose logs -f n8n
```

#### Backend API Errors
```bash
# Check backend status
curl http://localhost:8000/health

# Check database connection
docker-compose logs backend | grep -i database

# Restart backend
docker-compose restart backend
```

#### Workflow Not Executing
1. **Check workflow is active** in n8n interface
2. **Verify webhook URL** is correct
3. **Check authentication** headers
4. **Review execution logs** in n8n

#### Database Connection Issues
```bash
# Test PostgreSQL connection
docker exec -it lma-postgres pg_isready -U lma_user

# Check database logs
docker-compose logs postgres

# Restart database (will lose data)
docker-compose restart postgres
```

### Performance Issues

#### Slow Workflow Execution
- **Check system resources**: `docker stats`
- **Review workflow complexity**: Simplify if needed
- **Increase timeouts**: In n8n node settings
- **Check database performance**: Monitor query times

#### Memory Issues
```bash
# Check container memory usage
docker stats

# Increase memory limits in docker-compose.yml if needed
```

## 📚 Additional Resources

### Documentation
- **N8N Docs**: https://docs.n8n.io/
- **FastAPI Docs**: http://localhost:8000/docs
- **Workflow Guide**: `n8n-workflows/README.md`

### Monitoring
- **Grafana**: http://localhost:13000 (admin/admin)
- **Prometheus**: http://localhost:19090
- **N8N Executions**: http://localhost:5678 → Executions tab

### Support
- **Check logs**: `docker-compose logs -f`
- **Review test results**: Run `test_n8n_local.py`
- **Verify configuration**: Check `docker-compose.yml`

---

**Happy Testing!** 🎉

For issues or questions, check the logs first, then consult the documentation or create an issue on GitHub. 