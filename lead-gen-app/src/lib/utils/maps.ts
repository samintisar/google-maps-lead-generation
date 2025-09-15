import type { PlaceResult } from '$lib/types';
import { browser } from '$app/environment';

let mapLoader: any = null;
let googleMaps: any | null = null;

export async function initializeGoogleMaps(apiKey?: string) {
	if (!browser) return null;
	if (googleMaps) return googleMaps;

	if (!apiKey || apiKey === 'your_google_maps_api_key_here') {
		console.error('No Google Maps API key provided');
		return null;
	}

	try {
		// Dynamic import to avoid SSR issues
		const { Loader } = await import('@googlemaps/js-api-loader');

		if (!mapLoader) {
			mapLoader = new Loader({
				apiKey,
				version: 'weekly',
				libraries: ['places']
			});
		}

		const google = await mapLoader.load();
		googleMaps = google.maps;
		return googleMaps;
	} catch (error) {
		console.error('Error loading Google Maps:', error);
		return null;
	}
}

export function createMarker(
	map: google.maps.Map,
	place: PlaceResult,
	onClick?: (place: PlaceResult) => void
) {
	if (!googleMaps) return null;

	const marker = new googleMaps.Marker({
		position: { lat: place.location.latitude, lng: place.location.longitude },
		map,
		title: place.displayName
	});

	if (onClick) {
		marker.addListener('click', () => onClick(place));
	}

	return marker;
}

export async function searchPlaces(query: string, location: string, limit = 20): Promise<PlaceResult[]> {
	try {
		const response = await fetch('/api/places/search', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				textQuery: `${query} in ${location}`,
				maxResultCount: limit
			})
		});

		if (!response.ok) {
			throw new Error(`Search failed: ${response.statusText}`);
		}

		const data = await response.json();
		return data.places || [];
	} catch (error) {
		console.error('Error searching places:', error);
		throw error;
	}
}

export async function geocodeLocation(location: string): Promise<{ lat: number; lng: number } | null> {
	if (!googleMaps) return null;

	try {
		const geocoder = new googleMaps.Geocoder();
		const result = await geocoder.geocode({ address: location });

		if (result.results && result.results.length > 0) {
			const { lat, lng } = result.results[0].geometry.location;
			return { lat: lat(), lng: lng() };
		}
	} catch (error) {
		console.error('Geocoding error:', error);
	}

	return null;
}