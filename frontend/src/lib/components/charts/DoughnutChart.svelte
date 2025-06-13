<!-- Doughnut Chart Component -->
<script lang="ts">
	import BaseChart from './BaseChart.svelte';
	import type { ChartOptions } from 'chart.js';

	// Props
	export let data: any = null;
	export let title: string = '';
	export let height: number = 300;
	export let loading: boolean = false;
	export let error: string | null = null;
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
				const chartData = chart.data;
				if (chartData.labels && chartData.datasets[0] && Array.isArray(chartData.datasets[0].backgroundColor)) {
					return chartData.labels.map((label, i) => ({
						text: label as string,
						fillStyle: (chartData.datasets[0].backgroundColor as string[])[i] || '#ddd',
						strokeStyle: Array.isArray(chartData.datasets[0].borderColor) 
							? (chartData.datasets[0].borderColor as string[])[i] || '#fff'
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
</script>

<div class="doughnut-chart-container">
	{#if title}
		<h3 class="text-lg font-medium text-gray-900 mb-4">{title}</h3>
	{/if}
	
	<BaseChart
		type="doughnut"
		{data}
		options={mergedOptions}
		{height}
		{loading}
		{error}
		emptyMessage="No data available for doughnut chart"
	/>
	
	{#if showCenterText && centerText && data}
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