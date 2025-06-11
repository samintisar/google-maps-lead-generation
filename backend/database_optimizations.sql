-- Database Schema Optimizations for LMA Platform
-- Implements performance improvements based on query pattern analysis

-- ====================================
-- COMPOSITE INDEXES FOR COMMON QUERIES
-- ====================================

-- Lead Management Optimizations
-- Most common lead queries filter by organization + status + assignment
CREATE INDEX IF NOT EXISTS idx_leads_org_status_assigned 
ON leads(organization_id, status, assigned_to_id) 
WHERE status != 'closed_lost' AND status != 'closed_won';

-- Lead scoring and filtering by organization + score range
CREATE INDEX IF NOT EXISTS idx_leads_org_score_temp 
ON leads(organization_id, score DESC, lead_temperature) 
WHERE score > 0;

-- Lead search by organization + creation time (recent leads first)
CREATE INDEX IF NOT EXISTS idx_leads_org_created_desc 
ON leads(organization_id, created_at DESC);

-- Lead source analysis by organization + source + status
CREATE INDEX IF NOT EXISTS idx_leads_org_source_status 
ON leads(organization_id, source, status);

-- Communication Management Optimizations
-- Communication history by lead + type + completion
CREATE INDEX IF NOT EXISTS idx_comms_lead_type_completed 
ON communications(lead_id, communication_type, completed_at DESC) 
WHERE status = 'completed';

-- Scheduled communications by user + date
CREATE INDEX IF NOT EXISTS idx_comms_user_scheduled 
ON communications(user_id, scheduled_at) 
WHERE status = 'scheduled' AND scheduled_at IS NOT NULL;

-- Communication activity by organization (via lead) + date range
CREATE INDEX IF NOT EXISTS idx_comms_org_activity 
ON communications(lead_id, created_at DESC) 
INCLUDE (communication_type, direction, status);

-- Campaign Management Optimizations
-- Active campaigns by organization + type
CREATE INDEX IF NOT EXISTS idx_campaigns_org_type_active 
ON campaigns(organization_id, campaign_type) 
WHERE status = 'active';

-- Campaign lead performance tracking
CREATE INDEX IF NOT EXISTS idx_campaign_leads_performance 
ON campaign_leads(campaign_id, status, added_at DESC);

-- Workflow and Automation Optimizations
-- Active workflows by organization + category
CREATE INDEX IF NOT EXISTS idx_workflows_org_category_active 
ON workflows(organization_id, category) 
WHERE is_active = true;

-- Workflow execution monitoring
CREATE INDEX IF NOT EXISTS idx_workflow_exec_monitoring 
ON workflow_executions(workflow_id, status, started_at DESC);

-- User and Organization Management
-- Active users by organization + role
CREATE INDEX IF NOT EXISTS idx_users_org_role_active 
ON users(organization_id, role) 
WHERE is_active = true;

-- ====================================
-- JSON FIELD OPTIMIZATION WITH GIN INDEXES
-- ====================================

-- Lead tags and custom fields search optimization
CREATE INDEX IF NOT EXISTS idx_leads_tags_gin 
ON leads USING GIN (tags);

CREATE INDEX IF NOT EXISTS idx_leads_custom_fields_gin 
ON leads USING GIN (custom_fields);

-- User preferences optimization
CREATE INDEX IF NOT EXISTS idx_users_preferences_gin 
ON users USING GIN (preferences);

-- Organization settings optimization
CREATE INDEX IF NOT EXISTS idx_organizations_settings_gin 
ON organizations USING GIN (settings);

-- Lead scoring rule criteria optimization
CREATE INDEX IF NOT EXISTS idx_lead_scoring_criteria_gin 
ON lead_scoring_rules USING GIN (criteria);

-- Campaign targeting criteria optimization
CREATE INDEX IF NOT EXISTS idx_campaigns_target_criteria_gin 
ON campaigns USING GIN (target_criteria);

-- Communication metadata optimization
CREATE INDEX IF NOT EXISTS idx_communications_metadata_gin 
ON communications USING GIN (comm_metadata);

-- ====================================
-- PARTIAL INDEXES FOR ACTIVE RECORDS
-- ====================================

-- Only index active organizations for faster lookups
CREATE INDEX IF NOT EXISTS idx_organizations_active_only 
ON organizations(name, slug) 
WHERE is_active = true;

-- Only index verified active users
CREATE INDEX IF NOT EXISTS idx_users_verified_active 
ON users(email, username, organization_id) 
WHERE is_active = true AND is_verified = true;

-- Only index active lead scoring rules
CREATE INDEX IF NOT EXISTS idx_lead_scoring_rules_active_priority 
ON lead_scoring_rules(organization_id, priority DESC, rule_type) 
WHERE is_active = true;

-- Only index pending and in-progress leads for assignment queues
CREATE INDEX IF NOT EXISTS idx_leads_assignable 
ON leads(organization_id, score DESC, created_at DESC) 
WHERE status IN ('new', 'contacted', 'qualified') AND assigned_to_id IS NULL;

-- ====================================
-- TIME-SERIES OPTIMIZATION
-- ====================================

-- Activity logs partitioning support (monthly partitions)
CREATE INDEX IF NOT EXISTS idx_activity_logs_monthly 
ON activity_logs(lead_id, created_at, activity_type) 
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days';

-- Lead score history for recent changes (performance tracking)
CREATE INDEX IF NOT EXISTS idx_lead_score_recent 
ON lead_score_history(lead_id, created_at DESC) 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';

-- Communication scheduling optimization
CREATE INDEX IF NOT EXISTS idx_communications_upcoming 
ON communications(user_id, scheduled_at) 
WHERE status = 'scheduled' AND scheduled_at >= CURRENT_TIMESTAMP;

-- ====================================
-- COVERING INDEXES FOR READ-HEAVY QUERIES
-- ====================================

-- Lead dashboard queries optimization
CREATE INDEX IF NOT EXISTS idx_leads_dashboard_summary 
ON leads(organization_id, status, assigned_to_id) 
INCLUDE (score, lead_temperature, source, created_at, updated_at, value);

-- User activity summary optimization
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_summary 
ON activity_logs(user_id, created_at DESC) 
INCLUDE (activity_type, description, lead_id);

-- Campaign performance summary
CREATE INDEX IF NOT EXISTS idx_campaign_leads_summary 
ON campaign_leads(campaign_id, status) 
INCLUDE (added_at, last_contact_at, response_at, conversion_at);

-- ====================================
-- FUNCTIONAL INDEXES FOR COMPUTED VALUES
-- ====================================

-- Full name search optimization
CREATE INDEX IF NOT EXISTS idx_leads_full_name_lower 
ON leads(LOWER(first_name || ' ' || last_name));

-- Domain extraction from email for company matching
CREATE INDEX IF NOT EXISTS idx_leads_email_domain 
ON leads(LOWER(SPLIT_PART(email, '@', 2)));

-- User full name search
CREATE INDEX IF NOT EXISTS idx_users_full_name_lower 
ON users(LOWER(first_name || ' ' || last_name));

-- ====================================
-- CONSTRAINT OPTIMIZATIONS
-- ====================================

-- Add constraint for data integrity (prevents negative scores)
ALTER TABLE leads ADD CONSTRAINT check_lead_score_range 
CHECK (score >= 0 AND score <= 100);

-- Add constraint for value field (prevents negative values)
ALTER TABLE leads ADD CONSTRAINT check_lead_value_positive 
CHECK (value IS NULL OR value >= 0);

-- Add constraint for campaign budget
ALTER TABLE campaigns ADD CONSTRAINT check_campaign_budget_positive 
CHECK (budget_allocated IS NULL OR budget_allocated >= 0);

ALTER TABLE campaigns ADD CONSTRAINT check_campaign_budget_spent_positive 
CHECK (budget_spent >= 0);

-- Add constraint for lead scoring rules
ALTER TABLE lead_scoring_rules ADD CONSTRAINT check_score_points_range 
CHECK (score_points >= -100 AND score_points <= 100);

-- ====================================
-- STATISTICS UPDATES
-- ====================================

-- Update table statistics for better query planning
ANALYZE leads;
ANALYZE communications;
ANALYZE organizations;
ANALYZE users;
ANALYZE workflow_executions;
ANALYZE activity_logs;
ANALYZE lead_score_history;
ANALYZE campaigns;
ANALYZE campaign_leads;

-- ====================================
-- VACUUM AND REINDEX MAINTENANCE
-- ====================================

-- Vacuum tables to reclaim space and update statistics
VACUUM ANALYZE leads;
VACUUM ANALYZE communications;
VACUUM ANALYZE activity_logs;
VACUUM ANALYZE workflow_executions;

-- ====================================
-- PERFORMANCE MONITORING VIEWS
-- ====================================

-- Create view for lead performance metrics
CREATE OR REPLACE VIEW v_lead_performance_summary AS
SELECT 
    l.organization_id,
    l.status,
    l.source,
    l.lead_temperature,
    COUNT(*) as lead_count,
    AVG(l.score) as avg_score,
    AVG(EXTRACT(days FROM NOW() - l.created_at)) as avg_age_days,
    COUNT(c.id) as communication_count,
    COUNT(CASE WHEN c.direction = 'outbound' THEN 1 END) as outbound_comms,
    COUNT(CASE WHEN c.direction = 'inbound' THEN 1 END) as inbound_comms
FROM leads l
LEFT JOIN communications c ON l.id = c.lead_id
WHERE l.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY l.organization_id, l.status, l.source, l.lead_temperature;

-- Create view for user activity metrics
CREATE OR REPLACE VIEW v_user_activity_summary AS
SELECT 
    u.id as user_id,
    u.organization_id,
    u.role,
    COUNT(DISTINCT al.id) as total_activities,
    COUNT(DISTINCT c.id) as communication_count,
    COUNT(DISTINCT l.id) as assigned_leads,
    MAX(al.created_at) as last_activity_date,
    COUNT(CASE WHEN al.created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as activities_last_week
FROM users u
LEFT JOIN activity_logs al ON u.id = al.user_id
LEFT JOIN communications c ON u.id = c.user_id
LEFT JOIN leads l ON u.id = l.assigned_to_id
WHERE u.is_active = true
GROUP BY u.id, u.organization_id, u.role;

-- Create view for organization health metrics
CREATE OR REPLACE VIEW v_organization_health AS
SELECT 
    o.id as organization_id,
    o.name,
    o.subscription_tier,
    COUNT(DISTINCT u.id) as active_users,
    COUNT(DISTINCT l.id) as total_leads,
    COUNT(CASE WHEN l.status IN ('new', 'contacted', 'qualified') THEN 1 END) as active_leads,
    COUNT(CASE WHEN l.status IN ('closed_won') THEN 1 END) as won_leads,
    AVG(l.score) as avg_lead_score,
    COUNT(DISTINCT c.id) as total_communications,
    COUNT(DISTINCT w.id) as active_workflows,
    MAX(al.created_at) as last_activity_date
FROM organizations o
LEFT JOIN users u ON o.id = u.organization_id AND u.is_active = true
LEFT JOIN leads l ON o.id = l.organization_id
LEFT JOIN communications c ON l.id = c.lead_id
LEFT JOIN workflows w ON o.id = w.organization_id AND w.is_active = true
LEFT JOIN activity_logs al ON l.id = al.lead_id
WHERE o.is_active = true
GROUP BY o.id, o.name, o.subscription_tier;

-- ====================================
-- MONITORING QUERIES FOR PERFORMANCE VALIDATION
-- ====================================

-- Example queries to test optimization effectiveness:

-- 1. Lead dashboard query (should use idx_leads_dashboard_summary)
-- SELECT organization_id, status, COUNT(*), AVG(score) 
-- FROM leads 
-- WHERE organization_id = 1 AND status IN ('new', 'contacted', 'qualified')
-- GROUP BY organization_id, status;

-- 2. User activity query (should use idx_activity_logs_user_summary)
-- SELECT activity_type, COUNT(*), MAX(created_at)
-- FROM activity_logs 
-- WHERE user_id = 1 AND created_at >= CURRENT_DATE - INTERVAL '30 days'
-- GROUP BY activity_type;

-- 3. Lead search query (should use idx_leads_full_name_lower)
-- SELECT id, first_name, last_name, email, company
-- FROM leads 
-- WHERE LOWER(first_name || ' ' || last_name) LIKE '%john%';

-- 4. JSON search query (should use idx_leads_tags_gin)
-- SELECT id, first_name, last_name, tags
-- FROM leads 
-- WHERE tags @> '["hot_lead"]';

COMMENT ON SCHEMA public IS 'LMA Platform optimized schema with comprehensive indexing strategy for high-performance lead management operations'; 