import { goto } from '$app/navigation';
import { auth } from './stores/auth';
import { config, getApiUrl } from './config';
import type { 
	Lead, LeadCreate, LeadUpdate, LeadFilters, ApiResponse, ListResponse,
	DashboardMetrics, RevenueMetrics, FunnelMetrics
} from './types';

// Helper function to get auth headers for API requests
function getAuthHeaders(): HeadersInit {
	const token = auth.getToken();
	const headers: HeadersInit = {
		'Content-Type': 'application/json',
	};
	
	if (token) {
		headers['Authorization'] = `Bearer ${token}`;
	}
	
	return headers;
}

// Enhanced error handling for API responses
async function handleApiResponse<T>(response: Response): Promise<T> {
	if (!response.ok) {
		const contentType = response.headers.get('content-type');
		let errorData: any = {};
		
		try {
			if (contentType && contentType.includes('application/json')) {
				errorData = await response.json();
			} else {
				errorData = { message: await response.text() || `HTTP ${response.status} error` };
			}
		} catch {
			errorData = { message: `HTTP ${response.status}: ${response.statusText}` };
		}

		// Handle authentication errors
		if (response.status === 401 || response.status === 403) {
			if (config.features.enableDebugLogging) {
				console.warn('Authentication error, redirecting to login');
			}
			auth.logout();
			throw new Error('Authentication required. Please log in again.');
		}

		// Handle other HTTP errors
		const errorMessage = errorData.message || errorData.detail || `HTTP ${response.status} error`;
		throw new Error(errorMessage);
	}

	return response.json();
}

// Generic API request function with timeout support
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
	const url = getApiUrl(endpoint);
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), config.api.timeout);

	const requestConfig: RequestInit = {
		...options,
		headers: {
			...getAuthHeaders(),
			...options.headers,
		},
		signal: controller.signal,
	};

	try {
		if (config.features.enableDebugLogging) {
			console.log(`API Request: ${options.method || 'GET'} ${url}`);
		}

		const response = await fetch(url, requestConfig);
		clearTimeout(timeoutId);
		
		const result = await handleApiResponse<T>(response);
		
		if (config.features.enableDebugLogging) {
			console.log(`API Response: ${url}`, result);
		}
		
		return result;
	} catch (error) {
		clearTimeout(timeoutId);
		
		if (error instanceof Error && error.name === 'AbortError') {
			throw new Error('Request timeout. Please try again.');
		}
		
		if (config.features.enableDebugLogging) {
			console.error(`API request failed: ${endpoint}`, error);
		}
		
		throw error;
	}
}

// Helper function to decide which endpoint to use (dev vs authenticated)
function getEndpoint(authPath: string, devPath: string): string {
	return config.features.useDevEndpoints ? devPath : authPath;
}

// Generic API object for custom endpoints - handles absolute URLs directly
export const api = {
	get: <T>(endpoint: string) => {
		// If endpoint starts with /api, use it directly without getApiUrl
		const url = endpoint.startsWith('/api') ? 
			endpoint.replace('/api', config.api.baseUrl) : 
			getApiUrl(endpoint);
		return fetch(url, { 
			method: 'GET',
			headers: getAuthHeaders()
		}).then(handleApiResponse<T>);
	},
	post: <T>(endpoint: string, body?: any) => {
		const url = endpoint.startsWith('/api') ? 
			endpoint.replace('/api', config.api.baseUrl) : 
			getApiUrl(endpoint);
		return fetch(url, { 
			method: 'POST',
			headers: getAuthHeaders(),
			body: body ? JSON.stringify(body) : undefined 
		}).then(handleApiResponse<T>);
	},
	put: <T>(endpoint: string, body?: any) => {
		const url = endpoint.startsWith('/api') ? 
			endpoint.replace('/api', config.api.baseUrl) : 
			getApiUrl(endpoint);
		return fetch(url, { 
			method: 'PUT',
			headers: getAuthHeaders(),
			body: body ? JSON.stringify(body) : undefined 
		}).then(handleApiResponse<T>);
	},
	patch: <T>(endpoint: string, body?: any) => {
		const url = endpoint.startsWith('/api') ? 
			endpoint.replace('/api', config.api.baseUrl) : 
			getApiUrl(endpoint);
		return fetch(url, { 
			method: 'PATCH',
			headers: getAuthHeaders(),
			body: body ? JSON.stringify(body) : undefined 
		}).then(handleApiResponse<T>);
	},
	delete: <T>(endpoint: string) => {
		const url = endpoint.startsWith('/api') ? 
			endpoint.replace('/api', config.api.baseUrl) : 
			getApiUrl(endpoint);
		return fetch(url, { 
			method: 'DELETE',
			headers: getAuthHeaders()
		}).then(handleApiResponse<T>);
	}
};

// Lead API functions
export const leadApi = {
	// Get leads with filtering and pagination
	async getLeads(filters: LeadFilters = {}): Promise<ListResponse<Lead>> {
		const searchParams = new URLSearchParams();
		
		if (filters.skip !== undefined) searchParams.set('skip', filters.skip.toString());
		if (filters.limit !== undefined) searchParams.set('limit', filters.limit.toString());
		if (filters.status_filter) searchParams.set('status_filter', filters.status_filter);
		if (filters.source_filter) searchParams.set('source_filter', filters.source_filter);
		if (filters.search) searchParams.set('search', filters.search);
		if (filters.assigned_to_id) searchParams.set('assigned_to_id', filters.assigned_to_id.toString());

		const queryString = searchParams.toString();
		const endpoint = getEndpoint(
			`leads${queryString ? `?${queryString}` : ''}`,
			`leads/dev${queryString ? `?${queryString}` : ''}`
		);
		
		return apiRequest<ListResponse<Lead>>(endpoint);
	},

	// Get a specific lead by ID
	async getLead(id: number): Promise<Lead> {
		const endpoint = getEndpoint(`leads/${id}`, `leads/dev/${id}`);
		return apiRequest<Lead>(endpoint);
	},

	// Create a new lead
	async createLead(leadData: LeadCreate): Promise<ApiResponse<Lead>> {
		const endpoint = getEndpoint('leads', 'leads/dev');
		return apiRequest<ApiResponse<Lead>>(endpoint, {
			method: 'POST',
			body: JSON.stringify(leadData),
		});
	},

	// Update an existing lead
	async updateLead(id: number, leadData: LeadUpdate): Promise<ApiResponse<Lead>> {
		const endpoint = getEndpoint(`leads/${id}`, `leads/dev/${id}`);
		return apiRequest<ApiResponse<Lead>>(endpoint, {
			method: 'PUT',
			body: JSON.stringify(leadData),
		});
	},

	// Delete a lead
	async deleteLead(id: number): Promise<ApiResponse> {
		const endpoint = getEndpoint(`leads/${id}`, `leads/delete-test/${id}`);
		const method = config.features.useDevEndpoints ? 'GET' : 'DELETE';
		return apiRequest<ApiResponse>(endpoint, { method });
	},

	// Update lead status
	async updateLeadStatus(id: number, status: string): Promise<ApiResponse> {
		const endpoint = getEndpoint(`leads/${id}/status`, `leads/dev/${id}/status`);
		return apiRequest<ApiResponse>(endpoint, {
			method: 'PATCH',
			body: JSON.stringify({ new_status: status }),
		});
	},

	// Assign lead to user
	async assignLead(id: number, userId: number): Promise<ApiResponse> {
		const endpoint = getEndpoint(`leads/${id}/assign`, `leads/dev/${id}/assign`);
		return apiRequest<ApiResponse>(endpoint, {
			method: 'PATCH',
			body: JSON.stringify({ user_id: userId }),
		});
	},

	// Get lead score history
	async getLeadScoreHistory(id: number, limit: number = 10): Promise<ApiResponse> {
		const endpoint = getEndpoint(
			`leads/${id}/score/history?limit=${limit}`,
			`leads/dev/${id}/score/history?limit=${limit}`
		);
		return apiRequest<ApiResponse>(endpoint);
	},
};

// Metrics API functions
export const metricsApi = {
	// Get comprehensive dashboard metrics
	async getDashboardMetrics(daysBack: number = 30): Promise<ApiResponse<DashboardMetrics>> {
		const endpoint = getEndpoint(
			`metrics/dashboard?days_back=${daysBack}`,
			`metrics/dev/dashboard?days_back=${daysBack}`
		);
		return apiRequest<ApiResponse<DashboardMetrics>>(endpoint);
	},

	// Get detailed revenue metrics
	async getRevenueMetrics(daysBack: number = 90, groupBy: string = 'month'): Promise<ApiResponse<RevenueMetrics>> {
		const endpoint = getEndpoint(
			`metrics/revenue?days_back=${daysBack}&group_by=${groupBy}`,
			`metrics/dev/revenue?days_back=${daysBack}&group_by=${groupBy}`
		);
		return apiRequest<ApiResponse<RevenueMetrics>>(endpoint);
	},

	// Get sales funnel metrics
	async getFunnelMetrics(daysBack: number = 30): Promise<ApiResponse<FunnelMetrics>> {
		const endpoint = getEndpoint(
			`metrics/funnel?days_back=${daysBack}`,
			`metrics/dev/funnel?days_back=${daysBack}`
		);
		return apiRequest<ApiResponse<FunnelMetrics>>(endpoint);
	}
};

// Authentication API functions
export const authApi = {
	// Login with credentials
	async login(username: string, password: string): Promise<{ access_token: string; user: any }> {
		return apiRequest<{ access_token: string; user: any }>('auth/login', {
			method: 'POST',
			body: JSON.stringify({ username, password }),
		});
	},

	// Register new user
	async register(userData: {
		username: string;
		email: string;
		password: string;
		first_name?: string;
		last_name?: string;
		role?: string;
		organization_id?: number;
	}): Promise<{ success: boolean; data: any; access_token: string }> {
		return apiRequest<{ success: boolean; data: any; access_token: string }>('auth/register', {
			method: 'POST',
			body: JSON.stringify(userData),
		});
	},

	// Get current user info
	async getCurrentUser(): Promise<any> {
		return apiRequest<any>('auth/me');
	},

	// Logout (if backend endpoint exists)
	async logout(): Promise<void> {
		try {
			await apiRequest<void>('auth/logout', { method: 'POST' });
		} catch (error) {
			// Ignore logout errors as we'll clear local storage anyway
			if (config.features.enableDebugLogging) {
				console.warn('Logout API call failed:', error);
			}
		}
	},
};

// Export individual functions for convenience
export const {
	getLeads,
	getLead,
	createLead,
	updateLead,
	deleteLead,
	updateLeadStatus,
	assignLead,
	getLeadScoreHistory,
} = leadApi;

export const {
	getDashboardMetrics,
	getRevenueMetrics,
	getFunnelMetrics,
} = metricsApi;

export const {
	login,
	register,
	getCurrentUser,
	logout,
} = authApi; 