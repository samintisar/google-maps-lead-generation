<!-- Doughnut Chart Component -->
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
	export let cutout: string = '50%'; // Size of the hole in the center
	export let showCenterText: boolean = false;
	export let centerText: string = '';

	// Specific doughnut chart options
	const doughnutOptions: ChartOptions & { cutout?: string } = {
		cutout,
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

	// Add center text plugin if enabled
	$: finalOptions = showCenterText ? {
		...doughnutOptions,
		plugins: {
			...doughnutOptions.plugins,
			centerText: {
				display: true,
				text: centerText
			}
		}
	} : doughnutOptions;

	// Merged options
	$: mergedOptions = { ...finalOptions, ...customOptions };

	// Generate chart data based on metrics and chart type
	$: chartData = (() => {
		if (customData) return customData;
		if (!metrics) return null;

		switch (chartType) {
			case 'status':
				return dashboardCharts.leadStatusDistribution(metrics);
			case 'source':
				return dashboardCharts.leadSourceDistribution(metrics);
			default:
				return null;
		}
	})();

	// Chart title
	$: chartTitle = title || (chartType === 'status' ? 'Lead Status Distribution' : 'Lead Source Distribution');
</script>

<div class="doughnut-chart-container">
	{#if chartTitle}
		<h3 class="text-lg font-medium text-gray-900 mb-4">{chartTitle}</h3>
	{/if}
	
	<BaseChart
		type="doughnut"
		data={chartData}
		options={mergedOptions}
		{height}
		{loading}
		{error}
		emptyMessage="No data available for doughnut chart"
	/>
	
	{#if showCenterText && centerText && chartData}
		<div class="absolute inset-0 flex items-center justify-center pointer-events-none">
			<div class="text-center">
				<div class="text-2xl font-bold text-gray-900">{centerText}</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.doughnut-chart-container {
		width: 100%;
		position: relative;
	}
</style> 