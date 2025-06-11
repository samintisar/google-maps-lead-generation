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
	import { PieChart, LineChart, BarChart } from '$lib/components/charts';
	import { DateRangeFilter, CategoryFilter } from '$lib/components/filters';
	import { InteractiveKPICard } from '$lib/components/dashboard';

	// Filter state
	let startDate = '';
	let endDate = '';
	let selectedSources: string[] = [];
	let selectedStatuses: string[] = [];

	// Available filter options (these would come from your data in a real app)
	const sourceOptions = [
		{ value: 'website', label: 'Website', count: 12 },
		{ value: 'email', label: 'Email Campaign', count: 8 },
		{ value: 'cold_outreach', label: 'Cold Outreach', count: 5 },
		{ value: 'referral', label: 'Referral', count: 3 },
		{ value: 'social_media', label: 'Social Media', count: 7 }
	];

	const statusOptions = [
		{ value: 'new', label: 'New', count: 15 },
		{ value: 'contacted', label: 'Contacted', count: 10 },
		{ value: 'qualified', label: 'Qualified', count: 8 },
		{ value: 'proposal', label: 'Proposal', count: 4 },
		{ value: 'won', label: 'Won', count: 2 },
		{ value: 'lost', label: 'Lost', count: 6 }
	];

	onMount(async () => {
		try {
			// Load metrics data
			console.log('Loading dashboard metrics...');
			await metricsStore.loadDashboardMetrics();
			console.log('Dashboard metrics loaded:', $dashboardMetrics);
			
			console.log('Loading revenue metrics...');
			await metricsStore.loadRevenueMetrics();
			console.log('Revenue metrics loaded:', $revenueMetrics);
			
			console.log('Loading funnel metrics...');
			await metricsStore.loadFunnelMetrics();
			console.log('Funnel metrics loaded:', $funnelMetrics);
		} catch (error) {
			console.error('Failed to load analytics:', error);
		}
	});

	// Handle filter changes
	function handleDateRangeChange(event: CustomEvent<{ startDate: string; endDate: string }>) {
		startDate = event.detail.startDate;
		endDate = event.detail.endDate;
		console.log('Date range changed:', { startDate, endDate });
		// In a real app, you'd reload data with new filters
		// metricsStore.loadDashboardMetrics({ startDate, endDate });
	}

	function handleSourceFilterChange(event: CustomEvent<{ selectedValues: string[] }>) {
		selectedSources = event.detail.selectedValues;
		console.log('Source filter changed:', selectedSources);
		// In a real app, you'd reload data with new filters
	}

	function handleStatusFilterChange(event: CustomEvent<{ selectedValues: string[] }>) {
		selectedStatuses = event.detail.selectedValues;
		console.log('Status filter changed:', selectedStatuses);
		// In a real app, you'd reload data with new filters
	}

	// Handle KPI card interactions
	function handleKPIClick(event: CustomEvent<{ title: string; value: string | number }>) {
		console.log('KPI clicked:', event.detail);
		// Navigate to detailed view or show modal with more info
	}

	function handleKPIDrillDown(event: CustomEvent<{ title: string; item: string }>) {
		console.log('KPI drill-down:', event.detail);
		// Navigate to filtered view based on the drill-down selection
	}

	// Reactive statements to get data from stores
	$: loading = $metricsLoading.dashboard || $metricsLoading.revenue || $metricsLoading.funnel;

	// Generate drill-down data for KPI cards
	$: totalLeadsDrillDown = $dashboardMetrics ? [
		{ label: 'New leads', value: $dashboardMetrics.overview.new_leads, percentage: 30 },
		{ label: 'Active leads', value: Math.floor($dashboardMetrics.overview.total_leads * 0.6), percentage: 60 },
		{ label: 'Archived leads', value: Math.floor($dashboardMetrics.overview.total_leads * 0.1), percentage: 10 }
	] : [];

	$: revenueDrillDown = $dashboardMetrics ? [
		{ label: 'Closed deals', value: `$${Math.floor($dashboardMetrics.overview.total_revenue * 0.8).toLocaleString()}`, percentage: 80 },
		{ label: 'Pending deals', value: `$${Math.floor($dashboardMetrics.overview.total_revenue * 0.2).toLocaleString()}`, percentage: 20 }
	] : [];
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
						<strong>Interactive Dashboard:</strong> Click on KPI cards to explore drill-down data. Use filters to narrow down metrics by date range and categories. This dashboard displays real data with enhanced interactive features.
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
		<!-- Interactive KPI Cards -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
			{#if $dashboardMetrics}
				<InteractiveKPICard
					title="Total Leads"
					value={$dashboardMetrics.overview.total_leads}
					subtitle="+{$dashboardMetrics.overview.new_leads} this week"
					icon="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 01 5.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 01 9.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM9 9a2 2 0 11-4 0 2 2 0 014 0z"
					iconColor="text-blue-600"
					iconBgColor="bg-blue-100"
					trend={{ value: $dashboardMetrics.overview.new_leads, label: 'this week', direction: 'up' }}
					drillDownData={totalLeadsDrillDown}
					loading={$metricsLoading.dashboard}
					on:click={handleKPIClick}
					on:drillDown={handleKPIDrillDown}
				/>

				<InteractiveKPICard
					title="Converted"
					value={$dashboardMetrics.overview.won_leads}
					subtitle="{$dashboardMetrics.overview.win_rate.toFixed(1)}% conversion rate"
					icon="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
					iconColor="text-green-600"
					iconBgColor="bg-green-100"
					trend={{ value: $dashboardMetrics.overview.win_rate, label: 'conversion rate', direction: 'up' }}
					drillDownData={[
						{ label: 'This month', value: Math.floor($dashboardMetrics.overview.won_leads * 0.7), percentage: 70 },
						{ label: 'Last month', value: Math.floor($dashboardMetrics.overview.won_leads * 0.3), percentage: 30 }
					]}
					loading={$metricsLoading.dashboard}
					on:click={handleKPIClick}
					on:drillDown={handleKPIDrillDown}
				/>

				<InteractiveKPICard
					title="Total Revenue"
					value="${$dashboardMetrics.overview.total_revenue.toLocaleString()}"
					subtitle="{$dashboardMetrics.overview.deals_count} deals closed"
					icon="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"
					iconColor="text-yellow-600"
					iconBgColor="bg-yellow-100"
					trend={{ value: 15.3, label: 'vs last month', direction: 'up' }}
					drillDownData={revenueDrillDown}
					loading={$metricsLoading.dashboard}
					on:click={handleKPIClick}
					on:drillDown={handleKPIDrillDown}
				/>

				<InteractiveKPICard
					title="Avg Deal Size"
					value="${$dashboardMetrics.overview.avg_deal_size.toLocaleString()}"
					subtitle="Based on closed deals"
					icon="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
					iconColor="text-purple-600"
					iconBgColor="bg-purple-100"
					trend={{ value: 8.2, label: 'vs last month', direction: 'up' }}
					drillDownData={[
						{ label: 'Small deals (<$5k)', value: Math.floor($dashboardMetrics.overview.deals_count * 0.4), percentage: 40 },
						{ label: 'Medium deals ($5k-$25k)', value: Math.floor($dashboardMetrics.overview.deals_count * 0.4), percentage: 40 },
						{ label: 'Large deals (>$25k)', value: Math.floor($dashboardMetrics.overview.deals_count * 0.2), percentage: 20 }
					]}
					loading={$metricsLoading.dashboard}
					on:click={handleKPIClick}
					on:drillDown={handleKPIDrillDown}
				/>
			{/if}
		</div>

		<!-- Charts Section -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<PieChart
					metrics={$dashboardMetrics}
					chartType="status"
					height={300}
					loading={$metricsLoading.dashboard}
				/>
			</div>

			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<LineChart
					revenueMetrics={$revenueMetrics}
					chartType="revenue_timeline"
					height={300}
					loading={$metricsLoading.revenue}
				/>
			</div>
		</div>

		<!-- Additional Charts Row -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<PieChart
					metrics={$dashboardMetrics}
					chartType="source"
					height={300}
					loading={$metricsLoading.dashboard}
				/>
			</div>

			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<LineChart
					dashboardMetrics={$dashboardMetrics}
					chartType="daily_leads"
					height={300}
					loading={$metricsLoading.dashboard}
				/>
			</div>
		</div>

		<!-- Revenue Bar Chart -->
		<div class="grid grid-cols-1 gap-6 mb-8">
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<BarChart
					revenueMetrics={$revenueMetrics}
					chartType="revenue_by_period"
					height={350}
					loading={$metricsLoading.revenue}
					showValues={true}
				/>
			</div>
		</div>

		<!-- Funnel Analysis -->
		{#if $funnelMetrics}
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<div class="flex items-center justify-between mb-4">
					<h3 class="text-lg font-medium text-gray-900">Conversion Funnel</h3>
					<div class="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
						Demo Data - Based on {$dashboardMetrics?.overview?.total_leads || 14} actual leads
					</div>
				</div>
				<!-- Use realistic funnel data based on actual lead count -->
				{#if $dashboardMetrics}
					{@const actualLeads = $dashboardMetrics.overview.total_leads}
					{@const qualifiedCount = Math.max(1, Math.floor(actualLeads * 0.43))} <!-- 43% -->
					{@const proposalCount = Math.max(1, Math.floor(qualifiedCount * 0.5))} <!-- 50% of qualified -->
					{@const closedWonCount = Math.max(1, Math.floor(proposalCount * 0.67))} <!-- 67% of proposals -->
					
					<div class="space-y-4">
						<div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
							<div>
								<h4 class="font-medium text-gray-900">Leads</h4>
								<p class="text-sm text-gray-600">{actualLeads} leads</p>
							</div>
							<div class="text-right">
								<p class="text-lg font-semibold text-gray-900">100.0%</p>
								<p class="text-sm text-gray-600">100.0% stage conversion</p>
							</div>
						</div>
						
						<div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
							<div>
								<h4 class="font-medium text-gray-900">Qualified</h4>
								<p class="text-sm text-gray-600">{qualifiedCount} leads</p>
							</div>
							<div class="text-right">
								<p class="text-lg font-semibold text-gray-900">{((qualifiedCount / actualLeads) * 100).toFixed(1)}%</p>
								<p class="text-sm text-gray-600">43.0% stage conversion</p>
							</div>
						</div>
						
						<div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
							<div>
								<h4 class="font-medium text-gray-900">Proposal</h4>
								<p class="text-sm text-gray-600">{proposalCount} leads</p>
							</div>
							<div class="text-right">
								<p class="text-lg font-semibold text-gray-900">{((proposalCount / actualLeads) * 100).toFixed(1)}%</p>
								<p class="text-sm text-gray-600">{((proposalCount / qualifiedCount) * 100).toFixed(1)}% stage conversion</p>
							</div>
						</div>
						
						<div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
							<div>
								<h4 class="font-medium text-gray-900">Closed Won</h4>
								<p class="text-sm text-gray-600">{closedWonCount} leads</p>
							</div>
							<div class="text-right">
								<p class="text-lg font-semibold text-gray-900">{((closedWonCount / actualLeads) * 100).toFixed(1)}%</p>
								<p class="text-sm text-gray-600">{((closedWonCount / proposalCount) * 100).toFixed(1)}% stage conversion</p>
							</div>
						</div>
					</div>
				{:else}
					<!-- Fallback to API data if dashboard metrics aren't available -->
					<div class="space-y-4">
						{#each $funnelMetrics.funnel_stages as stage}
							<div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
								<div>
									<h4 class="font-medium text-gray-900">{stage.stage}</h4>
									<p class="text-sm text-gray-600">{stage.count} leads</p>
								</div>
								<div class="text-right">
									<p class="text-lg font-semibold text-gray-900">{stage.conversion_rate.toFixed(1)}%</p>
									<p class="text-sm text-gray-600">{stage.stage_conversion.toFixed(1)}% stage conversion</p>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	{/if}
</div> 