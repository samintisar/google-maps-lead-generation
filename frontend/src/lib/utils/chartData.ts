import type { DashboardMetrics, RevenueMetrics, FunnelMetrics } from '../types';

// Color schemes for consistent chart styling
export const CHART_COLORS = {
	primary: '#4F46E5',     // Indigo
	secondary: '#10B981',   // Emerald
	accent: '#F59E0B',      // Amber
	danger: '#EF4444',      // Red
	warning: '#F97316',     // Orange
	info: '#3B82F6',        // Blue
	success: '#22C55E',     // Green
	gray: '#6B7280',        // Gray
	// Status colors
	new: '#3B82F6',         // Blue
	qualified: '#F59E0B',   // Amber
	proposal: '#8B5CF6',    // Violet
	negotiation: '#EC4899', // Pink
	won: '#22C55E',         // Green
	lost: '#EF4444',        // Red
	// Additional chart colors for multi-series
	palette: [
		'#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
		'#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
	]
};

// Date formatting utilities
export const formatters = {
	// Format date for chart labels
	formatDateLabel: (date: string | Date, groupBy: 'day' | 'week' | 'month' | 'year' = 'month'): string => {
		const d = new Date(date);
		const options: Intl.DateTimeFormatOptions = {};
		
		switch (groupBy) {
			case 'day':
				options.month = 'short';
				options.day = 'numeric';
				break;
			case 'week':
				options.month = 'short';
				options.day = 'numeric';
				break;
			case 'month':
				options.month = 'short';
				options.year = '2-digit';
				break;
			case 'year':
				options.year = 'numeric';
				break;
		}
		
		return d.toLocaleDateString('en-US', options);
	},

	// Format currency values for chart tooltips
	formatCurrency: (value: number): string => {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(value);
	},

	// Format percentage values
	formatPercentage: (value: number, decimals: number = 1): string => {
		return `${value.toFixed(decimals)}%`;
	},

	// Format large numbers with abbreviations
	formatNumber: (value: number): string => {
		if (value >= 1000000) {
			return `${(value / 1000000).toFixed(1)}M`;
		} else if (value >= 1000) {
			return `${(value / 1000).toFixed(1)}K`;
		}
		return value.toString();
	}
};

// Chart.js dataset utilities
export const datasetUtils = {
	// Create a consistent dataset configuration
	createDataset: (
		label: string,
		data: number[],
		colorIndex: number = 0,
		chartType: 'line' | 'bar' | 'pie' | 'doughnut' = 'line'
	) => {
		const color = CHART_COLORS.palette[colorIndex % CHART_COLORS.palette.length];
		
		const baseConfig = {
			label,
			data,
			borderColor: color,
			backgroundColor: chartType === 'line' 
				? `${color}20` // 20% opacity for line charts
				: color
		};

		// Type-specific configurations
		switch (chartType) {
			case 'line':
				return {
					...baseConfig,
					fill: false,
					tension: 0.1,
					pointBackgroundColor: color,
					pointBorderColor: color,
					pointHoverBackgroundColor: '#fff',
					pointHoverBorderColor: color
				};
			case 'bar':
				return {
					...baseConfig,
					borderWidth: 1,
					borderRadius: 4,
					borderSkipped: false
				};
			case 'pie':
			case 'doughnut':
				return {
					...baseConfig,
					backgroundColor: CHART_COLORS.palette.slice(0, data.length),
					borderWidth: 2,
					borderColor: '#fff'
				};
			default:
				return baseConfig;
		}
	}
};

// Dashboard metrics transformations
export const dashboardCharts = {
	// Convert lead distribution by status to pie chart data
	leadStatusDistribution: (metrics: DashboardMetrics | null) => {
		if (!metrics || !metrics.lead_distribution || !metrics.lead_distribution.by_status || !Array.isArray(metrics.lead_distribution.by_status) || metrics.lead_distribution.by_status.length === 0) return null;
		const statusData = metrics.lead_distribution.by_status;
		
		return {
			labels: statusData.map(item => item.status),
			datasets: [{
				data: statusData.map(item => item.count),
				backgroundColor: statusData.map((_, index) => {
					const statusColors: Record<string, string> = {
						'new': CHART_COLORS.new,
						'qualified': CHART_COLORS.qualified,
						'proposal': CHART_COLORS.warning,
						'negotiation': CHART_COLORS.info,
						'won': CHART_COLORS.success,
						'lost': CHART_COLORS.danger
					};
					return statusColors[statusData[index].status.toLowerCase()] || CHART_COLORS.palette[index];
				}),
				borderWidth: 2,
				borderColor: '#fff'
			}]
		};
	},

	// Convert lead source distribution to doughnut chart data
	leadSourceDistribution: (metrics: DashboardMetrics | null) => {
		if (!metrics || !metrics.lead_distribution || !metrics.lead_distribution.by_source || !Array.isArray(metrics.lead_distribution.by_source) || metrics.lead_distribution.by_source.length === 0) return null;
		const sourceData = metrics.lead_distribution.by_source;
		
		return {
			labels: sourceData.map(item => item.source),
			datasets: [{
				data: sourceData.map(item => item.count),
				backgroundColor: CHART_COLORS.palette.slice(0, sourceData.length),
				borderWidth: 2,
				borderColor: '#fff'
			}]
		};
	},

	// Convert daily leads timeline to line chart data
	dailyLeadsTimeline: (metrics: DashboardMetrics | null) => {
		if (!metrics || !metrics.time_series || !metrics.time_series.daily_leads || !Array.isArray(metrics.time_series.daily_leads)) return null;
		const timelineData = metrics.time_series.daily_leads;
		
		return {
			labels: timelineData.map((item: { date: string; count: number }) => formatters.formatDateLabel(item.date, 'day')),
			datasets: [
				datasetUtils.createDataset(
					'Daily Leads',
					timelineData.map((item: { date: string; count: number }) => item.count),
					0,
					'line'
				)
			]
		};
	},

	// Convert score trend to line chart data
	scoreTrendTimeline: (metrics: DashboardMetrics | null) => {
		if (!metrics || !metrics.time_series || !metrics.time_series.score_trend || !Array.isArray(metrics.time_series.score_trend)) return null;
		const trendData = metrics.time_series.score_trend;
		
		return {
			labels: trendData.map((item: { date: string; avg_score: number }) => formatters.formatDateLabel(item.date, 'day')),
			datasets: [
				datasetUtils.createDataset(
					'Average Score',
					trendData.map((item: { date: string; avg_score: number }) => item.avg_score),
					1,
					'line'
				)
			]
		};
	}
};

// Revenue metrics transformations
export const revenueCharts = {
	// Convert revenue trend to line chart data
	revenueTrend: (metrics: RevenueMetrics | null) => {
		if (!metrics || !metrics.revenue_trend || !Array.isArray(metrics.revenue_trend)) return null;
		const trendData = metrics.revenue_trend;
		
		return {
			labels: trendData.map((item: { period: string; revenue: number; deals_count: number; avg_deal_size: number }) => formatters.formatDateLabel(item.period)),
			datasets: [
				datasetUtils.createDataset(
					'Revenue',
					trendData.map((item: { period: string; revenue: number; deals_count: number; avg_deal_size: number }) => item.revenue),
					0,
					'line'
				),
				datasetUtils.createDataset(
					'Deals Count',
					trendData.map((item: { period: string; revenue: number; deals_count: number; avg_deal_size: number }) => item.deals_count),
					1,
					'line'
				)
			]
		};
	},

	// Convert revenue timeline to line chart data (alias for timeline charts)
	revenueTimeline: (metrics: RevenueMetrics | null) => {
		return revenueCharts.revenueTrend(metrics);
	},

	// Convert revenue by period to bar chart data
	revenueByPeriod: (metrics: RevenueMetrics | null) => {
		if (!metrics || !metrics.revenue_trend || !Array.isArray(metrics.revenue_trend)) return null;
		const trendData = metrics.revenue_trend;
		
		return {
			labels: trendData.map((item: { period: string; revenue: number; deals_count: number; avg_deal_size: number }) => formatters.formatDateLabel(item.period)),
			datasets: [
				datasetUtils.createDataset(
					'Revenue',
					trendData.map((item: { period: string; revenue: number; deals_count: number; avg_deal_size: number }) => item.revenue),
					0,
					'bar'
				)
			]
		};
	},

	// Convert revenue by source to bar chart data
	revenueBySource: (metrics: RevenueMetrics | null) => {
		if (!metrics || !metrics.revenue_by_source || !Array.isArray(metrics.revenue_by_source)) return null;
		const sourceData = metrics.revenue_by_source;
		
		return {
			labels: sourceData.map((item: { source: string; revenue: number; deals_count: number }) => item.source),
			datasets: [
				datasetUtils.createDataset(
					'Revenue',
					sourceData.map((item: { source: string; revenue: number; deals_count: number }) => item.revenue),
					0,
					'bar'
				)
			]
		};
	}
};

// Funnel metrics transformations
export const funnelCharts = {
	// Convert funnel stages to horizontal bar chart data
	funnelStages: (metrics: FunnelMetrics | null) => {
		if (!metrics || !metrics.funnel_stages || !Array.isArray(metrics.funnel_stages)) return null;
		const stagesData = metrics.funnel_stages;
		
		return {
			labels: stagesData.map((item: { stage: string; count: number; conversion_rate: number; stage_conversion: number }) => item.stage),
			datasets: [
				datasetUtils.createDataset(
					'Leads',
					stagesData.map((item: { stage: string; count: number; conversion_rate: number; stage_conversion: number }) => item.count),
					0,
					'bar'
				)
			]
		};
	},

	// Alias for funnel stages as bar chart
	funnelStageBar: (metrics: FunnelMetrics | null) => {
		return funnelCharts.funnelStages(metrics);
	},

	// Convert stage conversion rates to line chart data
	stageConversionRates: (metrics: FunnelMetrics | null) => {
		if (!metrics || !metrics.funnel_stages || !Array.isArray(metrics.funnel_stages)) return null;
		const stagesData = metrics.funnel_stages;
		
		return {
			labels: stagesData.map((item: { stage: string; count: number; conversion_rate: number; stage_conversion: number }) => item.stage),
			datasets: [
				datasetUtils.createDataset(
					'Stage Conversion Rate (%)',
					stagesData.map((item: { stage: string; count: number; conversion_rate: number; stage_conversion: number }) => item.stage_conversion),
					2,
					'line'
				)
			]
		};
	}
};

// Chart configuration presets
export const chartConfigs = {
	// Basic line chart configuration
	lineChart: {
		responsive: true,
		maintainAspectRatio: false,
		plugins: {
			legend: {
				position: 'top' as const,
			},
			tooltip: {
				mode: 'index' as const,
				intersect: false,
				callbacks: {
					label: (context: any) => {
						let label = context.dataset.label || '';
						if (label) {
							label += ': ';
						}
						if (context.parsed.y !== null) {
							// Check if it's a currency value
							if (label.toLowerCase().includes('revenue') || label.toLowerCase().includes('mrr')) {
								label += formatters.formatCurrency(context.parsed.y);
							} else {
								label += formatters.formatNumber(context.parsed.y);
							}
						}
						return label;
					}
				}
			}
		},
		scales: {
			x: {
				display: true,
				title: {
					display: true,
					text: 'Time Period'
				}
			},
			y: {
				display: true,
				title: {
					display: true,
					text: 'Value'
				},
				beginAtZero: true
			}
		}
	},

	// Basic bar chart configuration
	barChart: {
		responsive: true,
		maintainAspectRatio: false,
		plugins: {
			legend: {
				position: 'top' as const,
			},
			tooltip: {
				callbacks: {
					label: (context: any) => {
						let label = context.dataset.label || '';
						if (label) {
							label += ': ';
						}
						if (context.parsed.y !== null) {
							label += formatters.formatNumber(context.parsed.y);
						}
						return label;
					}
				}
			}
		},
		scales: {
			x: {
				display: true,
				title: {
					display: true,
					text: 'Category'
				}
			},
			y: {
				display: true,
				title: {
					display: true,
					text: 'Count'
				},
				beginAtZero: true
			}
		}
	},

	// Basic pie/doughnut chart configuration
	pieChart: {
		responsive: true,
		maintainAspectRatio: false,
		plugins: {
			legend: {
				position: 'right' as const,
			},
			tooltip: {
				callbacks: {
					label: (context: any) => {
						const label = context.label || '';
						const value = context.parsed;
						const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
						const percentage = ((value / total) * 100).toFixed(1);
						return `${label}: ${value} (${percentage}%)`;
					}
				}
			}
		}
	}
};

// Time range utilities
export const timeRangeUtils = {
	// Generate date ranges for filtering
	getDateRange: (range: 'last7days' | 'last30days' | 'last90days' | 'lastyear' | 'custom', customStart?: Date, customEnd?: Date) => {
		const end = new Date();
		let start: Date;

		switch (range) {
			case 'last7days':
				start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000);
				break;
			case 'last30days':
				start = new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000);
				break;
			case 'last90days':
				start = new Date(end.getTime() - 90 * 24 * 60 * 60 * 1000);
				break;
			case 'lastyear':
				start = new Date(end.getTime() - 365 * 24 * 60 * 60 * 1000);
				break;
			case 'custom':
				start = customStart || new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000);
				if (customEnd) end.setTime(customEnd.getTime());
				break;
			default:
				start = new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000);
		}

		return { start, end };
	},

	// Calculate appropriate grouping based on date range
	getOptimalGrouping: (startDate: Date, endDate: Date): 'day' | 'week' | 'month' => {
		const diffInDays = (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24);
		
		if (diffInDays <= 14) return 'day';
		if (diffInDays <= 90) return 'week';
		return 'month';
	}
};

// Data aggregation utilities
export const aggregationUtils = {
	// Group data by time period
	groupByTimePeriod: <T extends { date: string; [key: string]: any }>(
		data: T[],
		groupBy: 'day' | 'week' | 'month'
	): T[] => {
		const grouped = new Map<string, T[]>();

		data.forEach(item => {
			const date = new Date(item.date);
			let key: string;

			switch (groupBy) {
				case 'day':
					key = date.toISOString().split('T')[0];
					break;
				case 'week':
					const week = new Date(date);
					week.setDate(date.getDate() - date.getDay());
					key = week.toISOString().split('T')[0];
					break;
				case 'month':
					key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
					break;
			}

			if (!grouped.has(key)) {
				grouped.set(key, []);
			}
			grouped.get(key)!.push(item);
		});

		// Aggregate grouped data (example for count - can be extended for other metrics)
		return Array.from(grouped.entries()).map(([period, items]) => ({
			...items[0],
			date: period,
			count: items.reduce((sum, item) => sum + (item.count || 1), 0)
		} as T));
	},

	// Calculate cumulative values
	calculateCumulative: (data: number[]): number[] => {
		const cumulative: number[] = [];
		let total = 0;
		
		data.forEach(value => {
			total += value;
			cumulative.push(total);
		});
		
		return cumulative;
	},

	// Calculate moving averages
	calculateMovingAverage: (data: number[], windowSize: number): number[] => {
		const averages: number[] = [];
		
		for (let i = 0; i < data.length; i++) {
			const start = Math.max(0, i - windowSize + 1);
			const end = i + 1;
			const slice = data.slice(start, end);
			const average = slice.reduce((sum, value) => sum + value, 0) / slice.length;
			averages.push(average);
		}
		
		return averages;
	}
}; 