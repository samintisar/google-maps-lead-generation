<!-- Line Chart Component -->
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
</script>

<div class="line-chart-container">
	{#if title}
		<h3 class="text-lg font-medium text-gray-900 mb-4">{title}</h3>
	{/if}
	
	<BaseChart
		type="line"
		{data}
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