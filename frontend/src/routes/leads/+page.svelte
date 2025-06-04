<script lang="ts">
	import { onMount } from 'svelte';
	import { Layout, Card, Button, Input } from '$lib/components';
	import SignedIn from 'clerk-sveltekit/client/SignedIn.svelte';
	import SignedOut from 'clerk-sveltekit/client/SignedOut.svelte';
	import ClerkLoading from 'clerk-sveltekit/client/ClerkLoading.svelte';
	import ClerkLoaded from 'clerk-sveltekit/client/ClerkLoaded.svelte';
	import { leads, leadStats, type Lead } from '$lib/stores';
	import { goto } from '$app/navigation';
	import toast from 'svelte-french-toast';
	
	let searchTerm = '';
	let statusFilter = 'all';
	let currentPage = 1;
	const itemsPerPage = 10;
	
	// Subscribe to leads store
	let allLeads: Lead[] = [];
	let filteredLeads: Lead[] = [];
	let totalLeads = 0;
	let isLoading = false;
	let error: string | null = null;
	let operationStates = {
		creating: false,
		updating: {} as Record<string, boolean>,
		deleting: {} as Record<string, boolean>
	};
	
	// Available status options
	const statusOptions = [
		{ value: 'all', label: 'All Statuses' },
		{ value: 'new', label: 'New' },
		{ value: 'contacted', label: 'Contacted' },
		{ value: 'qualified', label: 'Qualified' },
		{ value: 'proposal', label: 'Proposal' },
		{ value: 'negotiation', label: 'Negotiation' },
		{ value: 'closed_won', label: 'Closed Won' },
		{ value: 'closed_lost', label: 'Closed Lost' }
	];
	
	onMount(() => {
		// Subscribe to leads store for reactive updates
		const unsubscribeLeads = leads.subscribe(($leads) => {
			allLeads = $leads.leads;
			totalLeads = $leads.pagination.total;
			isLoading = $leads.isLoading;
			error = $leads.error;
			operationStates = $leads.operations;
			filterLeads();
		});
		
		// Initial load
		loadLeads();
		
		return () => {
			unsubscribeLeads();
		};
	});
	
	async function loadLeads() {
		try {
			await leads.loadLeads({ 
				limit: 100,
				search: searchTerm || undefined,
				status_filter: statusFilter !== 'all' ? statusFilter : undefined
			});
		} catch (error) {
			// Error handling is done in the store
			console.error('Failed to load leads:', error);
		}
	}
	
	function filterLeads() {
		let filtered = allLeads;
		
		// Apply search filter
		if (searchTerm) {
			const term = searchTerm.toLowerCase();
			filtered = filtered.filter(lead => 
				lead.first_name.toLowerCase().includes(term) ||
				lead.last_name.toLowerCase().includes(term) ||
				lead.email.toLowerCase().includes(term) ||
				lead.company?.toLowerCase().includes(term)
			);
		}
		
		// Apply status filter
		if (statusFilter !== 'all') {
			filtered = filtered.filter(lead => lead.status === statusFilter);
		}
		
		filteredLeads = filtered;
		currentPage = 1; // Reset to first page when filtering
	}
	
	function handleSearch() {
		filterLeads();
	}
	
	function handleStatusChange() {
		filterLeads();
	}
	
	async function deleteLead(leadId: string) {
		if (!confirm('Are you sure you want to delete this lead?')) {
			return;
		}
		
		try {
			await leads.deleteLead(leadId);
		} catch (error) {
			// Error handling is done in the store with toast
			console.error('Failed to delete lead:', error);
		}
	}
	
	function getStatusColor(status: string) {
		switch (status) {
			case 'new': return 'bg-blue-100 text-blue-800';
			case 'contacted': return 'bg-yellow-100 text-yellow-800';
			case 'qualified': return 'bg-green-100 text-green-800';
			case 'proposal': return 'bg-purple-100 text-purple-800';
			case 'negotiation': return 'bg-orange-100 text-orange-800';
			case 'closed_won': return 'bg-emerald-100 text-emerald-800';
			case 'closed_lost': return 'bg-red-100 text-red-800';
			default: return 'bg-gray-100 text-gray-800';
		}
	}
	
	function formatDate(dateString: string) {
		return new Date(dateString).toLocaleDateString();
	}
	
	function getFullName(lead: Lead) {
		return `${lead.first_name} ${lead.last_name}`.trim();
	}
	
	// Pagination
	$: totalPages = Math.ceil(filteredLeads.length / itemsPerPage);
	$: startIndex = (currentPage - 1) * itemsPerPage;
	$: endIndex = startIndex + itemsPerPage;
	$: paginatedLeads = filteredLeads.slice(startIndex, endIndex);
	
	function goToPage(page: number) {
		currentPage = page;
	}
</script>

<svelte:head>
	<title>Leads - LMA Platform</title>
</svelte:head>

<ClerkLoading>
	<div class="flex items-center justify-center h-64">
		<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
	</div>
</ClerkLoading>

<ClerkLoaded>
	<SignedIn>
		<Layout title="Leads">
			<div class="mb-6">
				<div class="flex items-center justify-between">
					<h2 class="text-2xl font-bold text-gray-900">Leads</h2>
					<Button variant="primary" href="/leads/new" disabled={operationStates.creating}>
						{#if operationStates.creating}
							<span class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></span>
						{/if}
						Add New Lead
					</Button>
				</div>
				<p class="mt-1 text-gray-600">
					Manage your lead database and track sales progress.
				</p>
			</div>
			
			<!-- Error Message -->
			{#if error}
				<div class="mb-6">
					<Card padding="medium">
						<div class="flex items-center p-4 text-red-800 bg-red-50 rounded-lg">
							<svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
							</svg>
							<span class="font-medium">{error}</span>
							<button on:click={() => leads.setError(null)} class="ml-auto text-red-600 hover:text-red-800">
								<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
								</svg>
							</button>
						</div>
					</Card>
				</div>
			{/if}
			
			<!-- Filters -->
			<div class="mb-6">
				<Card padding="medium">
					<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
						<div>
							<label for="search" class="block text-sm font-medium text-gray-700 mb-1">
								Search Leads
							</label>
							<Input
								id="search"
								type="text"
								placeholder="Search by name, email, or company..."
								bind:value={searchTerm}
								on:input={handleSearch}
							/>
						</div>
						
						<div>
							<label for="status-filter" class="block text-sm font-medium text-gray-700 mb-1">
								Filter by Status
							</label>
							<select
								id="status-filter"
								bind:value={statusFilter}
								on:change={handleStatusChange}
								class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
							>
								{#each statusOptions as option}
									<option value={option.value}>{option.label}</option>
								{/each}
							</select>
						</div>
						
						<div class="flex items-end">
							<Button variant="outline" on:click={loadLeads} disabled={isLoading}>
								{#if isLoading}
									<span class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></span>
								{/if}
								Refresh
							</Button>
						</div>
					</div>
				</Card>
			</div>
			
			{#if isLoading && allLeads.length === 0}
				<div class="flex items-center justify-center h-64">
					<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
				</div>
			{:else if allLeads.length === 0}
				<!-- Empty state -->
				<Card padding="large">
					<div class="text-center">
						<svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
							<path d="M34 40h10v-4a6 6 0 00-10.712-3.714M34 40H14m20 0v-4a9.971 9.971 0 00-.712-3.714M14 40H4v-4a6 6 0 0110.713-3.714M14 40v-4c0-1.313.253-2.566.713-3.714m0 0A10.003 10.003 0 0124 26c4.21 0 7.813 2.602 9.288 6.286M30 14a6 6 0 11-12 0 6 6 0 0112 0zm12 6a4 4 0 11-8 0 4 4 0 018 0zm-28 0a4 4 0 11-8 0 4 4 0 018 0z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
						</svg>
						<h3 class="mt-2 text-sm font-medium text-gray-900">No leads yet</h3>
						<p class="mt-1 text-sm text-gray-500">
							Get started by creating your first lead.
						</p>
						<div class="mt-6">
							<Button variant="primary" href="/leads/new">
								Add New Lead
							</Button>
						</div>
					</div>
				</Card>
			{:else}
				<!-- Leads table -->
				<Card>
					<div class="overflow-hidden">
						<div class="overflow-x-auto">
							<table class="min-w-full divide-y divide-gray-200">
								<thead class="bg-gray-50">
									<tr>
										<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
											Lead
										</th>
										<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
											Contact
										</th>
										<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
											Status
										</th>
										<th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
											Score
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
									{#each paginatedLeads as lead (lead.id)}
										<tr class="hover:bg-gray-50 {operationStates.deleting[lead.id] ? 'opacity-50' : ''}">
											<td class="px-6 py-4 whitespace-nowrap">
												<div class="flex items-center">
													<div class="flex-shrink-0 h-10 w-10">
														<div class="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
															<span class="text-sm font-medium text-gray-700">
																{lead.first_name.charAt(0)}{lead.last_name.charAt(0)}
															</span>
														</div>
													</div>
													<div class="ml-4">
														<div class="text-sm font-medium text-gray-900">
															{getFullName(lead)}
														</div>
														{#if lead.company}
															<div class="text-sm text-gray-500">
																{lead.company}
															</div>
														{/if}
													</div>
												</div>
											</td>
											<td class="px-6 py-4 whitespace-nowrap">
												<div class="text-sm text-gray-900">{lead.email}</div>
												{#if lead.phone}
													<div class="text-sm text-gray-500">{lead.phone}</div>
												{/if}
											</td>
											<td class="px-6 py-4 whitespace-nowrap">
												<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getStatusColor(lead.status)}">
													{lead.status.replace('_', ' ')}
												</span>
											</td>
											<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
												{lead.score}
											</td>
											<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
												{formatDate(lead.created_at)}
											</td>
											<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
												<div class="flex justify-end space-x-2">
													<Button variant="ghost" size="small" href="/leads/{lead.id}">
														View
													</Button>
													<Button 
														variant="ghost" 
														size="small" 
														href="/leads/{lead.id}/edit"
														disabled={operationStates.updating[lead.id]}
													>
														{#if operationStates.updating[lead.id]}
															<span class="animate-spin rounded-full h-3 w-3 border-b-2 border-current mr-1"></span>
														{/if}
														Edit
													</Button>
													<Button 
														variant="ghost" 
														size="small" 
														on:click={() => deleteLead(lead.id)}
														disabled={operationStates.deleting[lead.id]}
													>
														{#if operationStates.deleting[lead.id]}
															<span class="animate-spin rounded-full h-3 w-3 border-b-2 border-current mr-1"></span>
														{/if}
														Delete
													</Button>
												</div>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
					
					<!-- Pagination -->
					{#if totalPages > 1}
						<div class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
							<div class="flex-1 flex justify-between sm:hidden">
								<Button 
									variant="outline" 
									disabled={currentPage === 1}
									on:click={() => goToPage(currentPage - 1)}
								>
									Previous
								</Button>
								<Button 
									variant="outline" 
									disabled={currentPage === totalPages}
									on:click={() => goToPage(currentPage + 1)}
								>
									Next
								</Button>
							</div>
							<div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
								<div>
									<p class="text-sm text-gray-700">
										Showing
										<span class="font-medium">{startIndex + 1}</span>
										to
										<span class="font-medium">{Math.min(endIndex, filteredLeads.length)}</span>
										of
										<span class="font-medium">{filteredLeads.length}</span>
										results
									</p>
								</div>
								<div>
									<nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
										<button
											class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
											disabled={currentPage === 1}
											on:click={() => goToPage(currentPage - 1)}
										>
											Previous
										</button>
										
										{#each Array.from({ length: totalPages }, (_, i) => i + 1) as page}
											{#if page === currentPage}
												<span class="relative inline-flex items-center px-4 py-2 border border-blue-500 bg-blue-50 text-sm font-medium text-blue-600">
													{page}
												</span>
											{:else if page === 1 || page === totalPages || (page >= currentPage - 1 && page <= currentPage + 1)}
												<button
													class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
													on:click={() => goToPage(page)}
												>
													{page}
												</button>
											{:else if page === currentPage - 2 || page === currentPage + 2}
												<span class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
													...
												</span>
											{/if}
										{/each}
										
										<button
											class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
											disabled={currentPage === totalPages}
											on:click={() => goToPage(currentPage + 1)}
										>
											Next
										</button>
									</nav>
								</div>
							</div>
						</div>
					{/if}
				</Card>
			{/if}
		</Layout>
	</SignedIn>
</ClerkLoaded>

<SignedOut>
	<Layout title="Access Denied">
		<Card padding="large">
			<div class="text-center">
				<h3 class="text-lg font-medium text-gray-900 mb-2">Authentication Required</h3>
				<p class="text-gray-600 mb-6">
					You need to be signed in to access the leads page.
				</p>
				<Button variant="primary" href="/sign-in">
					Sign In
				</Button>
			</div>
		</Card>
	</Layout>
</SignedOut> 