import { browser } from '$app/environment';
import { env } from '$env/dynamic/public';

// Environment configuration
export const config = {
	// API configuration
	api: {
		baseUrl: browser ? (
			// Use VITE_API_URL if available, otherwise fall back to default
			env.PUBLIC_API_URL || 
			(window.location.hostname === 'localhost' 
				? 'http://localhost:18000/api'
				: `${window.location.protocol}//${window.location.hostname}:18000/api`)
		) : (env.PUBLIC_API_URL || 'http://localhost:18000/api'),
		timeout: 30000, // 30 seconds
	},
	
	// Authentication configuration
	auth: {
		tokenKey: 'auth_token',
		userKey: 'auth_user',
		tokenExpiry: 24 * 60 * 60 * 1000, // 24 hours in milliseconds
	},
	
	// App configuration
	app: {
		name: 'LMA Platform',
		version: '1.0.0',
		environment: browser ? 
			(window.location.hostname === 'localhost' ? 'development' : 'production') 
			: 'development',
	},
	
	// Features flags
	features: {
		useDevEndpoints: browser ? window.location.hostname === 'localhost' : true,
		enableDebugLogging: browser ? window.location.hostname === 'localhost' : false,
	}
};

// Helper function to check if we're in development
export const isDevelopment = () => config.app.environment === 'development';

// Helper function to get API URL with path
export const getApiUrl = (path: string) => {
	const cleanPath = path.startsWith('/') ? path.slice(1) : path;
	return `${config.api.baseUrl}/${cleanPath}`;
}; 