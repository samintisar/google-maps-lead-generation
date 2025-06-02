# Database Schema Design Document

## Overview
This document outlines the comprehensive database schema design for the Lead Management Automation (LMA) platform. The schema supports multi-tenant lead management with workflow automation, lead scoring, and comprehensive activity tracking.

## Current State Analysis

### Existing Models
The current implementation includes the following well-designed core models:

1. **User** - Authentication and user management with role-based access
2. **Organization** - Multi-tenancy support with settings and metadata
3. **Lead** - Core lead management with scoring and status tracking
4. **WorkflowExecution** - n8n workflow execution tracking and results
5. **ActivityLog** - General activity and interaction tracking

### Database Configuration
- **Primary Database**: PostgreSQL
- **ORM**: SQLAlchemy with Alembic migrations
- **Caching**: Redis for session management and performance
- **Multi-tenancy**: Organization-based data isolation

## Enhanced Schema Design

### Core Entities (Existing - To Be Enhanced)

#### 1. User Model (users)
```sql
-- Enhanced with additional fields
ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC';
ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}';
ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);
```

**Enhancements**:
- User preferences (notifications, dashboard layout)
- Timezone support for proper timestamp display
- Avatar URL for profile images

#### 2. Organization Model (organizations)
```sql
-- Already well-designed, potential additions:
ALTER TABLE organizations ADD COLUMN subscription_tier VARCHAR(50) DEFAULT 'free';
ALTER TABLE organizations ADD COLUMN billing_email VARCHAR(255);
```

#### 3. Lead Model (leads)
```sql
-- Enhanced lead tracking
ALTER TABLE leads ADD COLUMN linkedin_url VARCHAR(500);
ALTER TABLE leads ADD COLUMN lead_temperature VARCHAR(20) DEFAULT 'cold'; -- hot, warm, cold
ALTER TABLE leads ADD COLUMN expected_close_date DATE;
ALTER TABLE leads ADD COLUMN last_engagement_date TIMESTAMP WITH TIME ZONE;
```

### New Entities (To Be Added)

#### 4. Workflow Templates (workflows)
```sql
CREATE TABLE workflows (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    n8n_workflow_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100), -- lead_nurturing, follow_up, qualification, etc.
    trigger_type VARCHAR(100), -- manual, scheduled, event_based, lead_status_change
    trigger_conditions JSONB DEFAULT '{}',
    configuration JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workflows_organization_id ON workflows(organization_id);
CREATE INDEX idx_workflows_n8n_id ON workflows(n8n_workflow_id);
CREATE INDEX idx_workflows_trigger_type ON workflows(trigger_type);
CREATE INDEX idx_workflows_category ON workflows(category);
```

#### 5. Lead Scoring Rules (lead_scoring_rules)
```sql
CREATE TABLE lead_scoring_rules (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL, -- demographic, behavioral, engagement, firmographic
    criteria JSONB NOT NULL, -- JSON conditions for scoring
    score_points INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 1, -- Higher priority rules applied first
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scoring_rules_org_id ON lead_scoring_rules(organization_id);
CREATE INDEX idx_scoring_rules_type ON lead_scoring_rules(rule_type);
```

#### 6. Lead Score History (lead_score_history)
```sql
CREATE TABLE lead_score_history (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    previous_score INTEGER NOT NULL,
    new_score INTEGER NOT NULL,
    score_change INTEGER NOT NULL, -- calculated: new_score - previous_score
    reason VARCHAR(500), -- reason for score change
    rule_id INTEGER REFERENCES lead_scoring_rules(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_score_history_lead_id ON lead_score_history(lead_id);
CREATE INDEX idx_score_history_created_at ON lead_score_history(created_at);
```

#### 7. Communication Log (communications)
```sql
CREATE TABLE communications (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    communication_type VARCHAR(50) NOT NULL, -- email, call, meeting, linkedin, sms
    direction VARCHAR(20) NOT NULL, -- inbound, outbound
    subject VARCHAR(500),
    content TEXT,
    status VARCHAR(50) DEFAULT 'completed', -- scheduled, completed, failed, cancelled
    scheduled_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}', -- email headers, call duration, meeting attendees, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_communications_lead_id ON communications(lead_id);
CREATE INDEX idx_communications_user_id ON communications(user_id);
CREATE INDEX idx_communications_type ON communications(communication_type);
CREATE INDEX idx_communications_scheduled_at ON communications(scheduled_at);
```

#### 8. Campaigns (campaigns)
```sql
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    campaign_type VARCHAR(100), -- email, cold_outreach, content, social, event
    status VARCHAR(50) DEFAULT 'draft', -- draft, active, paused, completed, cancelled
    target_criteria JSONB DEFAULT '{}', -- JSON criteria for lead targeting
    start_date DATE,
    end_date DATE,
    budget_allocated INTEGER, -- in cents
    budget_spent INTEGER DEFAULT 0, -- in cents
    goals JSONB DEFAULT '{}', -- campaign goals and KPIs
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_campaigns_organization_id ON campaigns(organization_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_type ON campaigns(campaign_type);
```

#### 9. Campaign Leads (campaign_leads)
```sql
CREATE TABLE campaign_leads (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending', -- pending, contacted, responded, converted, excluded
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_contact_at TIMESTAMP WITH TIME ZONE,
    response_at TIMESTAMP WITH TIME ZONE,
    conversion_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(campaign_id, lead_id)
);

CREATE INDEX idx_campaign_leads_campaign_id ON campaign_leads(campaign_id);
CREATE INDEX idx_campaign_leads_lead_id ON campaign_leads(lead_id);
CREATE INDEX idx_campaign_leads_status ON campaign_leads(status);
```

#### 10. Integrations (integrations)
```sql
CREATE TABLE integrations (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    integration_type VARCHAR(100) NOT NULL, -- crm, email_provider, social, calendar, etc.
    provider_name VARCHAR(100) NOT NULL, -- salesforce, hubspot, gmail, outlook, etc.
    display_name VARCHAR(255),
    configuration JSONB NOT NULL, -- API keys, endpoints, settings (encrypted)
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, error, expired
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_frequency_minutes INTEGER DEFAULT 60,
    error_message TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_integrations_organization_id ON integrations(organization_id);
CREATE INDEX idx_integrations_type ON integrations(integration_type);
CREATE INDEX idx_integrations_status ON integrations(status);
```

#### 11. Lead Notes (lead_notes)
```sql
CREATE TABLE lead_notes (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    note_type VARCHAR(50) DEFAULT 'general', -- general, meeting, call, research, reminder
    content TEXT NOT NULL,
    is_private BOOLEAN DEFAULT false, -- Private to the user who created it
    mentioned_users INTEGER[], -- Array of user IDs mentioned in the note
    attachments JSONB DEFAULT '[]', -- Array of attachment metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lead_notes_lead_id ON lead_notes(lead_id);
CREATE INDEX idx_lead_notes_user_id ON lead_notes(user_id);
CREATE INDEX idx_lead_notes_type ON lead_notes(note_type);
CREATE INDEX idx_lead_notes_created_at ON lead_notes(created_at);
```

#### 12. Lead Assignments History (lead_assignments)
```sql
CREATE TABLE lead_assignments (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    assigned_from INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reason VARCHAR(500),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lead_assignments_lead_id ON lead_assignments(lead_id);
CREATE INDEX idx_lead_assignments_assigned_to ON lead_assignments(assigned_to);
CREATE INDEX idx_lead_assignments_assigned_at ON lead_assignments(assigned_at);
```

## Relationships and Constraints

### Key Relationships
1. **Organization → Users** (1:N): Multi-tenant user management
2. **Organization → Leads** (1:N): Organization-scoped leads
3. **Organization → Workflows** (1:N): Custom workflows per organization
4. **Organization → Campaigns** (1:N): Campaign management per organization
5. **Lead → Communications** (1:N): Communication history per lead
6. **Lead → Notes** (1:N): Detailed notes and research per lead
7. **Lead → Score History** (1:N): Track scoring changes over time
8. **Campaign → Leads** (N:N): Many-to-many campaign participation
9. **Workflow → Executions** (1:N): Track workflow runs

### Data Integrity Constraints
- All organization-scoped data uses `ON DELETE CASCADE`
- User references use `ON DELETE SET NULL` to preserve history
- Unique constraints on critical business keys (email within org, workflow IDs)
- JSON schema validation on configuration fields

## Performance Optimization

### Primary Indexes
- **Foreign keys**: All foreign key columns have indexes
- **Query patterns**: Indexes on frequently filtered columns (status, type, dates)
- **Composite indexes**: Multi-column indexes for common query patterns

### Specific Performance Indexes
```sql
-- Lead management queries
CREATE INDEX idx_leads_org_status_score ON leads(organization_id, status, score DESC);
CREATE INDEX idx_leads_assigned_status ON leads(assigned_to_id, status) WHERE assigned_to_id IS NOT NULL;

-- Activity and communication queries
CREATE INDEX idx_activity_logs_lead_type_date ON activity_logs(lead_id, activity_type, created_at DESC);
CREATE INDEX idx_communications_lead_type_date ON communications(lead_id, communication_type, completed_at DESC);

-- Campaign performance queries
CREATE INDEX idx_campaign_leads_campaign_status ON campaign_leads(campaign_id, status);

-- Workflow execution queries
CREATE INDEX idx_workflow_executions_workflow_status ON workflow_executions(workflow_id, status, started_at DESC);
```

### Partitioning Strategy (Future)
For high-volume deployments, consider partitioning:
- **activity_logs**: Partition by month (created_at)
- **communications**: Partition by month (created_at)
- **workflow_executions**: Partition by month (started_at)

## Security Considerations

### Row Level Security (RLS)
PostgreSQL RLS policies for multi-tenancy:
```sql
-- Enable RLS on all organization-scoped tables
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

-- Example policy for leads table
CREATE POLICY leads_organization_isolation ON leads
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

### Data Encryption
- Sensitive integration configuration data should be encrypted at application level
- Consider column-level encryption for PII if required by compliance

## Migration Strategy

### Phase 1: Core Enhancements (Current Sprint)
1. Add new tables: workflows, lead_scoring_rules, communications
2. Enhance existing tables with new columns
3. Create essential indexes

### Phase 2: Advanced Features
1. Add campaigns and campaign_leads tables
2. Implement lead_notes and lead_assignments
3. Add integrations table

### Phase 3: Performance & Scale
1. Implement partitioning for high-volume tables
2. Add Row Level Security policies
3. Optimize indexes based on usage patterns

## Redis Schema Design

### Session Management
```
sessions:{session_id} -> {user_data, expiry}
user_sessions:{user_id} -> [session_ids]
```

### Lead Caching
```
lead:{lead_id} -> {cached_lead_data}
lead_score:{lead_id} -> {current_score, last_calculated}
```

### Workflow Caching
```
workflow:{workflow_id} -> {workflow_config}
active_workflows:{organization_id} -> [workflow_ids]
```

### Communication Queues
```
outbound_emails -> [email_tasks]
scheduled_communications -> [scheduled_tasks]
```

## Conclusion

This enhanced schema design provides:
- **Scalability**: Proper indexing and potential for partitioning
- **Flexibility**: JSON fields for extensible configuration
- **Audit Trail**: Comprehensive history tracking
- **Performance**: Optimized for common query patterns
- **Security**: Multi-tenant isolation and encryption-ready
- **Integration-Ready**: Extensible integration framework

The schema supports the core LMA functionality while providing room for future enhancements and scaling. 