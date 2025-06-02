-- Initialize databases for LMA project

-- Create n8n database for workflow engine
CREATE DATABASE n8n_db;

-- Grant permissions to lma_user for n8n_db
GRANT ALL PRIVILEGES ON DATABASE n8n_db TO lma_user;

-- Connect to main database and create initial tables
\c lma_db;

-- Create enum types
CREATE TYPE user_role AS ENUM ('admin', 'manager', 'sales_rep', 'viewer');
CREATE TYPE lead_status AS ENUM ('new', 'contacted', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost');
CREATE TYPE lead_source AS ENUM ('website', 'email', 'social_media', 'referral', 'advertising', 'cold_outreach', 'event', 'other');
CREATE TYPE lead_temperature AS ENUM ('hot', 'warm', 'cold');
CREATE TYPE communication_type AS ENUM ('email', 'call', 'meeting', 'linkedin', 'sms');
CREATE TYPE communication_direction AS ENUM ('inbound', 'outbound');
CREATE TYPE communication_status AS ENUM ('scheduled', 'completed', 'failed', 'cancelled');
CREATE TYPE campaign_status AS ENUM ('draft', 'active', 'paused', 'completed', 'cancelled');
CREATE TYPE integration_status AS ENUM ('active', 'inactive', 'error', 'expired');

-- Organizations table (multi-tenancy)
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    website VARCHAR(255),
    industry VARCHAR(100),
    size VARCHAR(50),
    subscription_tier VARCHAR(50) DEFAULT 'free' NOT NULL,
    billing_email VARCHAR(255),
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role user_role DEFAULT 'sales_rep' NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_verified BOOLEAN DEFAULT false NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC' NOT NULL,
    preferences JSONB DEFAULT '{}' NOT NULL,
    avatar_url VARCHAR(500),
    organization_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Workflows table (n8n workflow templates)
CREATE TABLE IF NOT EXISTS workflows (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    n8n_workflow_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    trigger_type VARCHAR(100),
    trigger_conditions JSONB DEFAULT '{}' NOT NULL,
    configuration JSONB DEFAULT '{}' NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Leads table
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    company VARCHAR(255),
    job_title VARCHAR(100),
    phone VARCHAR(50),
    website VARCHAR(255),
    linkedin_url VARCHAR(500),
    lead_temperature lead_temperature DEFAULT 'cold' NOT NULL,
    expected_close_date DATE,
    last_engagement_date TIMESTAMP WITH TIME ZONE,
    status lead_status DEFAULT 'new' NOT NULL,
    source lead_source DEFAULT 'other' NOT NULL,
    score INTEGER DEFAULT 0 NOT NULL,
    value INTEGER,
    notes TEXT,
    tags JSONB,
    custom_fields JSONB,
    first_contacted_at TIMESTAMP WITH TIME ZONE,
    last_contacted_at TIMESTAMP WITH TIME ZONE,
    organization_id INTEGER REFERENCES organizations(id) NOT NULL,
    assigned_to_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Workflow executions table
CREATE TABLE IF NOT EXISTS workflow_executions (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(100) NOT NULL,
    execution_id VARCHAR(100) NOT NULL,
    lead_id INTEGER REFERENCES leads(id) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    finished_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    execution_data JSONB
);

-- Lead scoring rules table
CREATE TABLE IF NOT EXISTS lead_scoring_rules (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL,
    criteria JSONB NOT NULL,
    score_points INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    priority INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Lead score history table
CREATE TABLE IF NOT EXISTS lead_score_history (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE NOT NULL,
    previous_score INTEGER NOT NULL,
    new_score INTEGER NOT NULL,
    score_change INTEGER NOT NULL,
    reason VARCHAR(500),
    rule_id INTEGER REFERENCES lead_scoring_rules(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Communications table
CREATE TABLE IF NOT EXISTS communications (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    communication_type communication_type NOT NULL,
    direction communication_direction NOT NULL,
    subject VARCHAR(500),
    content TEXT,
    status communication_status DEFAULT 'completed' NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    comm_metadata JSONB DEFAULT '{}' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Lead notes table
CREATE TABLE IF NOT EXISTS lead_notes (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    note_type VARCHAR(50) DEFAULT 'general' NOT NULL,
    content TEXT NOT NULL,
    is_private BOOLEAN DEFAULT false NOT NULL,
    mentioned_users INTEGER[],
    attachments JSONB DEFAULT '[]' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    campaign_type VARCHAR(100),
    status campaign_status DEFAULT 'draft' NOT NULL,
    target_criteria JSONB DEFAULT '{}' NOT NULL,
    start_date DATE,
    end_date DATE,
    budget_allocated INTEGER,
    budget_spent INTEGER DEFAULT 0 NOT NULL,
    goals JSONB DEFAULT '{}' NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Campaign leads junction table
CREATE TABLE IF NOT EXISTS campaign_leads (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE NOT NULL,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_contact_at TIMESTAMP WITH TIME ZONE,
    response_at TIMESTAMP WITH TIME ZONE,
    conversion_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(campaign_id, lead_id)
);

-- Integrations table
CREATE TABLE IF NOT EXISTS integrations (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    integration_type VARCHAR(100) NOT NULL,
    provider_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255),
    configuration JSONB NOT NULL,
    status integration_status DEFAULT 'active' NOT NULL,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_frequency_minutes INTEGER DEFAULT 60 NOT NULL,
    error_message TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Lead assignments table
CREATE TABLE IF NOT EXISTS lead_assignments (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE NOT NULL,
    assigned_from INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reason VARCHAR(500),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Activity logs table
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    user_id INTEGER REFERENCES users(id),
    activity_type VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    activity_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for performance
-- Organizations indexes
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organizations_is_active ON organizations(is_active);

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Workflows indexes
CREATE INDEX IF NOT EXISTS idx_workflows_organization_id ON workflows(organization_id);
CREATE INDEX IF NOT EXISTS idx_workflows_n8n_id ON workflows(n8n_workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflows_category ON workflows(category);
CREATE INDEX IF NOT EXISTS idx_workflows_trigger_type ON workflows(trigger_type);
CREATE INDEX IF NOT EXISTS idx_workflows_is_active ON workflows(is_active);

-- Leads indexes
CREATE INDEX IF NOT EXISTS idx_leads_organization_id ON leads(organization_id);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_company ON leads(company);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score);
CREATE INDEX IF NOT EXISTS idx_leads_assigned_to_id ON leads(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_leads_lead_temperature ON leads(lead_temperature);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);

-- Workflow executions indexes
CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_execution_id ON workflow_executions(execution_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_lead_id ON workflow_executions(lead_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);

-- Lead scoring rules indexes
CREATE INDEX IF NOT EXISTS idx_lead_scoring_rules_organization_id ON lead_scoring_rules(organization_id);
CREATE INDEX IF NOT EXISTS idx_lead_scoring_rules_rule_type ON lead_scoring_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_lead_scoring_rules_is_active ON lead_scoring_rules(is_active);

-- Lead score history indexes
CREATE INDEX IF NOT EXISTS idx_lead_score_history_lead_id ON lead_score_history(lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_score_history_rule_id ON lead_score_history(rule_id);

-- Communications indexes
CREATE INDEX IF NOT EXISTS idx_communications_lead_id ON communications(lead_id);
CREATE INDEX IF NOT EXISTS idx_communications_user_id ON communications(user_id);
CREATE INDEX IF NOT EXISTS idx_communications_type ON communications(communication_type);
CREATE INDEX IF NOT EXISTS idx_communications_status ON communications(status);
CREATE INDEX IF NOT EXISTS idx_communications_scheduled_at ON communications(scheduled_at);

-- Lead notes indexes
CREATE INDEX IF NOT EXISTS idx_lead_notes_lead_id ON lead_notes(lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_notes_user_id ON lead_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_lead_notes_note_type ON lead_notes(note_type);

-- Campaigns indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_organization_id ON campaigns(organization_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_campaign_type ON campaigns(campaign_type);

-- Campaign leads indexes
CREATE INDEX IF NOT EXISTS idx_campaign_leads_campaign_id ON campaign_leads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_leads_lead_id ON campaign_leads(lead_id);
CREATE INDEX IF NOT EXISTS idx_campaign_leads_status ON campaign_leads(status);

-- Integrations indexes
CREATE INDEX IF NOT EXISTS idx_integrations_organization_id ON integrations(organization_id);
CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(integration_type);
CREATE INDEX IF NOT EXISTS idx_integrations_status ON integrations(status);

-- Lead assignments indexes
CREATE INDEX IF NOT EXISTS idx_lead_assignments_lead_id ON lead_assignments(lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_assignments_assigned_to ON lead_assignments(assigned_to);

-- Activity logs indexes
CREATE INDEX IF NOT EXISTS idx_activity_logs_lead_id ON activity_logs(lead_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_activity_type ON activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at);

-- Insert default organization for development
INSERT INTO organizations (name, slug, description, settings) 
VALUES ('Default Organization', 'default', 'Default organization for development', '{"timezone": "UTC", "currency": "USD"}')
ON CONFLICT (slug) DO NOTHING;

-- Insert default admin user (password: admin123)
-- The password hash corresponds to: admin123
INSERT INTO users (email, username, first_name, last_name, hashed_password, role, is_active, organization_id)
VALUES (
    'admin@lma.local', 
    'admin', 
    'Admin', 
    'User', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewGo5F/9Qj3hN3Ci', 
    'admin', 
    true,
    (SELECT id FROM organizations WHERE slug = 'default')
)
ON CONFLICT (email) DO NOTHING;

-- Insert sample lead scoring rules
INSERT INTO lead_scoring_rules (organization_id, name, description, rule_type, criteria, score_points, priority)
VALUES 
    (
        (SELECT id FROM organizations WHERE slug = 'default'),
        'Company Size - Enterprise',
        'Large enterprise companies get higher scores',
        'firmographic',
        '{"company_size": {"operator": ">=", "value": 1000}}',
        25,
        1
    ),
    (
        (SELECT id FROM organizations WHERE slug = 'default'),
        'Job Title - Decision Maker',
        'C-level executives and VPs get higher scores',
        'demographic',
        '{"job_title": {"operator": "contains", "values": ["CEO", "CTO", "VP", "Director"]}}',
        20,
        2
    ),
    (
        (SELECT id FROM organizations WHERE slug = 'default'),
        'Website Visit - Pricing Page',
        'Visitors to pricing page show purchase intent',
        'behavioral',
        '{"page_visited": {"value": "/pricing"}}',
        15,
        3
    )
ON CONFLICT DO NOTHING; 