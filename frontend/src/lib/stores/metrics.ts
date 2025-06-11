import { writable, derived } from 'svelte/store';
import type { DashboardMetrics, RevenueMetrics, FunnelMetrics } from '../types';
import { getDashboardMetrics, getRevenueMetrics, getFunnelMetrics } from '../api';

// Loading states for different metrics operations
export const metricsLoading = writable({
	dashboard: false,
	revenue: false,
	funnel: false
});

// Error states for metrics operations
export const metricsError = writable<string | null>(null);

// Core metrics data stores
export const dashboardMetrics = writable<DashboardMetrics | null>(null);
export const revenueMetrics = writable<RevenueMetrics | null>(null);
export const funnelMetrics = writable<FunnelMetrics | null>(null);

// Settings for metrics display
export const metricsSettings = writable({
	dashboardPeriod: 30,
	revenuePeriod: 90,
	revenueGroupBy: 'month',
	funnelPeriod: 30,
	autoRefresh: true,
	refreshInterval: 300000 // 5 minutes
});

// Create a comprehensive metrics store with actions
function createMetricsStore() {
	const setError = (error: string | null) => {
		metricsError.set(error);
		if (error) {
			// Auto-clear errors after 5 seconds
			setTimeout(() => metricsError.set(null), 5000);
		}
	};

	const setLoading = (type: 'dashboard' | 'revenue' | 'funnel', loading: boolean) => {
		metricsLoading.update(state => ({ ...state, [type]: loading }));
	};

	return {
		// Load dashboard metrics
		async loadDashboardMetrics(daysBack?: number) {
			try {
				setLoading('dashboard', true);
				setError(null);

				const period = daysBack || 30;
				const response = await getDashboardMetrics(period);
				
				if (response.success && response.data) {
					dashboardMetrics.set(response.data);
					// Update settings with current period
					metricsSettings.update(settings => ({ ...settings, dashboardPeriod: period }));
				} else {
					throw new Error(response.message || 'Failed to load dashboard metrics');
				}
			} catch (error) {
				console.error('Error loading dashboard metrics:', error);
				setError(error instanceof Error ? error.message : 'Failed to load dashboard metrics');
			} finally {
				setLoading('dashboard', false);
			}
		},

		// Load revenue metrics
		async loadRevenueMetrics(daysBack?: number, groupBy?: string) {
			try {
				setLoading('revenue', true);
				setError(null);

				const period = daysBack || 90;
				const grouping = groupBy || 'month';
				const response = await getRevenueMetrics(period, grouping);
				
				if (response.success && response.data) {
					revenueMetrics.set(response.data);
					// Update settings with current parameters
					metricsSettings.update(settings => ({ 
						...settings, 
						revenuePeriod: period,
						revenueGroupBy: grouping
					}));
				} else {
					throw new Error(response.message || 'Failed to load revenue metrics');
				}
			} catch (error) {
				console.error('Error loading revenue metrics:', error);
				setError(error instanceof Error ? error.message : 'Failed to load revenue metrics');
			} finally {
				setLoading('revenue', false);
			}
		},

		// Load funnel metrics
		async loadFunnelMetrics(daysBack?: number) {
			try {
				setLoading('funnel', true);
				setError(null);

				const period = daysBack || 30;
				const response = await getFunnelMetrics(period);
				
				if (response.success && response.data) {
					funnelMetrics.set(response.data);
					// Update settings with current period
					metricsSettings.update(settings => ({ ...settings, funnelPeriod: period }));
				} else {
					throw new Error(response.message || 'Failed to load funnel metrics');
				}
			} catch (error) {
				console.error('Error loading funnel metrics:', error);
				setError(error instanceof Error ? error.message : 'Failed to load funnel metrics');
			} finally {
				setLoading('funnel', false);
			}
		},

		// Load all metrics
		async loadAllMetrics() {
			const settings = metricsSettings;
			let currentSettings: any;
			settings.subscribe(s => currentSettings = s)();

			await Promise.all([
				this.loadDashboardMetrics(currentSettings.dashboardPeriod),
				this.loadRevenueMetrics(currentSettings.revenuePeriod, currentSettings.revenueGroupBy),
				this.loadFunnelMetrics(currentSettings.funnelPeriod)
			]);
		},

		// Refresh all metrics
		async refreshMetrics() {
			await this.loadAllMetrics();
		},

		// Update settings and reload relevant metrics
		async updateSettings(newSettings: Partial<{
			dashboardPeriod: number;
			revenuePeriod: number;
			revenueGroupBy: string;
			funnelPeriod: number;
			autoRefresh: boolean;
			refreshInterval: number;
		}>) {
			metricsSettings.update(current => ({ ...current, ...newSettings }));
			
			// Reload metrics if relevant settings changed
			if (newSettings.dashboardPeriod !== undefined) {
				await this.loadDashboardMetrics(newSettings.dashboardPeriod);
			}
			if (newSettings.revenuePeriod !== undefined || newSettings.revenueGroupBy !== undefined) {
				await this.loadRevenueMetrics(newSettings.revenuePeriod, newSettings.revenueGroupBy);
			}
			if (newSettings.funnelPeriod !== undefined) {
				await this.loadFunnelMetrics(newSettings.funnelPeriod);
			}
		},

		// Clear all metrics data
		clearMetrics() {
			dashboardMetrics.set(null);
			revenueMetrics.set(null);
			funnelMetrics.set(null);
			setError(null);
		}
	};
}

export const metricsStore = createMetricsStore();

// Derived stores for computed values
export const isAnyMetricsLoading = derived(
	metricsLoading,
	($loading) => $loading.dashboard || $loading.revenue || $loading.funnel
);

export const hasMetricsData = derived(
	[dashboardMetrics, revenueMetrics, funnelMetrics],
	([$dashboard, $revenue, $funnel]) => $dashboard !== null || $revenue !== null || $funnel !== null
);

// Helper to format currency values
export const formatCurrency = (value: number): string => {
	return new Intl.NumberFormat('en-US', {
		style: 'currency',
		currency: 'USD',
		minimumFractionDigits: 0,
		maximumFractionDigits: 0
	}).format(value);
};

// Helper to format percentage values
export const formatPercentage = (value: number): string => {
	return new Intl.NumberFormat('en-US', {
		style: 'percent',
		minimumFractionDigits: 1,
		maximumFractionDigits: 1
	}).format(value / 100);
};

// Auto-refresh functionality
let refreshInterval: NodeJS.Timeout | null = null;

metricsSettings.subscribe(settings => {
	// Clear existing interval
	if (refreshInterval) {
		clearInterval(refreshInterval);
		refreshInterval = null;
	}

	// Set up new interval if auto-refresh is enabled
	if (settings.autoRefresh && settings.refreshInterval > 0) {
		refreshInterval = setInterval(() => {
			metricsStore.refreshMetrics();
		}, settings.refreshInterval);
	}
});

// Clean up interval when component unmounts
export const cleanupMetricsAutoRefresh = () => {
	if (refreshInterval) {
		clearInterval(refreshInterval);
		refreshInterval = null;
	}
}; 