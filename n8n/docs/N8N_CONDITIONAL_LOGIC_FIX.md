# N8N Workflow Conditional Logic Fix

## Problem
The "Is Warm Lead" and "Is Hot Lead" conditional nodes in the n8n workflow were not generating outputs, causing subsequent nodes (Get Hot Leads for Outreach, Log Sales Alert Activity) to not execute.

## Root Cause
The conditional expressions were referencing the wrong data structure:
- **Incorrect**: `{{$json.data.lead_temperature}}`
- **Correct**: `{{$json.lead_temperature}}`

The `Update Lead Status` node returns data directly in `$json`, not wrapped in a `data` object.

## Fix Applied
Updated the following nodes in `Lead_Scoring_CORRECTED_UPDATED.json`:

### 1. Is Hot Lead1 Node
```json
"conditions": {
  "string": [
    {
      "value1": "={{$json.lead_temperature}}", // Fixed: removed .data
      "value2": "hot"
    }
  ]
}
```

### 2. Is Warm Lead1 Node  
```json
"conditions": {
  "string": [
    {
      "value1": "={{$json.lead_temperature}}", // Fixed: removed .data
      "value2": "warm"
    }
  ]
}
```

### 3. Log Sales Alert Activity1 Node
```json
"url": "http://backend:8000/api/workflows/leads/{{$json.id}}/social-outreach", // Fixed: removed .data
```

```json
"value": "Sales team notified about warm lead (Score: {{$json.score}})" // Fixed: removed .data
```

## Expected Behavior After Fix
- **Hot leads** (score ≥ 80): Trigger email alerts + outreach workflow
- **Warm leads** (score 60-79): Log sales activity for follow-up
- **Cold leads** (score < 60): Continue to CRM sync only

## Testing
Run `tests/test_workflow_conditionals.py` to verify the logic works correctly.

## Deployment
1. Stop the current n8n workflow
2. Import the updated `Lead_Scoring_CORRECTED_UPDATED.json` file
3. Activate the workflow
4. Test with sample leads of different temperatures

## Data Structure Reference
The corrected data structure from the Update Lead Status node:
```json
{
  "id": 3,
  "email": "user@example.com",
  "lead_temperature": "warm", // Direct property, not nested
  "score": 65,
  "score_breakdown": { ... },
  "// ... other lead properties"
}
``` 