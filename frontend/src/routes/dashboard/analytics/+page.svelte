<!-- Analytics Page - In Development -->
<script lang="ts">
	import { onMount } from 'svelte';
	// Metrics store removed - using static data
	import { PieChart, LineChart, BarChart } from '$lib/components/charts';
	import { DateRangeFilter, CategoryFilter } from '$lib/components/filters';

	// Static data - replaces metrics store
	const dashboardMetrics = {
		overview: {
			total_leads: 14,
			new_leads: 5,
			won_leads: 8,
			win_rate: 57.1,
			total_revenue: 125000,
			deals_count: 6,
			avg_deal_size: 20833
		}
	};
	
	const revenueMetrics = {
		monthly_revenue: [
			{ month: 'Jan', revenue: 85000 },
			{ month: 'Feb', revenue: 92000 },
			{ month: 'Mar', revenue: 125000 }
		]
	};
	
	const funnelMetrics = {
		funnel_stages: [
			{ stage: 'Lead', count: 14 },
			{ stage: 'Qualified', count: 10 },
			{ stage: 'Demo', count: 8 },
			{ stage: 'Closed', count: 6 }
		]
	};

	// UI state
	let loading = false;
	let startDate = '2024-01-01';
	let endDate = '2024-03-31';
	let selectedSources: string[] = [];
	let selectedStatuses: string[] = [];

	// Filter options
	const sourceOptions = [
		{ value: 'website', label: 'Website' },
		{ value: 'social', label: 'Social Media' },
		{ value: 'email', label: 'Email Campaign' },
		{ value: 'referral', label: 'Referral' }
	];

	const statusOptions = [
		{ value: 'new', label: 'New' },
		{ value: 'contacted', label: 'Contacted' },
		{ value: 'qualified', label: 'Qualified' },
		{ value: 'lost', label: 'Lost' }
	];

	onMount(async () => {
		// Static data loaded - no API calls needed
		loading = false;
	});

	// Handle filter changes
	function handleDateRangeChange(event: CustomEvent<{ startDate: string; endDate: string }>) {
		startDate = event.detail.startDate;
		endDate = event.detail.endDate;
		console.log('Date range changed:', { startDate, endDate });
	}

	function handleSourceFilterChange(event: CustomEvent<{ selectedValues: string[] }>) {
		selectedSources = event.detail.selectedValues;
		console.log('Source filter changed:', selectedSources);
	}

	function handleStatusFilterChange(event: CustomEvent<{ selectedValues: string[] }>) {
		selectedStatuses = event.detail.selectedValues;
		console.log('Status filter changed:', selectedStatuses);
	}

	// Handle KPI card interactions
	function handleKPIClick(event: CustomEvent<{ title: string; value: string | number }>) {
		console.log('KPI clicked:', event.detail);
	}

	function handleKPIDrillDown(event: CustomEvent<{ title: string; item: string }>) {
		console.log('KPI drill-down:', event.detail);
	}

	// Generate drill-down data for KPI cards
	const totalLeadsDrillDown = [
		{ label: 'New leads', value: dashboardMetrics.overview.new_leads, percentage: 30 },
		{ label: 'Active leads', value: Math.floor(dashboardMetrics.overview.total_leads * 0.6), percentage: 60 },
		{ label: 'Archived leads', value: Math.floor(dashboardMetrics.overview.total_leads * 0.1), percentage: 10 }
	];

	const revenueDrillDown = [
		{ label: 'Closed deals', value: `$${Math.floor(dashboardMetrics.overview.total_revenue * 0.8).toLocaleString()}`, percentage: 80 },
		{ label: 'Pending deals', value: `$${Math.floor(dashboardMetrics.overview.total_revenue * 0.2).toLocaleString()}`, percentage: 20 }
	];
</script>

<svelte:head>
	<title>Analytics - LMA Platform</title>
</svelte:head>

<div class="p-6">
	<div class="mb-6">
		<h1 class="text-3xl font-semibold text-gray-900">Analytics Dashboard</h1>
		<p class="text-gray-600 mt-2">Track performance and gain insights into your lead management activities.</p>
		<div class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
			<div class="flex">
				<svg class="flex-shrink-0 h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
					<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
				</svg>
				<div class="ml-3">
					<p class="text-sm text-blue-700">
						<strong>Static Dashboard:</strong> This dashboard displays static data for demonstration purposes. Authentication and metrics systems have been removed.
					</p>
				</div>
			</div>
		</div>
	</div>

	<!-- Filters Section -->
	{#if !loading}
		<div class="mb-8">
			<h2 class="text-lg font-medium text-gray-900 mb-4">Filters</h2>
			<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
				<DateRangeFilter
					bind:startDate
					bind:endDate
					on:change={handleDateRangeChange}
					disabled={loading}
				/>
				
				<CategoryFilter
					title="Lead Sources"
					icon="source"
					options={sourceOptions}
					bind:selectedValues={selectedSources}
					on:change={handleSourceFilterChange}
					disabled={loading}
				/>
				
				<CategoryFilter
					title="Lead Status"
					icon="status"
					options={statusOptions}
					bind:selectedValues={selectedStatuses}
					on:change={handleStatusFilterChange}
					disabled={loading}
				/>
			</div>
		</div>
	{/if}

	{#if loading}
		<div class="flex justify-center items-center h-64">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			<span class="ml-3 text-gray-600">Loading analytics...</span>
		</div>
	{:else}
		<!-- Static KPI Cards -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
			<div class="bg-white rounded-lg shadow border border-gray-200 p-6">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="bg-blue-100 rounded-md p-3">
							<svg class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 01 5.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 01 9.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM9 9a2 2 0 11-4 0 2 2 0 014 0z" />
							</svg>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">Total Leads</dt>
							<dd class="text-lg font-medium text-gray-900">{dashboardMetrics.overview.total_leads}</dd>
						</dl>
					</div>
				</div>
			</div>

			<div class="bg-white rounded-lg shadow border border-gray-200 p-6">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="bg-green-100 rounded-md p-3">
							<svg class="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">Converted</dt>
							<dd class="text-lg font-medium text-gray-900">{dashboardMetrics.overview.won_leads}</dd>
						</dl>
					</div>
				</div>
			</div>

			<div class="bg-white rounded-lg shadow border border-gray-200 p-6">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="bg-yellow-100 rounded-md p-3">
							<svg class="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
							</svg>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">Total Revenue</dt>
							<dd class="text-lg font-medium text-gray-900">${dashboardMetrics.overview.total_revenue.toLocaleString()}</dd>
						</dl>
					</div>
				</div>
			</div>

			<div class="bg-white rounded-lg shadow border border-gray-200 p-6">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="bg-purple-100 rounded-md p-3">
							<svg class="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
							</svg>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">Avg Deal Size</dt>
							<dd class="text-lg font-medium text-gray-900">${dashboardMetrics.overview.avg_deal_size.toLocaleString()}</dd>
						</dl>
					</div>
				</div>
			</div>
		</div>

		<!-- Simple Charts Section -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<h3 class="text-lg font-medium text-gray-900 mb-4">Lead Status Distribution</h3>
				<div class="space-y-3">
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600">New</span>
						<span class="text-sm font-medium">5</span>
					</div>
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600">Contacted</span>
						<span class="text-sm font-medium">3</span>
					</div>
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600">Qualified</span>
						<span class="text-sm font-medium">4</span>
					</div>
					<div class="flex justify-between items-center">
						<span class="text-sm text-gray-600">Won</span>
						<span class="text-sm font-medium">2</span>
					</div>
				</div>
			</div>

			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<h3 class="text-lg font-medium text-gray-900 mb-4">Monthly Revenue</h3>
				<div class="space-y-3">
					{#each revenueMetrics.monthly_revenue as month}
						<div class="flex justify-between items-center">
							<span class="text-sm text-gray-600">{month.month}</span>
							<span class="text-sm font-medium">${month.revenue.toLocaleString()}</span>
						</div>
					{/each}
				</div>
			</div>
		</div>

		<!-- Sales Funnel -->
		<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
			<h3 class="text-lg font-medium text-gray-900 mb-4">Sales Funnel</h3>
			<div class="space-y-4">
				{#each funnelMetrics.funnel_stages as stage}
					<div class="flex items-center justify-between">
						<div class="flex items-center">
							<div class="w-4 h-4 bg-blue-500 rounded mr-3"></div>
							<span class="text-sm font-medium text-gray-700">{stage.stage}</span>
						</div>
						<span class="text-sm text-gray-600">{stage.count}</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div> 