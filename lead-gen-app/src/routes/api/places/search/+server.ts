import { json } from '@sveltejs/kit';
import { GOOGLE_MAPS_API_KEY } from '$env/static/private';
import type { RequestHandler } from './$types';

// Places API (New) field mask - only valid fields
const FIELD_MASK = [
	'places.id',
	'places.displayName',
	'places.formattedAddress',
	'places.internationalPhoneNumber',
	'places.websiteUri',
	'places.rating',
	'places.userRatingCount',
	'places.primaryType',
	'places.types',
	'places.businessStatus',
	'places.location'
].join(',');


function transformPlaceData(place: any) {
	return {
		id: place.id,
		displayName: place.displayName?.text || '',
		formattedAddress: place.formattedAddress || '',
		internationalPhoneNumber: place.internationalPhoneNumber,
		nationalPhoneNumber: null, // Not available in Places API (New)
		websiteUri: place.websiteUri,
		rating: place.rating,
		userRatingCount: place.userRatingCount,
		primaryType: place.primaryType,
		primaryTypeDisplayName: place.primaryType, // Use primaryType as display name
		types: place.types,
		businessStatus: place.businessStatus,
		editorialSummary: null, // Not available in Places API (New)
		location: {
			latitude: place.location?.latitude || 0,
			longitude: place.location?.longitude || 0
		}
	};
}

export const POST: RequestHandler = async ({ request }) => {
	try {
		const { textQuery, locationBias, maxResultCount = 20 } = await request.json();

		if (!textQuery) {
			return json({ error: 'Text query is required' }, { status: 400 });
		}

		// Validate API key
		if (!GOOGLE_MAPS_API_KEY || GOOGLE_MAPS_API_KEY === 'your_google_maps_api_key_here') {
			return json({ error: 'Google Maps API key not configured' }, { status: 500 });
		}

		const requestBody = {
			textQuery,
			pageSize: Math.min(maxResultCount, 20), // Places API (New) uses pageSize, not maxResultCount
			...(locationBias && { locationBias })
		};

		const response = await fetch('https://places.googleapis.com/v1/places:searchText', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-Goog-Api-Key': GOOGLE_MAPS_API_KEY,
				'X-Goog-FieldMask': FIELD_MASK
			},
			body: JSON.stringify(requestBody)
		});

		if (!response.ok) {
			const errorText = await response.text();
			console.error('Places API error:', {
				status: response.status,
				statusText: response.statusText,
				headers: Object.fromEntries(response.headers.entries()),
				body: errorText
			});
			return json({
				error: 'Places API request failed',
				details: errorText,
				status: response.status
			}, { status: response.status });
		}

		const data = await response.json();

		return json({
			places: (data.places || []).map(transformPlaceData)
		});

	} catch (error) {
		console.error('Server error:', error);
		return json({ error: 'Internal server error' }, { status: 500 });
	}
};