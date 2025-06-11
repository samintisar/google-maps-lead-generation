<!-- Base Chart Component for Chart.js -->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Chart } from '$lib/utils/chartSetup';
	import type { ChartConfiguration, ChartType, ChartOptions } from 'chart.js';
	import { formatters } from '$lib/utils/chartData';

	// Props
	export let type: ChartType;
	export let data: any;
	export let options: ChartOptions = {};
	export let width: number = 400;
	export let height: number = 200;
	export let responsive: boolean = true;
	export let maintainAspectRatio: boolean = false;
	export let plugins: any[] = [];
	export let loading: boolean = false;
	export let error: string | null = null;
	export let emptyMessage: string = 'No data available';

	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;
	let container: HTMLDivElement;

	// Default chart options
	const defaultOptions: ChartOptions = {
		responsive,
		maintainAspectRatio,
		animation: {
			duration: 750,
			easing: 'easeInOutQuart'
		},
		interaction: {
			intersect: false,
			mode: 'index'
		},
		plugins: {
			legend: {
				display: true,
				position: 'top',
				labels: {
					usePointStyle: true,
					padding: 20,
					font: {
						size: 12,
						family: "'Inter', sans-serif"
					}
				}
			},
			tooltip: {
				enabled: true,
				backgroundColor: 'rgba(0, 0, 0, 0.8)',
				titleColor: '#fff',
				bodyColor: '#fff',
				borderColor: 'rgba(255, 255, 255, 0.1)',
				borderWidth: 1,
				cornerRadius: 6,
				displayColors: true,
				padding: 12,
				titleFont: {
					size: 13,
					weight: 'bold'
				},
				bodyFont: {
					size: 12
				},
				callbacks: {
					label: function(context) {
						const label = context.dataset.label || '';
						const value = context.parsed.y;
						
						// Format based on chart type and data
						if (type === 'pie' || type === 'doughnut') {
							const total = context.dataset.data
								.filter((item): item is number => typeof item === 'number')
								.reduce((a, b) => a + b, 0);
							const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
							return `${label}: ${value} (${percentage}%)`;
						}
						
						// Check if value looks like currency
						if (label.toLowerCase().includes('revenue') || label.toLowerCase().includes('value')) {
							return `${label}: ${formatters.formatCurrency(value)}`;
						}
						
						return `${label}: ${formatters.formatNumber(value)}`;
					}
				}
			}
		},
		scales: type === 'pie' || type === 'doughnut' ? undefined : {
			x: {
				grid: {
					display: false
				},
				ticks: {
					font: {
						size: 11,
						family: "'Inter', sans-serif"
					},
					color: '#6B7280'
				}
			},
			y: {
				grid: {
					color: 'rgba(107, 114, 128, 0.1)'
				},
				ticks: {
					font: {
						size: 11,
						family: "'Inter', sans-serif"
					},
					color: '#6B7280',
					callback: function(value) {
						// Auto-format y-axis based on common patterns
						if (typeof value === 'number') {
							if (value >= 1000000) {
								return formatters.formatNumber(value);
							} else if (value >= 1000) {
								return formatters.formatNumber(value);
							}
						}
						return value;
					}
				}
			}
		}
	};

	// Merge options
	$: mergedOptions = { ...defaultOptions, ...options };

	// Create or update chart
	function createChart() {
		if (!canvas || !data || isEmpty) {
			console.log('BaseChart createChart aborted:', { canvas: !!canvas, data: !!data, isEmpty, type });
			return;
		}

		console.log('BaseChart creating chart:', { type, data, isEmpty });
		destroyChart();

		const config: ChartConfiguration = {
			type,
			data,
			options: mergedOptions,
			plugins
		};

		try {
			chart = new Chart(canvas, config);
			console.log('BaseChart created successfully:', chart);
		} catch (err) {
			console.error('Failed to create chart:', err);
			error = 'Failed to render chart';
		}
	}

	function updateChart() {
		if (!chart || !data || isEmpty) return;

		chart.data = data;
		chart.options = mergedOptions;
		chart.update('none');
	}

	function destroyChart() {
		if (chart) {
			chart.destroy();
			chart = null;
		}
	}

	// Handle resize
	function handleResize() {
		if (chart && responsive) {
			chart.resize();
		}
	}

	// Lifecycle
	onMount(() => {
		if (data && !loading && !error && !isEmpty) {
			createChart();
		}

		// Add resize listener
		if (typeof window !== 'undefined') {
			window.addEventListener('resize', handleResize);
		}
	});

	// Reactive statement for chart updates
	$: if (chart && data && !loading && !error && !isEmpty) {
		updateChart();
	} else if (!chart && data && !loading && !error && !isEmpty) {
		createChart();
	}

	onDestroy(() => {
		destroyChart();
		
		if (typeof window !== 'undefined') {
			window.removeEventListener('resize', handleResize);
		}
	});

	// Check if data is empty
	$: isEmpty = !data || 
		!data.datasets || 
		data.datasets.length === 0 || 
		data.datasets.every((dataset: any) => !dataset.data || dataset.data.length === 0);
	
	// Debug isEmpty calculation
	$: {
		console.log('BaseChart isEmpty check:', {
			data: !!data,
			hasDatasets: data?.datasets ? true : false,
			datasetsLength: data?.datasets?.length,
			datasetDataLengths: data?.datasets?.map((d: any) => d.data?.length),
			isEmpty,
			type
		});
	}
</script>

<div bind:this={container} class="chart-container relative">
	{#if loading}
		<div class="flex items-center justify-center bg-gray-50 rounded-lg" style="height: {height}px;">
			<div class="flex items-center space-x-3">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
				<span class="text-sm text-gray-600">Loading chart...</span>
			</div>
		</div>
	{:else if error}
		<div class="flex items-center justify-center bg-red-50 rounded-lg" style="height: {height}px;">
			<div class="text-center">
				<svg class="w-8 h-8 text-red-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				<p class="text-sm text-red-600">{error}</p>
			</div>
		</div>
	{:else if isEmpty}
		<div class="flex items-center justify-center bg-gray-50 rounded-lg" style="height: {height}px;">
			<div class="text-center">
				<svg class="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
				</svg>
				<p class="text-sm text-gray-500">{emptyMessage}</p>
			</div>
		</div>
	{:else}
		<canvas 
			bind:this={canvas}
			{width}
			{height}
			class="chart-canvas"
		></canvas>
	{/if}
</div>

<style>
	.chart-container {
		position: relative;
	}
	
	.chart-canvas {
		max-width: 100%;
		height: auto;
	}
</style> 