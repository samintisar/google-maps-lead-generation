import { writable } from 'svelte/store';
import type { SavedLead, PlaceResult } from '$lib/types';

function createLeadsStore() {
	const { subscribe, set, update } = writable<SavedLead[]>([]);

	return {
		subscribe,
		init: () => {
			if (typeof window !== 'undefined') {
				const stored = localStorage.getItem('saved-leads');
				if (stored) {
					try {
						set(JSON.parse(stored));
					} catch (e) {
						console.error('Error loading leads from localStorage:', e);
						set([]);
					}
				}
			}
		},
		add: (place: PlaceResult) => {
			const lead: SavedLead = {
				...place,
				savedAt: new Date().toISOString()
			};

			update(leads => {
				const exists = leads.find(l => l.id === place.id);
				if (!exists) {
					const newLeads = [...leads, lead];
					if (typeof window !== 'undefined') {
						localStorage.setItem('saved-leads', JSON.stringify(newLeads));
					}
					return newLeads;
				}
				return leads;
			});
		},
		remove: (id: string) => {
			update(leads => {
				const newLeads = leads.filter(lead => lead.id !== id);
				if (typeof window !== 'undefined') {
					localStorage.setItem('saved-leads', JSON.stringify(newLeads));
				}
				return newLeads;
			});
		},
		clear: () => {
			set([]);
			if (typeof window !== 'undefined') {
				localStorage.removeItem('saved-leads');
			}
		}
	};
}

export const leadsStore = createLeadsStore();