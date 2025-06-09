# N8N Workflows for LMA

This directory contains n8n workflow definitions for the Lead Management Analytics platform.

## 🚀 Quick Setup

### 1. Access N8N
- URL: http://localhost:5678
- Username: `admin`
- Password: `admin123`

### 2. Import Workflows

1. **Open N8N** in your browser
2. **Click "Import from file"** (or use Ctrl+O)
3. **Select workflow file** from this directory
4. **Click "Import"**
5. **Save the workflow**
6. **Activate the workflow** (toggle switch in top-right)

## 📁 Available Workflows

### Lead_Scoring_CORRECTED.json ⭐ (Recommended)
**Purpose**: Complete lead scoring automation with proper local endpoints

**Features**:
- Automated lead scoring (0-100 points)
- Temperature classification (hot/warm/cold/frozen)
- Sales alert emails for hot leads
- CRM synchronization
- Activity logging

**Triggers**:
- Webhook: `/webhook/lead-activity`
- Cron: Every hour for batch processing

**Endpoints Used**:
- `GET /api/leads/dev?test_scoring=true` - Fetch leads for scoring
- `POST /api/workflows/leads/{id}/update-status` - Update lead status
- `GET /api/workflows/leads/social-outreach` - Get leads for outreach
- `POST /api/workflows/leads/{id}/social-outreach` - Log outreach activity
- `GET /api/workflows/leads/crm-sync` - Get leads for CRM sync

### Lead_Scoring.json (Legacy)
**Purpose**: Original workflow with external endpoints (for reference only)

**Note**: This workflow uses incorrect endpoints and external IPs. Use `Lead_Scoring_CORRECTED.json` instead.

### Template Workflows

#### crm-sync-template-api.json
- CRM synchronization template
- Bidirectional data sync
- Error handling and retry logic

#### social-media-outreach-template-api.json
- LinkedIn and email outreach automation
- Personalized messaging
- Response tracking

#### lead-nurturing-template-api.json
- Automated lead nurturing sequences
- Email drip campaigns
- Engagement tracking

#### template-index.json
- Master template index
- Workflow organization
- Template metadata

## 🔧 Configuration

### Authentication
All workflows are configured to use:
- **Authorization Header**: `Bearer test-token`
- **Base URL**: `http://backend:8000` (internal Docker network)

### Webhook URLs
When testing webhooks externally, use:
- **Base URL**: `http://localhost:5678`
- **Webhook Path**: `/webhook/[webhook-name]`

Example: `http://localhost:5678/webhook/lead-activity`

## 🧪 Testing Workflows

### Manual Testing
1. **Open workflow** in n8n editor
2. **Click "Execute Workflow"** button
3. **Check execution log** for results
4. **View node outputs** by clicking on nodes

### API Testing
```bash
# Test lead scoring webhook
curl -X POST http://localhost:5678/webhook/lead-activity \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1, "activity": "website_visit"}'
```

### Using Test Scripts
```bash
cd tests
python test_n8n_webhook_endpoints.py
```

## 📊 Workflow Monitoring

### N8N Interface
- **Executions**: View all workflow runs
- **Logs**: Check execution details and errors
- **Metrics**: Monitor performance and success rates

### External Monitoring
- **Grafana**: http://localhost:13000
- **Prometheus**: http://localhost:19090
- **Backend Logs**: `docker-compose logs -f backend`

## 🔄 Workflow Development

### Best Practices
1. **Use environment variables** for URLs and credentials
2. **Add error handling** nodes for robust workflows
3. **Test with sample data** before production use
4. **Document workflow purpose** and dependencies
5. **Version control** workflow exports

### Common Issues
- **Connection errors**: Check if backend service is running
- **Authentication failures**: Verify Bearer token configuration
- **Timeout errors**: Increase node timeout settings
- **Data format issues**: Check API response formats

### Debugging
1. **Enable debug mode** in workflow settings
2. **Check node outputs** for data flow
3. **Review execution logs** for errors
4. **Test individual nodes** in isolation

## 🚀 Production Deployment

### Environment Variables
Update these in production:
- `N8N_BASIC_AUTH_USER`: Production username
- `N8N_BASIC_AUTH_PASSWORD`: Strong password
- `N8N_ENCRYPTION_KEY`: Unique encryption key
- `WEBHOOK_URL`: Production webhook URL

### Security
- **Change default credentials**
- **Use HTTPS** for webhook URLs
- **Implement proper authentication**
- **Regular backup** of workflows

### Scaling
- **Use n8n queue mode** for high volume
- **Monitor resource usage**
- **Implement workflow versioning**
- **Set up alerting** for failed executions

## 📚 Resources

- [N8N Documentation](https://docs.n8n.io/)
- [Workflow Templates](https://n8n.io/workflows/)
- [API Integration Guide](https://docs.n8n.io/integrations/)
- [Best Practices](https://docs.n8n.io/workflows/best-practices/)

---

**Need Help?** Check the n8n logs with `docker-compose logs -f n8n` or consult the official documentation. 