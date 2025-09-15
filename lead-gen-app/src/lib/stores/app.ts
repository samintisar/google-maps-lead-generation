import { writable } from 'svelte/store';
import type { PlaceResult, MapState, TabType } from '$lib/types';

export const searchResults = writable<PlaceResult[]>([]);
export const selectedPlace = writable<PlaceResult | null>(null);
export const isLoading = writable(false);
export const activeTab = writable<TabType>('results');
export const isMobile = writable(false);

export const mapState = writable<MapState>({
	center: { lat: 40.7128, lng: -74.0060 }, // NYC default
	zoom: 12,
	places: [],
	selectedPlace: null
});

export const searchParams = writable({
	query: '',
	location: '',
	limit: 20
});