"""Add schema tables manually with existing enums

Revision ID: 0300ecf06a9b
Revises: b51d12408c9f
Create Date: 2024-11-25 21:52:03.502618

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0300ecf06a9b'
down_revision: Union[str, None] = 'b51d12408c9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create lead_scoring_rules table
    op.execute("""
        CREATE TABLE lead_scoring_rules (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            rule_type VARCHAR(50) NOT NULL,
            criteria JSON NOT NULL,
            score_points INTEGER NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            priority INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_lead_scoring_rules_id ON lead_scoring_rules(id);
        CREATE INDEX ix_lead_scoring_rules_rule_type ON lead_scoring_rules(rule_type);
    """)

    # Create campaigns table with existing campaignstatus enum
    op.execute("""
        CREATE TABLE campaigns (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            campaign_type VARCHAR(100),
            status campaignstatus NOT NULL DEFAULT 'draft',
            target_criteria JSON NOT NULL DEFAULT '{}',
            start_date DATE,
            end_date DATE,
            budget_allocated INTEGER,
            budget_spent INTEGER NOT NULL DEFAULT 0,
            goals JSON NOT NULL DEFAULT '{}',
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_campaigns_id ON campaigns(id);
        CREATE INDEX ix_campaigns_campaign_type ON campaigns(campaign_type);
        CREATE INDEX ix_campaigns_status ON campaigns(status);
    """)

    # Create integrations table with existing integrationstatus enum
    op.execute("""
        CREATE TABLE integrations (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            integration_type VARCHAR(100) NOT NULL,
            provider_name VARCHAR(100) NOT NULL,
            display_name VARCHAR(255),
            configuration JSON NOT NULL DEFAULT '{}',
            status integrationstatus NOT NULL DEFAULT 'inactive',
            last_sync_at TIMESTAMP WITH TIME ZONE,
            sync_frequency_minutes INTEGER NOT NULL DEFAULT 60,
            error_message TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_integrations_id ON integrations(id);
        CREATE INDEX ix_integrations_integration_type ON integrations(integration_type);
        CREATE INDEX ix_integrations_status ON integrations(status);
    """)

    # Create workflows table
    op.execute("""
        CREATE TABLE workflows (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            n8n_workflow_id VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            category VARCHAR(100),
            trigger_type VARCHAR(100),
            trigger_conditions JSON NOT NULL DEFAULT '{}',
            configuration JSON NOT NULL DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_workflows_id ON workflows(id);
        CREATE INDEX ix_workflows_category ON workflows(category);
        CREATE UNIQUE INDEX ix_workflows_n8n_workflow_id ON workflows(n8n_workflow_id);
        CREATE INDEX ix_workflows_trigger_type ON workflows(trigger_type);
    """)

    # Create campaign_leads table
    op.execute("""
        CREATE TABLE campaign_leads (
            id SERIAL PRIMARY KEY,
            campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
            lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
            status VARCHAR(50) NOT NULL DEFAULT 'added',
            added_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            last_contact_at TIMESTAMP WITH TIME ZONE,
            response_at TIMESTAMP WITH TIME ZONE,
            conversion_at TIMESTAMP WITH TIME ZONE
        );
        CREATE INDEX ix_campaign_leads_id ON campaign_leads(id);
        CREATE INDEX ix_campaign_leads_status ON campaign_leads(status);
    """)

    # Create communications table with existing enums
    op.execute("""
        CREATE TABLE communications (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            communication_type communicationtype NOT NULL,
            direction communicationdirection NOT NULL,
            subject VARCHAR(500),
            content TEXT,
            status communicationstatus NOT NULL DEFAULT 'scheduled',
            scheduled_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            comm_metadata JSON NOT NULL DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_communications_id ON communications(id);
        CREATE INDEX ix_communications_communication_type ON communications(communication_type);
        CREATE INDEX ix_communications_scheduled_at ON communications(scheduled_at);
    """)

    # Create lead_assignments table
    op.execute("""
        CREATE TABLE lead_assignments (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
            assigned_from INTEGER REFERENCES users(id) ON DELETE SET NULL,
            assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
            assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            reason VARCHAR(500),
            assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_lead_assignments_id ON lead_assignments(id);
    """)

    # Create lead_notes table
    op.execute("""
        CREATE TABLE lead_notes (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            note_type VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            is_private BOOLEAN NOT NULL DEFAULT false,
            mentioned_users INTEGER[],
            attachments JSON NOT NULL DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_lead_notes_id ON lead_notes(id);
        CREATE INDEX ix_lead_notes_note_type ON lead_notes(note_type);
    """)

    # Create lead_score_history table
    op.execute("""
        CREATE TABLE lead_score_history (
            id SERIAL PRIMARY KEY,
            lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
            previous_score INTEGER NOT NULL,
            new_score INTEGER NOT NULL,
            score_change INTEGER NOT NULL,
            reason VARCHAR(500),
            rule_id INTEGER REFERENCES lead_scoring_rules(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_lead_score_history_id ON lead_score_history(id);
    """)

    # Add new columns to existing tables
    op.execute("""
        ALTER TABLE leads 
        ADD COLUMN linkedin_url VARCHAR(500),
        ADD COLUMN lead_temperature leadtemperature NOT NULL DEFAULT 'warm',
        ADD COLUMN expected_close_date DATE,
        ADD COLUMN last_engagement_date TIMESTAMP WITH TIME ZONE;
    """)

    op.execute("""
        ALTER TABLE organizations 
        ADD COLUMN subscription_tier VARCHAR(50) NOT NULL DEFAULT 'free',
        ADD COLUMN billing_email VARCHAR(255);
    """)

    op.execute("""
        ALTER TABLE users 
        ADD COLUMN timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
        ADD COLUMN preferences JSON NOT NULL DEFAULT '{}',
        ADD COLUMN avatar_url VARCHAR(500);
    """)


def downgrade() -> None:
    # Remove added columns
    op.execute("ALTER TABLE users DROP COLUMN avatar_url, DROP COLUMN preferences, DROP COLUMN timezone;")
    op.execute("ALTER TABLE organizations DROP COLUMN billing_email, DROP COLUMN subscription_tier;")
    op.execute("ALTER TABLE leads DROP COLUMN last_engagement_date, DROP COLUMN expected_close_date, DROP COLUMN lead_temperature, DROP COLUMN linkedin_url;")
    
    # Drop tables in reverse dependency order
    op.execute("DROP TABLE IF EXISTS lead_score_history CASCADE;")
    op.execute("DROP TABLE IF EXISTS lead_notes CASCADE;")
    op.execute("DROP TABLE IF EXISTS lead_assignments CASCADE;")
    op.execute("DROP TABLE IF EXISTS communications CASCADE;")
    op.execute("DROP TABLE IF EXISTS campaign_leads CASCADE;")
    op.execute("DROP TABLE IF EXISTS workflows CASCADE;")
    op.execute("DROP TABLE IF EXISTS integrations CASCADE;")
    op.execute("DROP TABLE IF EXISTS campaigns CASCADE;")
    op.execute("DROP TABLE IF EXISTS lead_scoring_rules CASCADE;")
