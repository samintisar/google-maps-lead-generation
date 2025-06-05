<!-- Analytics Page - In Development -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { 
		metricsStore, 
		dashboardMetrics, 
		revenueMetrics, 
		funnelMetrics, 
		metricsLoading 
	} from '$lib/stores/metrics';

	onMount(async () => {
		try {
			// Load metrics data
			await metricsStore.loadDashboardMetrics();
			await metricsStore.loadRevenueMetrics();
			await metricsStore.loadFunnelMetrics();
		} catch (error) {
			console.error('Failed to load analytics:', error);
		}
	});

	// Reactive statements to get data from stores
	$: loading = $metricsLoading.dashboard || $metricsLoading.revenue || $metricsLoading.funnel;
</script>

<svelte:head>
	<title>Analytics - LMA Platform</title>
</svelte:head>

<div class="p-6">
	<div class="mb-6">
		<h1 class="text-3xl font-semibold text-gray-900">Analytics Dashboard</h1>
		<p class="text-gray-600 mt-2">Track performance and gain insights into your lead management activities.</p>
	</div>

	{#if loading}
		<div class="flex justify-center items-center h-64">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			<span class="ml-3 text-gray-600">Loading analytics...</span>
		</div>
	{:else}
		<!-- Key Metrics Summary -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
			{#if $dashboardMetrics}
				<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-gray-600">Total Leads</p>
							<p class="text-2xl font-semibold text-gray-900">{$dashboardMetrics.overview.total_leads}</p>
						</div>
						<div class="p-3 bg-blue-100 rounded-full">
							<svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 515.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 919.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM9 9a2 2 0 11-4 0 2 2 0 014 0z" />
							</svg>
						</div>
					</div>
					<div class="mt-2 flex items-center text-sm">
						<span class="text-green-600 font-medium">+{$dashboardMetrics.overview.new_leads}</span>
						<span class="text-gray-600 ml-1">this week</span>
					</div>
				</div>

				<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-gray-600">Converted</p>
							<p class="text-2xl font-semibold text-gray-900">{$dashboardMetrics.overview.won_leads}</p>
						</div>
						<div class="p-3 bg-green-100 rounded-full">
							<svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
						</div>
					</div>
					<div class="mt-2 flex items-center text-sm">
						<span class="text-gray-600">
							{($dashboardMetrics.overview.win_rate * 100).toFixed(1)}% conversion rate
						</span>
					</div>
				</div>

				<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-gray-600">Total Revenue</p>
							<p class="text-2xl font-semibold text-gray-900">${$dashboardMetrics.overview.total_revenue.toLocaleString()}</p>
						</div>
						<div class="p-3 bg-yellow-100 rounded-full">
							<svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
							</svg>
						</div>
					</div>
					<div class="mt-2 flex items-center text-sm">
						<span class="text-green-600 font-medium">{$dashboardMetrics.overview.deals_count} deals</span>
						<span class="text-gray-600 ml-1">closed</span>
					</div>
				</div>

				<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm font-medium text-gray-600">Avg Deal Size</p>
							<p class="text-2xl font-semibold text-gray-900">${$dashboardMetrics.overview.avg_deal_size.toLocaleString()}</p>
						</div>
						<div class="p-3 bg-purple-100 rounded-full">
							<svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
							</svg>
						</div>
					</div>
					<div class="mt-2 flex items-center text-sm">
						<span class="text-gray-600">Based on closed deals</span>
					</div>
				</div>
			{/if}
		</div>

		<!-- Charts Section - Placeholder for now -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<h3 class="text-lg font-medium text-gray-900 mb-4">Lead Status Distribution</h3>
				<div class="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
					<div class="text-center">
						<svg class="w-12 h-12 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
						</svg>
						<p class="text-gray-500">Chart visualization coming soon</p>
					</div>
				</div>
			</div>

			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<h3 class="text-lg font-medium text-gray-900 mb-4">Revenue Trends</h3>
				<div class="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
					<div class="text-center">
						<svg class="w-12 h-12 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
						</svg>
						<p class="text-gray-500">Chart visualization coming soon</p>
					</div>
				</div>
			</div>
		</div>

		<!-- Funnel Analysis -->
		{#if $funnelMetrics}
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<h3 class="text-lg font-medium text-gray-900 mb-4">Conversion Funnel</h3>
				<div class="space-y-4">
					{#each $funnelMetrics.funnel_stages as stage}
						<div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
							<div>
								<h4 class="font-medium text-gray-900">{stage.stage}</h4>
								<p class="text-sm text-gray-600">{stage.count} leads</p>
							</div>
							<div class="text-right">
								<p class="text-lg font-semibold text-gray-900">{(stage.conversion_rate * 100).toFixed(1)}%</p>
								<p class="text-sm text-gray-600">{(stage.stage_conversion * 100).toFixed(1)}% stage conversion</p>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	{/if}
</div> 