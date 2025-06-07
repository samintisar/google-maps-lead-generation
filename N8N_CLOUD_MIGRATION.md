# n8n Cloud Migration Guide

This document outlines the changes made to support **n8n Cloud** integration, replacing direct PostgreSQL database access with API-based interactions.

## 🔄 What Changed

### **Removed Components:**
- ❌ Local n8n Docker container
- ❌ n8n service from docker-compose.yml  
- ❌ Direct PostgreSQL access from n8n workflows
- ❌ n8n monitoring in Prometheus

### **Added Components:**
- ✅ New API endpoints for n8n Cloud integration
- ✅ Backend sales alerts system
- ✅ API-based lead scoring workflow
- ✅ External IP configuration

---

## 🚀 New API Endpoints

### **Lead Management APIs**
```bash
# Get leads that need scoring
GET /api/leads/for-scoring?hours_back=24

# Bulk update lead scores from n8n
POST /api/leads/score/bulk-update-n8n

# Log lead activity
POST /api/leads/activity/log
```

### **Sales Alert APIs**
```bash
# Hot lead notifications
POST /api/sales-alerts/hot-lead

# Warm lead notifications  
POST /api/sales-alerts/warm-lead

# Score change notifications
POST /api/sales-alerts/score-change
```

---

## 📁 New Files Created

### **Backend Files:**
- `backend/routers/sales.py` - Sales alert endpoints
- `n8n-workflows/lead-scoring-template-api.json` - API-based workflow

### **Updated Files:**
- `backend/routers/leads.py` - Added n8n-specific endpoints
- `backend/main.py` - Added sales router
- `backend/config.py` - Updated for n8n Cloud URLs
- `docker-compose.yml` - Removed n8n service
- `monitoring/prometheus/prometheus.yml` - Removed n8n monitoring

---

## 🛠️ Setup Instructions

### **1. Update Environment Variables**
Add these to your `.env` file:
```bash
# n8n Cloud Configuration
N8N_WEBHOOK_URL=https://your-n8n-cloud-instance.app.n8n.cloud/webhook
N8N_API_BASE_URL=https://your-n8n-cloud-instance.app.n8n.cloud/api/v1
N8N_API_KEY=your_n8n_cloud_api_key_here

# Your Public IP (for webhook callbacks)
PUBLIC_IP=192.168.1.106
BACKEND_URL=http://192.168.1.106:8000

# Frontend Configuration
VITE_N8N_URL=https://your-n8n-cloud-instance.app.n8n.cloud
VITE_API_URL=http://192.168.1.106:8000
```

### **2. n8n Cloud Credentials Setup**

**Backend API Credential (HTTP Header Auth):**
```
Name: Backend API
Header Name: Authorization
Header Value: Bearer dev-token-12345
```

**SMTP Email Credential:**
```
Host: smtp.gmail.com (or your SMTP provider)
Port: 587
Security: STARTTLS
Username: your-email@domain.com
Password: your-app-password
```

### **3. Import New Workflow**
1. Go to n8n Cloud dashboard
2. Import `n8n-workflows/lead-scoring-template-api.json`
3. Update all URLs to use your public IP: `http://192.168.1.106:8000`
4. Configure credentials as above
5. Activate the workflow

---

## 🔧 Key Differences from Local n8n

### **Database Access:**
- ❌ **Before:** Direct PostgreSQL queries
- ✅ **Now:** REST API calls to backend

### **Authentication:**
- ❌ **Before:** None (local network)
- ✅ **Now:** HTTP Header Authentication

### **Connectivity:**
- ❌ **Before:** Docker internal network (`postgres:5432`)
- ✅ **Now:** Public IP access (`192.168.1.106:8000`)

---

## 📊 Workflow Changes

### **Get Leads for Scoring Node:**
```json
{
  "name": "Get Leads for Scoring",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "http://192.168.1.106:8000/api/leads/for-scoring",
    "httpMethod": "GET",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth"
  }
}
```

### **Update Lead Score Node:**
```json
{
  "name": "Update Lead Score", 
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "http://192.168.1.106:8000/api/leads/score/bulk-update-n8n",
    "httpMethod": "POST",
    "body": "[{\"id\": {{$json.id}}, \"score\": {{$json.score}}, \"lead_temperature\": \"{{$json.lead_temperature}}\"}]"
  }
}
```

### **Log Activity Node:**
```json
{
  "name": "Log Scoring Activity",
  "type": "n8n-nodes-base.httpRequest", 
  "parameters": {
    "url": "http://192.168.1.106:8000/api/leads/activity/log",
    "httpMethod": "POST",
    "body": "{\"lead_id\": {{$json.id}}, \"activity_type\": \"lead_scoring\"}"
  }
}
```

---

## ✅ Testing the Setup

### **1. Test API Endpoints:**
```bash
# Test lead retrieval
curl -H "Authorization: Bearer dev-token-12345" \
  "http://192.168.1.106:8000/api/leads/for-scoring?hours_back=24"

# Test hot lead alert
curl -X POST -H "Authorization: Bearer dev-token-12345" \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1, "name": "Test Lead", "score": 85}' \
  "http://192.168.1.106:8000/api/sales-alerts/hot-lead"
```

### **2. Test n8n Workflow:**
1. Trigger workflow manually in n8n Cloud
2. Check backend logs: `docker-compose logs backend`
3. Verify activity logs in database
4. Confirm lead scores were updated

---

## 🔒 Security Considerations

### **API Authentication:**
- Using development token for simplicity
- For production, implement proper JWT tokens
- Consider API rate limiting

### **Network Access:**
- Backend is accessible via public IP
- Consider VPN or tunneling for production
- Use HTTPS in production environment

### **Data Privacy:**
- Lead data transmitted over HTTP (local network)
- Use HTTPS for production deployments
- Consider data encryption for sensitive fields

---

## 🚨 Troubleshooting

### **Common Issues:**

**1. n8n Can't Connect to Backend:**
- ✅ Verify public IP is correct (`192.168.1.106`)
- ✅ Check backend is running: `curl http://192.168.1.106:8000/health`
- ✅ Verify authentication header in n8n credential

**2. Authentication Errors:**
- ✅ Check HTTP Header Auth credential in n8n
- ✅ Verify header name is `Authorization`
- ✅ Verify header value is `Bearer dev-token-12345`

**3. No Leads Returned:**
- ✅ Check if leads exist in database
- ✅ Verify dev user organization ID
- ✅ Adjust `hours_back` parameter

**4. Workflow Timeouts:**
- ✅ Increase timeout in n8n nodes (30+ seconds)
- ✅ Check backend response times
- ✅ Verify network connectivity

### **Debug Commands:**
```bash
# Check backend status
docker-compose ps

# View backend logs
docker-compose logs backend --tail=50

# Test direct API access
curl -H "Authorization: Bearer dev-token-12345" \
  "http://192.168.1.106:8000/api/leads/dev"

# Check database connection
docker-compose exec postgres psql -U lma_user -d lma_db -c "SELECT COUNT(*) FROM leads;"
```

---

## 📈 Benefits of n8n Cloud Migration

✅ **Scalability:** Cloud-hosted, managed infrastructure  
✅ **Reliability:** Professional uptime and support  
✅ **Maintenance:** No local container management  
✅ **Features:** Access to latest n8n features  
✅ **Integration:** Better external service connectivity  

---

## 🎯 Next Steps

1. **Test the new workflow thoroughly**
2. **Set up production authentication**
3. **Configure proper HTTPS**
4. **Add monitoring for API endpoints**
5. **Implement email notifications**
6. **Add error handling and retries**

---

*Migration completed successfully! Your n8n workflows now run in the cloud while securely accessing your local backend via API endpoints.* 