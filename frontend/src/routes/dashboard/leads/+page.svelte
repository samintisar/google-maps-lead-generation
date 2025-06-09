<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { leadsStore, leads, leadsLoading, leadsError, leadsPagination } from '$lib/stores/leads';
	import { LeadStatus, LeadSource } from '$lib/types';
	import type { Lead } from '$lib/types';

	// Reactive state
	let searchTerm = '';
	let statusFilter = '';
	let sourceFilter = '';
	let currentPage = 1;
	const itemsPerPage = 20;

	// Load leads on component mount
	onMount(() => {
		loadLeads();
	});

	// Load leads with current filters
	async function loadLeads() {
		const filters = {
			skip: (currentPage - 1) * itemsPerPage,
			limit: itemsPerPage,
			...(searchTerm && { search: searchTerm }),
			...(statusFilter && { status_filter: statusFilter as any }),
			...(sourceFilter && { source_filter: sourceFilter as any }),
		};

		await leadsStore.loadLeads(filters);
	}

	// Handle search
	function handleSearch() {
		currentPage = 1;
		loadLeads();
	}

	// Handle filter change
	function handleFilterChange() {
		currentPage = 1;
		loadLeads();
	}

	// Handle pagination
	function goToPage(page: number) {
		currentPage = page;
		loadLeads();
	}

	// Navigate to lead detail
	function viewLead(leadId: number) {
		goto(`/dashboard/leads/${leadId}`);
	}

	// Navigate to create new lead
	function createNewLead() {
		goto('/dashboard/leads/new');
	}

	// Delete lead
	async function deleteLead(lead: Lead) {
		if (confirm(`Are you sure you want to delete ${lead.first_name} ${lead.last_name}?`)) {
			await leadsStore.deleteLead(lead.id);
		}
	}

	// Format date
	function formatDate(dateString: string) {
		return new Date(dateString).toLocaleDateString();
	}

	// Get status badge color
	function getStatusColor(status: LeadStatus) {
		const colors = {
			[LeadStatus.NEW]: 'bg-blue-100 text-blue-800',
			[LeadStatus.CONTACTED]: 'bg-yellow-100 text-yellow-800',
			[LeadStatus.QUALIFIED]: 'bg-green-100 text-green-800',
			[LeadStatus.PROPOSAL]: 'bg-purple-100 text-purple-800',
			[LeadStatus.NEGOTIATION]: 'bg-orange-100 text-orange-800',
			[LeadStatus.WON]: 'bg-green-100 text-green-800',
			[LeadStatus.LOST]: 'bg-red-100 text-red-800',
			[LeadStatus.NURTURING]: 'bg-indigo-100 text-indigo-800',
			[LeadStatus.UNRESPONSIVE]: 'bg-gray-100 text-gray-800',
		};
		return colors[status] || 'bg-gray-100 text-gray-800';
	}

	// Clear all filters
	function clearFilters() {
		searchTerm = '';
		statusFilter = '';
		sourceFilter = '';
		currentPage = 1;
		loadLeads();
	}

	// Safe string formatter for status/source values
	function safeFormat(value: any): string {
		if (!value || typeof value !== 'string') {
			console.warn('safeFormat received invalid value:', value);
			return 'UNKNOWN';
		}
		return value.replace('_', ' ').toUpperCase();
	}

	// Get temperature badge color
	function getTemperatureColor(temperature: string | undefined): string {
		const temp = (temperature || '').toLowerCase();
		switch (temp) {
			case 'hot':
				return 'bg-red-100 text-red-800';
			case 'warm':
				return 'bg-yellow-100 text-yellow-800';
			case 'cold':
				return 'bg-blue-100 text-blue-800';
			default:
				return 'bg-gray-100 text-gray-800';
		}
	}
</script>

<svelte:head>
	<title>Leads - LMA Platform</title>
</svelte:head>

<div class="py-6">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
		<!-- Page header -->
		<div class="md:flex md:items-center md:justify-between mb-6">
			<div class="flex-1 min-w-0">
				<h1 class="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
					Leads
				</h1>
				<p class="mt-1 text-sm text-gray-500">
					Manage your lead pipeline and track prospect engagement
				</p>
			</div>
			<div class="mt-4 flex md:mt-0 md:ml-4">
				<button
					type="button"
					onclick={createNewLead}
					class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
				>
					<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
					</svg>
					Add Lead
				</button>
			</div>
		</div>

		<!-- Error message -->
		{#if $leadsError}
			<div class="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative">
				<strong class="font-bold">Error:</strong>
				<span class="block sm:inline">{$leadsError}</span>
			</div>
		{/if}

		<!-- Filters -->
		<div class="bg-white shadow rounded-lg mb-6">
			<div class="px-4 py-5 sm:p-6">
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
					<!-- Search -->
					<div>
						<label for="search" class="block text-sm font-medium text-gray-700">Search</label>
						<div class="mt-1 relative rounded-md shadow-sm">
							<input
								type="text"
								id="search"
								bind:value={searchTerm}
								onkeydown={(e) => e.key === 'Enter' && handleSearch()}
								placeholder="Name, email, or company"
								class="focus:ring-indigo-500 focus:border-indigo-500 block w-full pl-3 pr-10 py-2 sm:text-sm border-gray-300 rounded-md"
							/>
							<div class="absolute inset-y-0 right-0 pr-3 flex items-center">
								<button
									type="button"
									onclick={handleSearch}
									class="text-gray-400 hover:text-gray-600"
									aria-label="Search leads"
								>
									<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
									</svg>
								</button>
							</div>
						</div>
					</div>

					<!-- Status Filter -->
					<div>
						<label for="status" class="block text-sm font-medium text-gray-700">Status</label>
						<select
							id="status"
							bind:value={statusFilter}
							onchange={handleFilterChange}
							class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
						>
							<option value="">All Statuses</option>
							{#each Object.values(LeadStatus) as status}
								<option value={status}>{safeFormat(status)}</option>
							{/each}
						</select>
					</div>

					<!-- Source Filter -->
					<div>
						<label for="source" class="block text-sm font-medium text-gray-700">Source</label>
						<select
							id="source"
							bind:value={sourceFilter}
							onchange={handleFilterChange}
							class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
						>
							<option value="">All Sources</option>
							{#each Object.values(LeadSource) as source}
								<option value={source}>{safeFormat(source)}</option>
							{/each}
						</select>
					</div>

					<!-- Clear Filters -->
					<div class="flex items-end">
						<button
							type="button"
							onclick={clearFilters}
							class="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
						>
							Clear Filters
						</button>
					</div>
				</div>
			</div>
		</div>

		<!-- Leads Table -->
		<div class="bg-white shadow overflow-hidden sm:rounded-md">
			{#if $leadsLoading.list}
				<div class="py-12 text-center">
					<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
					<p class="mt-2 text-sm text-gray-500">Loading leads...</p>
				</div>
			{:else if $leads.length === 0}
				<div class="py-12 text-center">
					<svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
					</svg>
					<h3 class="mt-2 text-sm font-medium text-gray-900">No leads found</h3>
					<p class="mt-1 text-sm text-gray-500">
						{searchTerm || statusFilter || sourceFilter 
							? 'Try adjusting your filters or search term.'
							: 'Get started by creating your first lead.'}
					</p>
					{#if !searchTerm && !statusFilter && !sourceFilter}
						<div class="mt-6">
							<button
								type="button"
								onclick={createNewLead}
								class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
							>
								<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
								</svg>
								Add Your First Lead
							</button>
						</div>
					{/if}
				</div>
			{:else}
				<!-- Table -->
				<div class="overflow-x-auto">
					<table class="min-w-full divide-y divide-gray-200">
						<thead class="bg-gray-50">
							<tr>
								<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Name & Contact
								</th>
								<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Company
								</th>
								<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Status
								</th>
								<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Source
								</th>
								<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Score
								</th>
								<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Temperature
								</th>
								<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Created
								</th>
								<th scope="col" class="relative px-6 py-3">
									<span class="sr-only">Actions</span>
								</th>
							</tr>
						</thead>
						<tbody class="bg-white divide-y divide-gray-200">
							{#each $leads as lead (lead.id)}
								<tr class="hover:bg-gray-50 cursor-pointer" onclick={() => viewLead(lead.id)}>
									<td class="px-6 py-4 whitespace-nowrap">
										<div class="flex items-center">
											<div class="flex-shrink-0 h-10 w-10">
												<div class="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
													<span class="text-sm font-medium text-gray-700">
														{lead.first_name?.[0]}{lead.last_name?.[0]}
													</span>
												</div>
											</div>
											<div class="ml-4">
												<div class="text-sm font-medium text-gray-900">
													{lead.first_name} {lead.last_name}
												</div>
												<div class="text-sm text-gray-500">{lead.email}</div>
											</div>
										</div>
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<div class="text-sm text-gray-900">{lead.company || '-'}</div>
										<div class="text-sm text-gray-500">{lead.job_title || '-'}</div>
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getStatusColor(lead.status)}">
											{safeFormat(lead.status)}
										</span>
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
										{safeFormat(lead.source)}
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<div class="flex items-center">
											<div class="text-sm font-medium text-gray-900">{lead.score}/100</div>
											<div class="ml-2 w-16 bg-gray-200 rounded-full h-2">
												<div 
													class="bg-indigo-600 h-2 rounded-full" 
													style="width: {lead.score}%"
												></div>
											</div>
										</div>
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getTemperatureColor(lead.lead_temperature)}">
											{(lead.lead_temperature || 'cold').toUpperCase()}
										</span>
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
										{formatDate(lead.created_at)}
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
										<button
											type="button"
											onclick={(e) => { e.stopPropagation(); deleteLead(lead); }}
											class="text-red-600 hover:text-red-900"
										>
											Delete
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				<!-- Pagination -->
				{#if $leadsPagination.pages > 1}
					<div class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
						<div class="flex-1 flex justify-between sm:hidden">
							<button
								onclick={() => goToPage(currentPage - 1)}
								disabled={currentPage === 1}
								class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
							>
								Previous
							</button>
							<button
								onclick={() => goToPage(currentPage + 1)}
								disabled={currentPage === $leadsPagination.pages}
								class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
							>
								Next
							</button>
						</div>
						<div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
							<div>
								<p class="text-sm text-gray-700">
									Showing <span class="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span>
									to <span class="font-medium">{Math.min(currentPage * itemsPerPage, $leadsPagination.total)}</span>
									of <span class="font-medium">{$leadsPagination.total}</span> results
								</p>
							</div>
							<div>
								<nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
									<button
										onclick={() => goToPage(currentPage - 1)}
										disabled={currentPage === 1}
										class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
									>
										<span class="sr-only">Previous</span>
										<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
											<path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
										</svg>
									</button>

									{#each Array.from({length: Math.min(5, $leadsPagination.pages)}, (_, i) => {
										const start = Math.max(1, Math.min(currentPage - 2, $leadsPagination.pages - 4));
										return start + i;
									}) as page}
										<button
											onclick={() => goToPage(page)}
											class="relative inline-flex items-center px-4 py-2 border text-sm font-medium {page === currentPage 
												? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600' 
												: 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'}"
										>
											{page}
										</button>
									{/each}

									<button
										onclick={() => goToPage(currentPage + 1)}
										disabled={currentPage === $leadsPagination.pages}
										class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
									>
										<span class="sr-only">Next</span>
										<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
											<path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
										</svg>
									</button>
								</nav>
							</div>
						</div>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div> 