import type { DashboardMetrics, RevenueMetrics, FunnelMetrics } from '../types';

// Cache entry interface
interface CacheEntry<T> {
	data: T;
	timestamp: number;
	expiresAt: number;
}

// Cache configuration
const CACHE_CONFIG = {
	// Cache durations in milliseconds
	DASHBOARD_METRICS: 5 * 60 * 1000,    // 5 minutes
	REVENUE_METRICS: 10 * 60 * 1000,     // 10 minutes
	FUNNEL_METRICS: 10 * 60 * 1000,      // 10 minutes
	
	// Maximum cache size (number of entries)
	MAX_CACHE_SIZE: 50,
	
	// Storage key prefix
	STORAGE_PREFIX: 'lma_metrics_cache_'
};

// Cache storage (in-memory with localStorage backup)
class MetricsCache {
	private memoryCache = new Map<string, CacheEntry<any>>();
	private useLocalStorage: boolean;

	constructor() {
		// Check if localStorage is available
		this.useLocalStorage = this.isLocalStorageAvailable();
		
		// Load existing cache from localStorage on initialization
		if (this.useLocalStorage) {
			this.loadFromLocalStorage();
		}
	}

	private isLocalStorageAvailable(): boolean {
		try {
			const test = '__localStorage_test__';
			localStorage.setItem(test, test);
			localStorage.removeItem(test);
			return true;
		} catch {
			return false;
		}
	}

	private loadFromLocalStorage(): void {
		try {
			const keys = Object.keys(localStorage).filter(key => 
				key.startsWith(CACHE_CONFIG.STORAGE_PREFIX)
			);

			keys.forEach(key => {
				const data = localStorage.getItem(key);
				if (data) {
					const entry: CacheEntry<any> = JSON.parse(data);
					const cacheKey = key.replace(CACHE_CONFIG.STORAGE_PREFIX, '');
					
					// Only load if not expired
					if (entry.expiresAt > Date.now()) {
						this.memoryCache.set(cacheKey, entry);
					} else {
						// Remove expired entries from localStorage
						localStorage.removeItem(key);
					}
				}
			});
		} catch (error) {
			console.warn('Failed to load cache from localStorage:', error);
		}
	}

	private saveToLocalStorage(key: string, entry: CacheEntry<any>): void {
		if (!this.useLocalStorage) return;

		try {
			const storageKey = CACHE_CONFIG.STORAGE_PREFIX + key;
			localStorage.setItem(storageKey, JSON.stringify(entry));
		} catch (error) {
			console.warn('Failed to save cache to localStorage:', error);
		}
	}

	private removeFromLocalStorage(key: string): void {
		if (!this.useLocalStorage) return;

		try {
			const storageKey = CACHE_CONFIG.STORAGE_PREFIX + key;
			localStorage.removeItem(storageKey);
		} catch (error) {
			console.warn('Failed to remove cache from localStorage:', error);
		}
	}

	private generateKey(type: string, params: Record<string, any> = {}): string {
		const paramString = Object.keys(params)
			.sort()
			.map(key => `${key}=${params[key]}`)
			.join('&');
		
		return paramString ? `${type}?${paramString}` : type;
	}

	private cleanupExpiredEntries(): void {
		const now = Date.now();
		const expiredKeys: string[] = [];

		this.memoryCache.forEach((entry, key) => {
			if (entry.expiresAt <= now) {
				expiredKeys.push(key);
			}
		});

		expiredKeys.forEach(key => {
			this.memoryCache.delete(key);
			this.removeFromLocalStorage(key);
		});
	}

	private enforceMaxSize(): void {
		if (this.memoryCache.size <= CACHE_CONFIG.MAX_CACHE_SIZE) return;

		// Remove oldest entries
		const entries = Array.from(this.memoryCache.entries())
			.sort((a, b) => a[1].timestamp - b[1].timestamp);

		const toRemove = entries.slice(0, this.memoryCache.size - CACHE_CONFIG.MAX_CACHE_SIZE);
		
		toRemove.forEach(([key]) => {
			this.memoryCache.delete(key);
			this.removeFromLocalStorage(key);
		});
	}

	// Get cached data
	get<T>(type: string, params: Record<string, any> = {}): T | null {
		this.cleanupExpiredEntries();
		
		const key = this.generateKey(type, params);
		const entry = this.memoryCache.get(key);

		if (entry && entry.expiresAt > Date.now()) {
			return entry.data as T;
		}

		// Remove expired entry
		if (entry) {
			this.memoryCache.delete(key);
			this.removeFromLocalStorage(key);
		}

		return null;
	}

	// Set cached data
	set<T>(type: string, data: T, params: Record<string, any> = {}): void {
		const key = this.generateKey(type, params);
		const now = Date.now();
		
		// Determine cache duration based on type
		let duration: number;
		switch (type) {
			case 'dashboard':
				duration = CACHE_CONFIG.DASHBOARD_METRICS;
				break;
			case 'revenue':
				duration = CACHE_CONFIG.REVENUE_METRICS;
				break;
			case 'funnel':
				duration = CACHE_CONFIG.FUNNEL_METRICS;
				break;
			default:
				duration = CACHE_CONFIG.DASHBOARD_METRICS; // Default duration
		}

		const entry: CacheEntry<T> = {
			data,
			timestamp: now,
			expiresAt: now + duration
		};

		this.memoryCache.set(key, entry);
		this.saveToLocalStorage(key, entry);
		
		// Cleanup if needed
		this.enforceMaxSize();
	}

	// Check if data is cached and valid
	has(type: string, params: Record<string, any> = {}): boolean {
		const key = this.generateKey(type, params);
		const entry = this.memoryCache.get(key);
		return entry !== undefined && entry.expiresAt > Date.now();
	}

	// Clear specific cache entry
	clear(type: string, params: Record<string, any> = {}): void {
		const key = this.generateKey(type, params);
		this.memoryCache.delete(key);
		this.removeFromLocalStorage(key);
	}

	// Clear all cache
	clearAll(): void {
		// Clear memory cache
		this.memoryCache.clear();

		// Clear localStorage cache
		if (this.useLocalStorage) {
			const keys = Object.keys(localStorage).filter(key => 
				key.startsWith(CACHE_CONFIG.STORAGE_PREFIX)
			);
			keys.forEach(key => localStorage.removeItem(key));
		}
	}

	// Get cache statistics
	getStats(): {
		size: number;
		entries: Array<{ key: string; type: string; timestamp: number; expiresAt: number; size: number }>;
	} {
		const entries = Array.from(this.memoryCache.entries()).map(([key, entry]) => ({
			key,
			type: key.split('?')[0],
			timestamp: entry.timestamp,
			expiresAt: entry.expiresAt,
			size: JSON.stringify(entry.data).length
		}));

		return {
			size: this.memoryCache.size,
			entries
		};
	}

	// Preload cache with fresh data
	async preload(
		loaders: {
			dashboard?: () => Promise<DashboardMetrics>;
			revenue?: (params?: any) => Promise<RevenueMetrics>;
			funnel?: (params?: any) => Promise<FunnelMetrics>;
		}
	): Promise<void> {
		const promises: Promise<void>[] = [];

		if (loaders.dashboard) {
			promises.push(
				loaders.dashboard().then(data => {
					this.set('dashboard', data);
				}).catch(error => {
					console.warn('Failed to preload dashboard metrics:', error);
				})
			);
		}

		if (loaders.revenue) {
			promises.push(
				loaders.revenue().then(data => {
					this.set('revenue', data);
				}).catch(error => {
					console.warn('Failed to preload revenue metrics:', error);
				})
			);
		}

		if (loaders.funnel) {
			promises.push(
				loaders.funnel().then(data => {
					this.set('funnel', data);
				}).catch(error => {
					console.warn('Failed to preload funnel metrics:', error);
				})
			);
		}

		await Promise.allSettled(promises);
	}
}

// Create singleton instance
export const metricsCache = new MetricsCache();

// Cache-aware API wrapper functions
export const cachedApiCall = {
	// Get dashboard metrics with caching
	async getDashboardMetrics(
		apiCall: () => Promise<DashboardMetrics>,
		params: Record<string, any> = {},
		forceRefresh: boolean = false
	): Promise<DashboardMetrics> {
		if (!forceRefresh) {
			const cached = metricsCache.get<DashboardMetrics>('dashboard', params);
			if (cached) {
				return cached;
			}
		}

		const data = await apiCall();
		metricsCache.set('dashboard', data, params);
		return data;
	},

	// Get revenue metrics with caching
	async getRevenueMetrics(
		apiCall: () => Promise<RevenueMetrics>,
		params: Record<string, any> = {},
		forceRefresh: boolean = false
	): Promise<RevenueMetrics> {
		if (!forceRefresh) {
			const cached = metricsCache.get<RevenueMetrics>('revenue', params);
			if (cached) {
				return cached;
			}
		}

		const data = await apiCall();
		metricsCache.set('revenue', data, params);
		return data;
	},

	// Get funnel metrics with caching
	async getFunnelMetrics(
		apiCall: () => Promise<FunnelMetrics>,
		params: Record<string, any> = {},
		forceRefresh: boolean = false
	): Promise<FunnelMetrics> {
		if (!forceRefresh) {
			const cached = metricsCache.get<FunnelMetrics>('funnel', params);
			if (cached) {
				return cached;
			}
		}

		const data = await apiCall();
		metricsCache.set('funnel', data, params);
		return data;
	}
};

// Cache invalidation utilities
export const cacheInvalidation = {
	// Invalidate cache when data changes
	onDataChange(type: 'dashboard' | 'revenue' | 'funnel' | 'all'): void {
		if (type === 'all') {
			metricsCache.clearAll();
		} else {
			// Clear all entries of the specified type
			const stats = metricsCache.getStats();
			stats.entries
				.filter(entry => entry.type === type)
				.forEach(entry => {
					const [cacheType, params] = entry.key.split('?');
					const paramObj = params ? 
						Object.fromEntries(new URLSearchParams(params)) : {};
					metricsCache.clear(cacheType, paramObj);
				});
		}
	},

	// Invalidate cache for specific time ranges
	onTimeRangeChange(newRange: { start: Date; end: Date }): void {
		// For now, clear all cache when time range changes
		// Could be optimized to only clear relevant entries
		metricsCache.clearAll();
	}
};

// Export cache configuration for external use
export { CACHE_CONFIG }; 