import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { config } from '../config';
import { authApi } from '../api';

export interface User {
	id: number;
	username: string;
	email: string;
	first_name?: string;
	last_name?: string;
	role?: string;
	organization_id?: number;
}

export interface AuthState {
	user: User | null;
	token: string | null;
	isAuthenticated: boolean;
	isLoading: boolean;
	error: string | null;
}

// Initial state
const initialState: AuthState = {
	user: null,
	token: null,
	isAuthenticated: false,
	isLoading: true,
	error: null
};

// Create the store
export const authStore = writable<AuthState>(initialState);

// Helper function to check if token is expired
function isTokenExpired(token: string): boolean {
	if (!token) return true;
	
	try {
		// Basic JWT parsing (for expiration check)
		const payload = JSON.parse(atob(token.split('.')[1]));
		const now = Math.floor(Date.now() / 1000);
		return payload.exp && payload.exp < now;
	} catch {
		// If we can't parse the token, consider it expired
		return true;
	}
}

// Helper function to validate stored auth data
function validateStoredAuth(): { token: string; user: User } | null {
	if (!browser) return null;
	
	const token = localStorage.getItem(config.auth.tokenKey);
	const userJson = localStorage.getItem(config.auth.userKey);
	
	if (!token || !userJson) return null;
	
	// Check if token is expired
	if (isTokenExpired(token)) {
		localStorage.removeItem(config.auth.tokenKey);
		localStorage.removeItem(config.auth.userKey);
		return null;
	}
	
	try {
		const user = JSON.parse(userJson);
		return { token, user };
	} catch (e) {
		console.error('Error parsing stored user data:', e);
		localStorage.removeItem(config.auth.tokenKey);
		localStorage.removeItem(config.auth.userKey);
		return null;
	}
}

// Auth functions
export const auth = {
	// Initialize auth state from localStorage
	init() {
		if (!browser) return;
		
		const storedAuth = validateStoredAuth();
		
		if (storedAuth) {
			authStore.set({
				user: storedAuth.user,
				token: storedAuth.token,
				isAuthenticated: true,
				isLoading: false,
				error: null
			});
		} else {
			authStore.set({
				...initialState,
				isLoading: false
			});
		}
	},

	// Login with credentials
	async login(username: string, password: string): Promise<void> {
		authStore.update(state => ({ 
			...state, 
			isLoading: true, 
			error: null 
		}));

		try {
			const response = await authApi.login(username, password);
			
			// Store auth data
			if (browser) {
				localStorage.setItem(config.auth.tokenKey, response.access_token);
				localStorage.setItem(config.auth.userKey, JSON.stringify(response.user));
			}

			authStore.set({
				user: response.user,
				token: response.access_token,
				isAuthenticated: true,
				isLoading: false,
				error: null
			});

			// Redirect to dashboard
			goto('/dashboard');
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : 'Login failed';
			authStore.update(state => ({ 
				...state, 
				isLoading: false, 
				error: errorMessage 
			}));
			throw error;
		}
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
	}): Promise<void> {
		authStore.update(state => ({ 
			...state, 
			isLoading: true, 
			error: null 
		}));

		try {
			const response = await authApi.register(userData);
			
			// Store auth data
			if (browser) {
				localStorage.setItem(config.auth.tokenKey, response.access_token);
				localStorage.setItem(config.auth.userKey, JSON.stringify(response.data));
			}

			authStore.set({
				user: response.data,
				token: response.access_token,
				isAuthenticated: true,
				isLoading: false,
				error: null
			});

			// Redirect to dashboard
			goto('/dashboard');
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : 'Registration failed';
			authStore.update(state => ({ 
				...state, 
				isLoading: false, 
				error: errorMessage 
			}));
			throw error;
		}
	},

	// Refresh user data
	async refreshUser(): Promise<void> {
		try {
			const user = await authApi.getCurrentUser();
			authStore.update(state => ({
				...state,
				user,
				error: null
			}));
		} catch (error) {
			console.error('Failed to refresh user:', error);
			// If refresh fails, might need to logout
			if (error instanceof Error && error.message.includes('Authentication required')) {
				this.logout();
			}
		}
	},

	// Logout
	async logout(): Promise<void> {
		authStore.update(state => ({ ...state, isLoading: true }));

		try {
			// Try to call logout API
			await authApi.logout();
		} catch (error) {
			// Ignore logout API errors - we'll clear local storage anyway
			if (config.features.enableDebugLogging) {
				console.warn('Logout API call failed:', error);
			}
		}

		// Clear local storage
		if (browser) {
			localStorage.removeItem(config.auth.tokenKey);
			localStorage.removeItem(config.auth.userKey);
		}

		authStore.set({
			user: null,
			token: null,
			isAuthenticated: false,
			isLoading: false,
			error: null
		});

		goto('/login');
	},

	// Clear error
	clearError(): void {
		authStore.update(state => ({ ...state, error: null }));
	},

	// Get current token
	getToken(): string | null {
		if (!browser) return null;
		const token = localStorage.getItem(config.auth.tokenKey);
		
		// Check if token is expired
		if (token && isTokenExpired(token)) {
			this.logout();
			return null;
		}
		
		return token;
	},

	// Check if user is authenticated
	isAuthenticated(): boolean {
		const token = this.getToken();
		return !!token && !isTokenExpired(token);
	}
};

// Initialize auth on store creation
if (browser) {
	auth.init();
} 