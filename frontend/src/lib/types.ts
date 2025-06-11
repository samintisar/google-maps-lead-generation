// Lead types based on backend schemas
export interface Lead {
	id: number;
	first_name: string;
	last_name: string;
	email: string;
	phone?: string;
	company?: string;
	job_title?: string;
	industry?: string;
	website?: string;
	address?: string;
	city?: string;
	state?: string;
	postal_code?: string;
	country?: string;
	source: LeadSource;
	status: LeadStatus;
	score: number;
	lead_temperature?: string;
	interest_level: number;
	budget?: number;
	timeline?: string;
	needs?: string;
	pain_points?: string;
	preferred_contact_method?: string;
	tags?: string[];
	custom_fields?: Record<string, any>;
	notes?: string;
	organization_id: number;
	assigned_to_id?: number;
	last_engagement_date?: string;
	first_contacted_at?: string;
	last_contacted_at?: string;
	created_at: string;
	updated_at: string;
	organization?: Organization;
	assigned_to?: User;
}

export interface LeadCreate {
	first_name: string;
	last_name: string;
	email: string;
	phone?: string;
	company?: string;
	job_title?: string;
	industry?: string;
	website?: string;
	address?: string;
	city?: string;
	state?: string;
	postal_code?: string;
	country?: string;
	source: LeadSource;
	status?: LeadStatus;
	interest_level?: number;
	budget?: number;
	timeline?: string;
	needs?: string;
	pain_points?: string;
	preferred_contact_method?: string;
	tags?: string[];
	custom_fields?: Record<string, any>;
	notes?: string;
	organization_id: number;
	assigned_to_id?: number;
}

export interface LeadUpdate {
	first_name?: string;
	last_name?: string;
	email?: string;
	phone?: string;
	company?: string;
	job_title?: string;
	industry?: string;
	website?: string;
	address?: string;
	city?: string;
	state?: string;
	postal_code?: string;
	country?: string;
	source?: LeadSource;
	status?: LeadStatus;
	interest_level?: number;
	budget?: number;
	timeline?: string;
	needs?: string;
	pain_points?: string;
	preferred_contact_method?: string;
	tags?: string[];
	custom_fields?: Record<string, any>;
	notes?: string;
	assigned_to_id?: number;
}

export enum LeadStatus {
	NEW = 'new',
	CONTACTED = 'contacted',
	QUALIFIED = 'qualified',
	PROPOSAL = 'proposal',
	NEGOTIATION = 'negotiation',
	WON = 'won',
	LOST = 'lost',
	NURTURING = 'nurturing',
	UNRESPONSIVE = 'unresponsive'
}

export enum LeadSource {
	WEBSITE = 'website',
	REFERRAL = 'referral',
	SOCIAL_MEDIA = 'social_media',
	EMAIL_CAMPAIGN = 'email_campaign',
	COLD_OUTREACH = 'cold_outreach',
	EVENT = 'event',
	ADVERTISEMENT = 'advertisement',
	ORGANIC_SEARCH = 'organic_search',
	PAID_SEARCH = 'paid_search',
	PARTNER = 'partner',
	OTHER = 'other'
}

// User and Organization types
export interface User {
	id: number;
	email: string;
	username: string;
	full_name: string;
	organization_id?: number;
	is_active: boolean;
	created_at: string;
	updated_at: string;
}

export interface Organization {
	id: number;
	name: string;
	website?: string;
	industry?: string;
	size?: string;
	is_active: boolean;
	created_at: string;
	updated_at: string;
}

// API Response types
export interface ApiResponse<T = any> {
	success: boolean;
	data?: T;
	message?: string;
	error?: string;
}

export interface ListResponse<T = any> {
	items: T[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

// Lead filtering and search
export interface LeadFilters {
	skip?: number;
	limit?: number;
	status_filter?: LeadStatus;
	source_filter?: LeadSource;
	search?: string;
	assigned_to_id?: number;
}

// Metrics types for SaaS dashboard
export interface DashboardMetrics {
	overview: {
		total_leads: number;
		new_leads: number;
		qualified_leads: number;
		won_leads: number;
		lost_leads: number;
		qualification_rate: number;
		win_rate: number;
		total_revenue: number;
		avg_deal_size: number;
		deals_count: number;
		total_activities: number;
		period_days: number;
	};
	lead_distribution: {
		by_status: Array<{ status: string; count: number }>;
		by_source: Array<{ source: string; count: number }>;
	};
	score_analytics: {
		avg_score: number;
		max_score: number;
		min_score: number;
	};
	communication_metrics: {
		total_communications: number;
		outbound_count: number;
		inbound_count: number;
	};
	time_series: {
		daily_leads: Array<{ date: string; count: number }>;
		score_trend: Array<{ date: string; avg_score: number }>;
	};
	team_performance: Array<{
		user_id: number;
		name: string;
		leads_assigned: number;
		leads_won: number;
		revenue_generated: number;
		win_rate: number;
	}>;
	campaign_performance: Array<{
		campaign_id: number;
		name: string;
		status: string;
		total_leads: number;
		converted_leads: number;
		conversion_rate: number;
		budget_allocated: number;
		budget_spent: number;
		budget_utilization: number;
	}>;
}

export interface RevenueMetrics {
	revenue_trend: Array<{
		period: string;
		revenue: number;
		deals_count: number;
		avg_deal_size: number;
	}>;
	revenue_by_source: Array<{
		source: string;
		revenue: number;
		deals_count: number;
	}>;
	group_by: string;
	period_days: number;
}

export interface FunnelMetrics {
	funnel_stages: Array<{
		stage: string;
		count: number;
		conversion_rate: number;
		stage_conversion: number;
	}>;
	total_leads: number;
	period_days: number;
} 