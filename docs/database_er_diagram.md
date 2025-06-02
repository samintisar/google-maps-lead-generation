# Database Entity-Relationship Diagram

## LMA Platform - Complete ER Diagram

```mermaid
erDiagram
    %% Core Entities
    Organization {
        int id PK
        string name
        string slug UK
        text description
        string website
        string industry
        string size
        json settings
        string subscription_tier
        string billing_email
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    User {
        int id PK
        string email UK
        string username UK
        string first_name
        string last_name
        string hashed_password
        enum role
        boolean is_active
        boolean is_verified
        string timezone
        json preferences
        string avatar_url
        timestamp created_at
        timestamp updated_at
        timestamp last_login
        int organization_id FK
    }

    Lead {
        int id PK
        string email
        string first_name
        string last_name
        string company
        string job_title
        string phone
        string website
        string linkedin_url
        enum status
        enum source
        string lead_temperature
        int score
        int value
        text notes
        json tags
        json custom_fields
        date expected_close_date
        timestamp first_contacted_at
        timestamp last_contacted_at
        timestamp last_engagement_date
        timestamp created_at
        timestamp updated_at
        int organization_id FK
        int assigned_to_id FK
    }

    %% Workflow System
    Workflow {
        int id PK
        string n8n_workflow_id UK
        string name
        text description
        string category
        string trigger_type
        json trigger_conditions
        json configuration
        boolean is_active
        timestamp created_at
        timestamp updated_at
        int organization_id FK
        int created_by FK
    }

    WorkflowExecution {
        int id PK
        string workflow_id
        string execution_id
        string status
        timestamp started_at
        timestamp finished_at
        text error_message
        json execution_data
        int lead_id FK
    }

    %% Lead Scoring System
    LeadScoringRule {
        int id PK
        string name
        text description
        string rule_type
        json criteria
        int score_points
        boolean is_active
        int priority
        timestamp created_at
        timestamp updated_at
        int organization_id FK
    }

    LeadScoreHistory {
        int id PK
        int previous_score
        int new_score
        int score_change
        string reason
        timestamp created_at
        int lead_id FK
        int rule_id FK
    }

    %% Communication System
    Communication {
        int id PK
        string communication_type
        string direction
        string subject
        text content
        string status
        timestamp scheduled_at
        timestamp completed_at
        json metadata
        timestamp created_at
        timestamp updated_at
        int lead_id FK
        int user_id FK
    }

    LeadNote {
        int id PK
        string note_type
        text content
        boolean is_private
        int[] mentioned_users
        json attachments
        timestamp created_at
        timestamp updated_at
        int lead_id FK
        int user_id FK
    }

    %% Campaign System
    Campaign {
        int id PK
        string name
        text description
        string campaign_type
        string status
        json target_criteria
        date start_date
        date end_date
        int budget_allocated
        int budget_spent
        json goals
        timestamp created_at
        timestamp updated_at
        int organization_id FK
        int created_by FK
    }

    CampaignLead {
        int id PK
        string status
        timestamp added_at
        timestamp last_contact_at
        timestamp response_at
        timestamp conversion_at
        int campaign_id FK
        int lead_id FK
    }

    %% Integration System
    Integration {
        int id PK
        string integration_type
        string provider_name
        string display_name
        json configuration
        string status
        timestamp last_sync_at
        int sync_frequency_minutes
        text error_message
        timestamp created_at
        timestamp updated_at
        int organization_id FK
        int created_by FK
    }

    %% Activity Tracking
    ActivityLog {
        int id PK
        string activity_type
        string description
        json activity_metadata
        timestamp created_at
        int lead_id FK
        int user_id FK
    }

    LeadAssignment {
        int id PK
        string reason
        timestamp assigned_at
        int lead_id FK
        int assigned_from FK
        int assigned_to FK
        int assigned_by FK
    }

    %% Relationships
    Organization ||--o{ User : "has"
    Organization ||--o{ Lead : "contains"
    Organization ||--o{ Workflow : "owns"
    Organization ||--o{ Campaign : "runs"
    Organization ||--o{ LeadScoringRule : "defines"
    Organization ||--o{ Integration : "configures"

    User ||--o{ Lead : "assigned_to"
    User ||--o{ Communication : "performs"
    User ||--o{ LeadNote : "creates"
    User ||--o{ Workflow : "creates"
    User ||--o{ Campaign : "creates"
    User ||--o{ Integration : "creates"
    User ||--o{ ActivityLog : "performs"
    User ||--o{ LeadAssignment : "assigned_from"
    User ||--o{ LeadAssignment : "assigned_to"
    User ||--o{ LeadAssignment : "assigned_by"

    Lead ||--o{ Communication : "receives"
    Lead ||--o{ LeadNote : "has"
    Lead ||--o{ WorkflowExecution : "triggers"
    Lead ||--o{ ActivityLog : "generates"
    Lead ||--o{ LeadScoreHistory : "tracks"
    Lead ||--o{ LeadAssignment : "history"
    Lead ||--o{ CampaignLead : "participates"

    Workflow ||--o{ WorkflowExecution : "executes"

    LeadScoringRule ||--o{ LeadScoreHistory : "applies"

    Campaign ||--o{ CampaignLead : "includes"
```

## Entity Descriptions

### Core Business Entities

#### Organization
- **Purpose**: Multi-tenant isolation and configuration
- **Key Features**: Subscription management, settings, billing
- **Relationships**: Root entity for all organizational data

#### User
- **Purpose**: Authentication, authorization, and user management
- **Key Features**: Role-based access, preferences, activity tracking
- **Relationships**: Belongs to organization, assigned to leads

#### Lead
- **Purpose**: Central entity for prospect management
- **Key Features**: Contact info, scoring, status tracking, engagement history
- **Relationships**: Core entity connected to most other tables

### Workflow & Automation

#### Workflow
- **Purpose**: n8n workflow template/definition storage
- **Key Features**: Trigger configuration, categorization, status management
- **Relationships**: Links to executions, owned by organization

#### WorkflowExecution
- **Purpose**: Track individual workflow runs and results
- **Key Features**: Status tracking, error handling, execution data
- **Relationships**: Links workflow templates to specific leads

### Lead Management & Scoring

#### LeadScoringRule
- **Purpose**: Define flexible scoring criteria and algorithms
- **Key Features**: JSON-based criteria, priority weighting, rule types
- **Relationships**: Organization-specific, applied to lead scoring

#### LeadScoreHistory
- **Purpose**: Audit trail for score changes over time
- **Key Features**: Score change tracking, reason logging, rule attribution
- **Relationships**: Tracks lead score evolution with rule references

### Communication & Engagement

#### Communication
- **Purpose**: Comprehensive communication history across all channels
- **Key Features**: Multi-channel support, scheduling, status tracking
- **Relationships**: Links users, leads, and communication events

#### LeadNote
- **Purpose**: Detailed notes, research, and collaboration on leads
- **Key Features**: Type categorization, privacy controls, mentions, attachments
- **Relationships**: User-created content linked to specific leads

### Campaign Management

#### Campaign
- **Purpose**: Organize and track marketing/outreach campaigns
- **Key Features**: Budget tracking, target criteria, performance goals
- **Relationships**: Organization-owned, user-created, includes multiple leads

#### CampaignLead
- **Purpose**: Many-to-many relationship between campaigns and leads
- **Key Features**: Status tracking, timeline management, conversion tracking
- **Relationships**: Junction table with temporal tracking

### Integration & External Systems

#### Integration
- **Purpose**: Manage connections to external systems (CRM, email, etc.)
- **Key Features**: Configuration storage, sync management, error handling
- **Relationships**: Organization-specific integrations with user attribution

### Activity & Audit

#### ActivityLog
- **Purpose**: General activity tracking and audit trail
- **Key Features**: Flexible metadata, activity categorization
- **Relationships**: Links users and leads to specific activities

#### LeadAssignment
- **Purpose**: Track lead ownership changes over time
- **Key Features**: Assignment history, reason tracking, user attribution
- **Relationships**: Historical record of lead ownership changes

## Data Flow Patterns

### Lead Lifecycle Flow
1. **Lead Creation** → Lead table entry
2. **Initial Scoring** → LeadScoringRule evaluation → LeadScoreHistory entry
3. **Assignment** → LeadAssignment entry → User assignment
4. **Communication** → Communication entries → ActivityLog entries
5. **Workflow Triggers** → WorkflowExecution entries
6. **Campaign Association** → CampaignLead entries
7. **Notes & Research** → LeadNote entries
8. **Score Updates** → LeadScoreHistory entries

### Campaign Flow
1. **Campaign Setup** → Campaign table entry
2. **Lead Targeting** → CampaignLead entries based on target_criteria
3. **Communication Execution** → Communication entries
4. **Response Tracking** → CampaignLead status updates
5. **Performance Analysis** → Aggregated reporting from related tables

### Integration Sync Flow
1. **Integration Setup** → Integration table entry
2. **Scheduled Sync** → External system data pull/push
3. **Lead Updates** → Lead table modifications
4. **Activity Logging** → ActivityLog entries for sync activities
5. **Error Handling** → Integration table error_message updates

## Performance Considerations

### Query Optimization Patterns
- **Lead Dashboard**: Organization-scoped lead queries with status/score filtering
- **Activity Timeline**: Time-based queries across Communication, ActivityLog, LeadNote
- **Campaign Performance**: Aggregation queries across Campaign and CampaignLead
- **Scoring Analysis**: Historical scoring trends via LeadScoreHistory

### Index Strategy
- **Foreign Keys**: All FK columns indexed for JOIN performance
- **Composite Indexes**: Multi-column indexes for common filter combinations
- **Partial Indexes**: Filtered indexes for active/non-null records
- **Time-based Indexes**: Descending indexes on timestamp columns for recent-first queries

This ER diagram provides a comprehensive view of the LMA platform's data architecture, supporting complex lead management workflows while maintaining performance and scalability. 