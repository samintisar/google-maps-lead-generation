<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { 
		metricsStore, 
		dashboardMetrics, 
		metricsLoading, 
		metricsError,
		formatCurrency,
		formatPercentage,
		cleanupMetricsAutoRefresh
	} from '$lib/stores/metrics';
	import { authStore } from '$lib/stores/auth';

	// Load metrics when component mounts
	onMount(async () => {
		await metricsStore.loadDashboardMetrics();
	});

	// Clean up auto-refresh when component unmounts
	onDestroy(() => {
		cleanupMetricsAutoRefresh();
	});
</script>

<svelte:head>
	<title>Dashboard - LMA Platform</title>
</svelte:head>

<div class="py-6">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
		<!-- Page header -->
		<h1 class="text-2xl font-semibold text-gray-900">Dashboard</h1>
	</div>
	<div class="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
		<!-- Dashboard content -->
		<div class="py-4">
			<!-- Welcome section -->
			<div class="bg-white overflow-hidden shadow rounded-lg mb-6">
				<div class="px-4 py-5 sm:p-6">
					<h2 class="text-lg font-medium text-gray-900 mb-2">
						Welcome back, {$authStore.user?.username || 'User'}!
					</h2>
					<p class="text-sm text-gray-600">
						Here's an overview of your lead management activity.
					</p>
				</div>
			</div>

			<!-- Error message -->
			{#if $metricsError}
				<div class="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
					<div class="flex">
						<div class="flex-shrink-0">
							<svg class="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
							</svg>
						</div>
						<div class="ml-3">
							<p class="text-sm text-red-800">{$metricsError}</p>
						</div>
					</div>
				</div>
			{/if}

			<!-- Stats grid -->
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
				<div class="bg-white overflow-hidden shadow rounded-lg">
					<div class="p-5">
						<div class="flex items-center">
							<div class="flex-shrink-0">
								<svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
								</svg>
							</div>
							<div class="ml-5 w-0 flex-1">
								<dl>
									<dt class="text-sm font-medium text-gray-500 truncate">Total Leads</dt>
									<dd class="text-lg font-medium text-gray-900">
										{#if $metricsLoading.dashboard}
											<div class="animate-pulse bg-gray-200 h-6 w-16 rounded"></div>
										{:else if $dashboardMetrics}
											{$dashboardMetrics.overview.total_leads.toLocaleString()}
										{:else}
											--
										{/if}
									</dd>
								</dl>
							</div>
						</div>
					</div>
				</div>

				<div class="bg-white overflow-hidden shadow rounded-lg">
					<div class="p-5">
						<div class="flex items-center">
							<div class="flex-shrink-0">
								<svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
								</svg>
							</div>
							<div class="ml-5 w-0 flex-1">
								<dl>
									<dt class="text-sm font-medium text-gray-500 truncate">New This Period</dt>
									<dd class="text-lg font-medium text-gray-900">
										{#if $metricsLoading.dashboard}
											<div class="animate-pulse bg-gray-200 h-6 w-16 rounded"></div>
										{:else if $dashboardMetrics}
											{$dashboardMetrics.overview.new_leads.toLocaleString()}
										{:else}
											--
										{/if}
									</dd>
								</dl>
							</div>
						</div>
					</div>
				</div>

				<div class="bg-white overflow-hidden shadow rounded-lg">
					<div class="p-5">
						<div class="flex items-center">
							<div class="flex-shrink-0">
								<svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
							</div>
							<div class="ml-5 w-0 flex-1">
								<dl>
									<dt class="text-sm font-medium text-gray-500 truncate">Won Deals</dt>
									<dd class="text-lg font-medium text-gray-900">
										{#if $metricsLoading.dashboard}
											<div class="animate-pulse bg-gray-200 h-6 w-16 rounded"></div>
										{:else if $dashboardMetrics}
											{$dashboardMetrics.overview.won_leads.toLocaleString()}
										{:else}
											--
										{/if}
									</dd>
								</dl>
							</div>
						</div>
					</div>
				</div>

				<div class="bg-white overflow-hidden shadow rounded-lg">
					<div class="p-5">
						<div class="flex items-center">
							<div class="flex-shrink-0">
								<svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
								</svg>
							</div>
							<div class="ml-5 w-0 flex-1">
								<dl>
									<dt class="text-sm font-medium text-gray-500 truncate">Revenue</dt>
									<dd class="text-lg font-medium text-gray-900">
										{#if $metricsLoading.dashboard}
											<div class="animate-pulse bg-gray-200 h-6 w-16 rounded"></div>
										{:else if $dashboardMetrics}
											{formatCurrency($dashboardMetrics.overview.total_revenue)}
										{:else}
											--
										{/if}
									</dd>
								</dl>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Quick actions -->
			<div class="bg-white shadow rounded-lg">
				<div class="px-4 py-5 sm:p-6">
					<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Quick Actions</h3>
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
						<a
							href="/dashboard/leads"
							class="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
						>
							<div class="flex-shrink-0">
								<svg class="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
								</svg>
							</div>
							<div class="flex-1 min-w-0">
								<p class="text-sm font-medium text-gray-900">View All Leads</p>
								<p class="text-sm text-gray-500">Manage your lead pipeline</p>
							</div>
						</a>

						<a
							href="/dashboard/leads/new"
							class="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
						>
							<div class="flex-shrink-0">
								<svg class="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
								</svg>
							</div>
							<div class="flex-1 min-w-0">
								<p class="text-sm font-medium text-gray-900">Add New Lead</p>
								<p class="text-sm text-gray-500">Capture a new prospect</p>
							</div>
						</a>

						<a
							href="/dashboard/analytics"
							class="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
						>
							<div class="flex-shrink-0">
								<svg class="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
								</svg>
							</div>
							<div class="flex-1 min-w-0">
								<p class="text-sm font-medium text-gray-900">View Analytics</p>
								<p class="text-sm text-gray-500">Track performance metrics</p>
							</div>
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>
</div> 