<!-- Pie Chart Component -->
<script lang="ts">
	import BaseChart from './BaseChart.svelte';
	import { dashboardCharts } from '$lib/utils/chartData';
	import type { DashboardMetrics } from '$lib/types';
	import type { ChartOptions } from 'chart.js';

	// Props
	export let metrics: DashboardMetrics | null = null;
	export let chartType: 'status' | 'source' = 'status';
	export let title: string = '';
	export let height: number = 300;
	export let loading: boolean = false;
	export let error: string | null = null;
	export let customData: any = null;
	export let customOptions: ChartOptions = {};

	// Specific pie chart options
	const pieOptions: ChartOptions = {
		plugins: {
			legend: {
				position: 'right',
				labels: {
					usePointStyle: true,
					padding: 15,
					generateLabels: (chart) => {
						const data = chart.data;
						if (data.labels && data.datasets[0] && Array.isArray(data.datasets[0].backgroundColor)) {
							return data.labels.map((label, i) => ({
								text: label as string,
								fillStyle: (data.datasets[0].backgroundColor as string[])[i] || '#ddd',
								strokeStyle: Array.isArray(data.datasets[0].borderColor) 
									? (data.datasets[0].borderColor as string[])[i] || '#fff'
									: '#fff',
								lineWidth: 2,
								pointStyle: 'circle'
							}));
						}
						return [];
					}
				}
			},
			tooltip: {
				callbacks: {
					label: function(context) {
						const label = context.label || '';
						const value = context.parsed;
						const total = context.dataset.data
							.filter((item): item is number => typeof item === 'number')
							.reduce((a, b) => a + b, 0);
						const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
						return `${label}: ${value} (${percentage}%)`;
					}
				}
			}
		}
	};

	// Merged options
	$: mergedOptions = { ...pieOptions, ...customOptions };

	// Generate chart data based on metrics and chart type
	$: chartData = (() => {
		if (customData) return customData;
		if (!metrics) {
			console.log('PieChart: No metrics provided');
			return null;
		}

		let result;
		switch (chartType) {
			case 'status':
				result = dashboardCharts.leadStatusDistribution(metrics);
				console.log('PieChart leadStatusDistribution result:', result);
				return result;
			case 'source':
				result = dashboardCharts.leadSourceDistribution(metrics);
				console.log('PieChart leadSourceDistribution result:', result);
				return result;
			default:
				return null;
		}
	})();

	// Chart title
	$: chartTitle = title || (chartType === 'status' ? 'Lead Status Distribution' : 'Lead Source Distribution');
</script>

<div class="pie-chart-container">
	{#if chartTitle}
		<h3 class="text-lg font-medium text-gray-900 mb-4">{chartTitle}</h3>
	{/if}
	
	<BaseChart
		type="pie"
		data={chartData}
		options={mergedOptions}
		{height}
		{loading}
		{error}
		emptyMessage="No data available for pie chart"
	/>
</div>

<style>
	.pie-chart-container {
		width: 100%;
	}
</style> 