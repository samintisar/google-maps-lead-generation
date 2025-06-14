import { writable, derived, get as getStore } from 'svelte/store';
import { leadApi } from '$lib/api';
import type { Lead, LeadCreate, LeadUpdate, LeadFilters, ListResponse, LeadEnrichmentResponse, LeadEnrichmentStatus } from '$lib/types';

// Store state interface
interface LeadsState {
	leads: Lead[];
	currentLead: Lead | null;
	loading: {
		list: boolean;
		detail: boolean;
		create: boolean;
		update: boolean;
		delete: boolean;
		enrich: boolean;
	};
	error: string | null;
	pagination: {
		total: number;
		page: number;
		per_page: number;
		pages: number;
	};
	filters: LeadFilters;
}

// Initial state
const initialState: LeadsState = {
	leads: [],
	currentLead: null,
	loading: {
		list: false,
		detail: false,
		create: false,
		update: false,
		delete: false,
		enrich: false,
	},
	error: null,
	pagination: {
		total: 0,
		page: 1,
		per_page: 20,
		pages: 0,
	},
	filters: {
		skip: 0,
		limit: 20,
	},
};

// Create the main store
const { subscribe, set, update } = writable<LeadsState>(initialState);

// Helper function to show user-friendly error messages
function showError(message: string) {
	update(state => ({ ...state, error: message }));
	// Clear error after 5 seconds
	setTimeout(() => {
		update(state => ({ ...state, error: null }));
	}, 5000);
}

// Helper function to handle optimistic updates
function optimisticUpdate<T>(
	operation: () => Promise<T>,
	optimisticFn: (state: LeadsState) => LeadsState,
	rollbackFn: (state: LeadsState) => LeadsState,
	loadingKey: keyof LeadsState['loading']
) {
	return async (): Promise<T | null> => {
		try {
			// Set loading state
			update(state => ({
				...state,
				loading: { ...state.loading, [loadingKey]: true },
				error: null,
			}));

			// Apply optimistic update
			update(optimisticFn);

			// Perform actual operation
			const result = await operation();

			// Clear loading state
			update(state => ({
				...state,
				loading: { ...state.loading, [loadingKey]: false },
			}));

			return result;
		} catch (error) {
			// Rollback optimistic update
			update(rollbackFn);

			// Clear loading and show error
			update(state => ({
				...state,
				loading: { ...state.loading, [loadingKey]: false },
			}));

			const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
			showError(errorMessage);
			
			return null;
		}
	};
}

// Store actions
export const leadsStore = {
	subscribe,

	// Load leads with current filters
	async loadLeads(newFilters?: Partial<LeadFilters>) {
		try {
			update(state => ({
				...state,
				loading: { ...state.loading, list: true },
				error: null,
				filters: { ...state.filters, ...newFilters },
			}));

			const currentState = getStore(leadsStore);
			const leads = await leadApi.getLeads(currentState.filters);

			update(state => ({
				...state,
				leads,
				pagination: {
					total: leads.length,
					page: 1,
					per_page: leads.length,
					pages: 1,
				},
				loading: { ...state.loading, list: false },
			}));
		} catch (error) {
			update(state => ({
				...state,
				loading: { ...state.loading, list: false },
			}));

			const errorMessage = error instanceof Error ? error.message : 'Failed to load leads';
			showError(errorMessage);
		}
	},

	// Load a specific lead
	async loadLead(id: number) {
		try {
			update(state => ({
				...state,
				loading: { ...state.loading, detail: true },
				error: null,
			}));

			const lead = await leadApi.getLead(id);

			update(state => ({
				...state,
				currentLead: lead,
				loading: { ...state.loading, detail: false },
			}));

			return lead;
		} catch (error) {
			update(state => ({
				...state,
				currentLead: null,
				loading: { ...state.loading, detail: false },
			}));

			const errorMessage = error instanceof Error ? error.message : 'Failed to load lead';
			showError(errorMessage);
			return null;
		}
	},

	// Create a new lead with optimistic update
	async createLead(leadData: LeadCreate) {
		try {
			update(state => ({
				...state,
				loading: { ...state.loading, create: true },
				error: null,
			}));

			const result = await leadApi.createLead(leadData);

			update(state => ({
				...state,
				loading: { ...state.loading, create: false },
			}));

			// Reload leads to get the new lead with full data
			this.loadLeads();

			return result;
		} catch (error) {
			update(state => ({
				...state,
				loading: { ...state.loading, create: false },
			}));

			const errorMessage = error instanceof Error ? error.message : 'Failed to create lead';
			showError(errorMessage);
			return null;
		}
	},

	// Update a lead with optimistic update
	updateLead: (id: number, leadData: LeadUpdate) =>
		optimisticUpdate(
			() => leadApi.updateLead(id, leadData),
			(state) => ({
				...state,
				leads: state.leads.map(lead =>
					lead.id === id ? { ...lead, ...leadData } : lead
				),
				currentLead: state.currentLead?.id === id 
					? { ...state.currentLead, ...leadData } 
					: state.currentLead,
			}),
			(state) => {
				// Rollback by reloading leads
				leadsStore.loadLeads();
				if (state.currentLead?.id === id) {
					leadsStore.loadLead(id);
				}
				return state;
			},
			'update'
		)(),

	// Delete a lead with optimistic update
	deleteLead: (id: number) =>
		optimisticUpdate(
			() => leadApi.deleteLead(id),
			(state) => ({
				...state,
				leads: state.leads.filter(lead => lead.id !== id),
				currentLead: state.currentLead?.id === id ? null : state.currentLead,
			}),
			(state) => {
				// Rollback by reloading leads
				leadsStore.loadLeads();
				return state;
			},
			'delete'
		)(),

	// Update lead status
	async updateLeadStatus(id: number, status: string) {
		try {
			await leadApi.updateLead(id, { status: status as any });
			
			// Update local state
			update(state => ({
				...state,
				leads: state.leads.map(lead =>
					lead.id === id ? { ...lead, status: status as any } : lead
				),
				currentLead: state.currentLead?.id === id 
					? { ...state.currentLead, status: status as any } 
					: state.currentLead,
			}));
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : 'Failed to update lead status';
			showError(errorMessage);
		}
	},

	// Enrich a lead with Perplexity data
	async enrichLead(id: number): Promise<LeadEnrichmentResponse | null> {
		try {
			update(state => ({
				...state,
				loading: { ...state.loading, enrich: true },
				error: null,
			}));

			const response = await leadApi.enrichLead(id);

			// Update enrichment status in local state
			update(state => ({
				...state,
				leads: state.leads.map(lead =>
					lead.id === id ? { ...lead, enrichment_status: 'pending' } : lead
				),
				currentLead: state.currentLead?.id === id 
					? { ...state.currentLead, enrichment_status: 'pending' } 
					: state.currentLead,
				loading: { ...state.loading, enrich: false },
			}));

			return response;
		} catch (error) {
			update(state => ({
				...state,
				loading: { ...state.loading, enrich: false },
			}));

			const errorMessage = error instanceof Error ? error.message : 'Failed to enrich lead';
			showError(errorMessage);
			return null;
		}
	},

	// Get enrichment status for a lead
	async getEnrichmentStatus(id: number): Promise<LeadEnrichmentStatus | null> {
		try {
			const status = await leadApi.getEnrichmentStatus(id);
			return status;
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : 'Failed to get enrichment status';
			showError(errorMessage);
			return null;
		}
	},

	// Poll for enrichment completion
	async pollEnrichmentStatus(id: number, maxAttempts: number = 30): Promise<boolean> {
		let attempts = 0;
		
		while (attempts < maxAttempts) {
			const status = await this.getEnrichmentStatus(id);
			
			if (status?.enrichment_status === 'completed') {
				// Reload the lead to get updated enrichment data
				await this.loadLead(id);
				return true;
			} else if (status?.enrichment_status === 'failed') {
				showError('Lead enrichment failed. Please try again.');
				return false;
			}
			
			// Wait 2 seconds before next poll
			await new Promise(resolve => setTimeout(resolve, 2000));
			attempts++;
		}
		
		showError('Lead enrichment is taking longer than expected. Please check back later.');
		return false;
	},



	// Set current lead
	setCurrentLead(lead: Lead | null) {
		update(state => ({ ...state, currentLead: lead }));
	},

	// Clear error
	clearError() {
		update(state => ({ ...state, error: null }));
	},

	// Update filters
	setFilters(newFilters: Partial<LeadFilters>) {
		update(state => ({
			...state,
			filters: { ...state.filters, ...newFilters },
		}));
	},

	// Reset store to initial state
	reset() {
		set(initialState);
	},
};

// Helper function to get current state
function get(store: typeof leadsStore): LeadsState {
	let state: LeadsState;
	store.subscribe(s => state = s)();
	return state!;
}

// Derived stores for convenient access
export const leads = derived(leadsStore, state => state.leads);
export const currentLead = derived(leadsStore, state => state.currentLead);
export const leadsLoading = derived(leadsStore, state => state.loading);
export const leadsError = derived(leadsStore, state => state.error);
export const leadsPagination = derived(leadsStore, state => state.pagination);
export const leadsFilters = derived(leadsStore, state => state.filters); 