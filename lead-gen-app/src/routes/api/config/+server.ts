import { json } from '@sveltejs/kit';
import { GOOGLE_MAPS_API_KEY } from '$env/static/private';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
	// Only return whether API key is configured, not the key itself
	const isConfigured = !!(GOOGLE_MAPS_API_KEY && GOOGLE_MAPS_API_KEY !== 'your_google_maps_api_key_here');

	// Don't hard-fail in dev; expose flag and only include apiKey when configured
	return json({
		configured: isConfigured,
		apiKey: isConfigured ? GOOGLE_MAPS_API_KEY : undefined
	});
};