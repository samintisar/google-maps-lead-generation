# How to Actually Test the Lead Scoring Workflow in N8N Cloud

You're right - my previous testing was just **simulation**! Let's actually execute the workflow in your n8n Cloud instance.

## 🚀 Step 1: Import the Workflow

1. **Go to your n8n Cloud instance**
2. **Click "Import workflow"** (+ button > Import from file)
3. **Upload** the `n8n-workflows/Lead_Scoring.json` file
4. **Save** the imported workflow

## ⚙️ Step 2: Configure the Workflow

### Update the HTTP Request Node
The workflow is already configured with the correct endpoint:
```
URL: http://192.168.1.106:8000/api/leads/dev?test_scoring=true
Method: GET
Authentication: None (for development)
```

### Check Email Configuration (Optional)
If you want to test email alerts:
- Configure SMTP credentials in the "Send Sales Alert Email" node
- Or disable this node for initial testing

## 🧪 Step 3: Test the Workflow Manually

### Option A: Test Individual Nodes
1. **Select the "Get Leads for Scoring" node**
2. **Click "Test step"** or "Execute node"
3. **Verify** it returns the 4 test leads
4. **Continue testing** each subsequent node

### Option B: Execute Full Workflow
1. **Click "Execute workflow"** button
2. **Watch the execution** flow through each node
3. **Check for errors** in any node
4. **View the final results**

## 🔍 Step 4: Verify Execution Results

After execution, you should see:

### ✅ Expected Success Flow
```
Hourly Score Update (Cron) 
    ↓
Get Leads for Scoring (HTTP Request)
    ↓ (4 leads retrieved)
Calculate Lead Scores (Code)
    ↓ (Scores calculated)
Significant Score Change (If)
    ↓ (Some leads qualify)
Update Lead Score (HTTP Request) ⚠️ May fail - endpoint needs implementation
    ↓
Is Hot Lead / Is Warm Lead (If conditions)
    ↓
Notify Sales Team / Trigger Follow-up ⚠️ May fail - endpoints need implementation
    ↓
Log Scoring Activity ⚠️ May fail - endpoint needs implementation
```

### ⚠️ Expected Failures (These are OK!)
- **Update Lead Score**: `/api/leads/score/bulk-update-n8n` endpoint not implemented yet
- **Notify Sales Team**: `/api/sales-alerts/hot-lead` endpoint not implemented yet  
- **Log Scoring Activity**: `/api/leads/activity/log` endpoint not implemented yet

## 📊 Step 5: What to Look For

### ✅ Success Indicators
1. **"Get Leads for Scoring"** returns 4 leads in JSON format
2. **"Calculate Lead Scores"** processes all 4 leads and adds scoring data
3. **Score calculations** show realistic values (demographic, behavioral, etc.)
4. **Temperature classification** correctly identifies hot/warm/cold leads

### ❌ Expected Errors (Normal for now)
- HTTP 404/500 errors on bulk-update, sales-alerts, activity-log endpoints
- These will be fixed when we implement the missing backend endpoints

## 🧪 Step 6: Manual Test Run

Let's do a quick test to verify your workflow is working:

1. **Import the workflow** into n8n Cloud
2. **Execute the "Get Leads for Scoring" node** manually
3. **Check if you get this result**:
```json
{
  "items": [
    {
      "email": "john.doe@example.com", 
      "first_name": "John",
      "last_name": "Doe",
      "company": "Tech Corp",
      "score": 75,
      // ... more fields
    }
    // ... 3 more leads
  ]
}
```

## 🔧 Troubleshooting

### If "Get Leads for Scoring" Fails:
- **Check URL**: Make sure `http://192.168.1.106:8000` is accessible from n8n Cloud
- **Try the URL in browser**: Visit the endpoint directly to verify it works
- **Check firewall**: Ensure your local backend is accessible from the internet

### If Scoring Calculation Fails:
- **Check the Code node**: Look for JavaScript errors in the console
- **Verify data structure**: Ensure the input data matches expected format

### If Everything Fails:
- **Use webhook testing**: Import the workflow and trigger via webhook
- **Test locally first**: Run n8n locally to test before using Cloud

## 🎯 Success Criteria

**Your workflow is working correctly if:**
1. ✅ "Get Leads for Scoring" retrieves 4 leads
2. ✅ "Calculate Lead Scores" processes them without errors  
3. ✅ Score breakdown shows realistic values
4. ✅ Temperature classification works (hot/warm/cold)
5. ⚠️ Downstream endpoints fail (expected until we implement them)

## 📞 Need Help?

If you're still not seeing executions in n8n Cloud:
1. **Check the executions tab** in your n8n Cloud workspace
2. **Look for error messages** in failed nodes
3. **Verify network connectivity** between n8n Cloud and your backend
4. **Test the backend endpoint** directly in a browser first

**The core workflow logic should work perfectly - any failures will be on the backend endpoints we haven't implemented yet!** 