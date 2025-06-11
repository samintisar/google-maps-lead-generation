<!-- Line Chart Component -->
<script lang="ts">
	import BaseChart from './BaseChart.svelte';
	import { dashboardCharts, revenueCharts } from '$lib/utils/chartData';
	import type { DashboardMetrics, RevenueMetrics } from '$lib/types';
	import type { ChartOptions } from 'chart.js';

	// Props
	export let dashboardMetrics: DashboardMetrics | null = null;
	export let revenueMetrics: RevenueMetrics | null = null;
	export let chartType: 'daily_leads' | 'score_trend' | 'revenue_timeline' | 'custom' = 'daily_leads';
	export let title: string = '';
	export let height: number = 300;
	export let loading: boolean = false;
	export let error: string | null = null;
	export let customData: any = null;
	export let customOptions: ChartOptions = {};
	export let showPoints: boolean = true;
	export let fill: boolean = false;
	export let tension: number = 0.1;
	export let gridLines: boolean = true;

	// Specific line chart options
	const lineOptions: ChartOptions = {
		elements: {
			line: {
				tension,
				fill
			},
			point: {
				radius: showPoints ? 4 : 0,
				hoverRadius: showPoints ? 6 : 0,
				hitRadius: 10
			}
		},
		plugins: {
			legend: {
				position: 'top',
				labels: {
					usePointStyle: true,
					padding: 20
				}
			}
		},
		scales: {
			x: {
				grid: {
					display: gridLines,
					color: 'rgba(107, 114, 128, 0.1)'
				},
				ticks: {
					maxTicksLimit: 8,
					color: '#6B7280'
				}
			},
			y: {
				grid: {
					display: gridLines,
					color: 'rgba(107, 114, 128, 0.1)'
				},
				ticks: {
					color: '#6B7280'
				},
				beginAtZero: true
			}
		},
		interaction: {
			mode: 'index',
			intersect: false
		},
		maintainAspectRatio: false
	};

	// Merged options
	$: mergedOptions = { ...lineOptions, ...customOptions };

	// Generate chart data based on metrics and chart type
	$: chartData = (() => {
		if (customData) return customData;
		if (loading) return null;

		try {
			switch (chartType) {
				case 'daily_leads':
					return dashboardMetrics ? dashboardCharts.dailyLeadsTimeline(dashboardMetrics) : null;
				case 'score_trend':
					return dashboardMetrics ? dashboardCharts.scoreTrendTimeline(dashboardMetrics) : null;
				case 'revenue_timeline':
					return revenueMetrics ? revenueCharts.revenueTimeline(revenueMetrics) : null;
				default:
					return null;
			}
		} catch (err) {
			console.error('Error generating chart data:', err);
			return null;
		}
	})();

	// Chart title
	$: chartTitle = title || (() => {
		switch (chartType) {
			case 'daily_leads':
				return 'Daily Leads Timeline';
			case 'score_trend':
				return 'Lead Score Trend';
			case 'revenue_timeline':
				return 'Revenue Timeline';
			default:
				return 'Timeline Chart';
		}
	})();
</script>

<div class="line-chart-container">
	{#if chartTitle}
		<h3 class="text-lg font-medium text-gray-900 mb-4">{chartTitle}</h3>
	{/if}
	
	<BaseChart
		type="line"
		data={chartData}
		options={mergedOptions}
		{height}
		{loading}
		{error}
		emptyMessage="No timeline data available"
	/>
</div>

<style>
	.line-chart-container {
		width: 100%;
	}
</style> 