<!-- Bar Chart Component -->
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
					return value.toLocaleString();
				}
			}
		}
	} : barOptions;

	// Merged options
	$: mergedOptions = { ...finalOptions, ...customOptions };
</script>

<div class="bar-chart-container">
	{#if title}
		<h3 class="text-lg font-medium text-gray-900 mb-4">{title}</h3>
	{/if}
	
	<BaseChart
		type="bar"
		{data}
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