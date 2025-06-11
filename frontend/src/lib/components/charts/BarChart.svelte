<!-- Bar Chart Component -->
<script lang="ts">
	import BaseChart from './BaseChart.svelte';
	import { revenueCharts, funnelCharts } from '$lib/utils/chartData';
	import type { RevenueMetrics, FunnelMetrics } from '$lib/types';
	import type { ChartOptions } from 'chart.js';

	// Props
	export let revenueMetrics: RevenueMetrics | null = null;
	export let funnelMetrics: FunnelMetrics | null = null;
	export let chartType: 'revenue_by_period' | 'funnel_stages' | 'custom' = 'revenue_by_period';
	export let title: string = '';
	export let height: number = 300;
	export let loading: boolean = false;
	export let error: string | null = null;
	export let customData: any = null;
	export let customOptions: ChartOptions = {};
	export let horizontal: boolean = false;
	export let showValues: boolean = false;
	export let borderRadius: number = 4;

	// Specific bar chart options
	const barOptions: ChartOptions = {
		indexAxis: horizontal ? 'y' : 'x',
		elements: {
			bar: {
				borderRadius,
				borderSkipped: false
			}
		},
		plugins: {
			legend: {
				position: 'top',
				labels: {
					usePointStyle: true,
					padding: 20
				}
			},
			tooltip: {
				mode: 'index',
				intersect: false
			}
		},
		scales: {
			x: {
				grid: {
					display: !horizontal,
					color: 'rgba(107, 114, 128, 0.1)'
				},
				ticks: {
					color: '#6B7280'
				}
			},
			y: {
				grid: {
					display: horizontal,
					color: 'rgba(107, 114, 128, 0.1)'
				},
				ticks: {
					color: '#6B7280'
				},
				beginAtZero: true
			}
		},
		maintainAspectRatio: false
	};

	// Add data labels plugin if showValues is true
	$: finalOptions = showValues ? {
		...barOptions,
		plugins: {
			...barOptions.plugins,
			datalabels: {
				display: true,
				align: 'end',
				anchor: 'end',
				color: '#374151',
				font: {
					weight: 'bold',
					size: 11
				},
				formatter: (value: number) => {
					if (chartType === 'revenue_by_period') {
						return new Intl.NumberFormat('en-US', {
							style: 'currency',
							currency: 'USD',
							minimumFractionDigits: 0
						}).format(value);
					}
					return value.toLocaleString();
				}
			}
		}
	} : barOptions;

	// Merged options
	$: mergedOptions = { ...finalOptions, ...customOptions };

	// Generate chart data based on metrics and chart type
	$: chartData = (() => {
		if (customData) return customData;

		switch (chartType) {
			case 'revenue_by_period':
				return revenueMetrics ? revenueCharts.revenueByPeriod(revenueMetrics) : null;
			case 'funnel_stages':
				return funnelMetrics ? funnelCharts.funnelStageBar(funnelMetrics) : null;
			default:
				return null;
		}
	})();

	// Chart title
	$: chartTitle = title || (() => {
		switch (chartType) {
			case 'revenue_by_period':
				return 'Revenue by Period';
			case 'funnel_stages':
				return 'Funnel Conversion Stages';
			default:
				return 'Bar Chart';
		}
	})();
</script>

<div class="bar-chart-container">
	{#if chartTitle}
		<h3 class="text-lg font-medium text-gray-900 mb-4">{chartTitle}</h3>
	{/if}
	
	<BaseChart
		type="bar"
		data={chartData}
		options={mergedOptions}
		{height}
		{loading}
		{error}
		emptyMessage="No data available for bar chart"
	/>
</div>

<style>
	.bar-chart-container {
		width: 100%;
	}
</style> 