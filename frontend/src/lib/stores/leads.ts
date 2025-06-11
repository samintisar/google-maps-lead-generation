import { writable, derived } from 'svelte/store';
import { leadApi } from '$lib/api';
import type { Lead, LeadCreate, LeadUpdate, LeadFilters, ListResponse } from '$lib/types';

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

			const currentState = get(leadsStore);
			const response: ListResponse<Lead> = await leadApi.getLeads(currentState.filters);

			update(state => ({
				...state,
				leads: response.items,
				pagination: {
					total: response.total,
					page: response.page,
					per_page: response.per_page,
					pages: response.pages,
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
			await leadApi.updateLeadStatus(id, status);
			
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

	// Assign lead to user
	async assignLead(id: number, userId: number) {
		try {
			await leadApi.assignLead(id, userId);
			
			// Update local state
			update(state => ({
				...state,
				leads: state.leads.map(lead =>
					lead.id === id ? { ...lead, assigned_to_id: userId } : lead
				),
				currentLead: state.currentLead?.id === id 
					? { ...state.currentLead, assigned_to_id: userId } 
					: state.currentLead,
			}));
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : 'Failed to assign lead';
			showError(errorMessage);
		}
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