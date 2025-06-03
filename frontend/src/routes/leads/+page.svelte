<script lang="ts">
	import { onMount } from 'svelte';
	import { Layout, Card, Button, Input } from '$lib/components';
	import { auth, leads, type User, type Lead } from '$lib/stores';
	import { api } from '$lib/api';
	import { goto } from '$app/navigation';
	import toast from 'svelte-french-toast';
	
	let user: User | null = null;
	let isLoading = true;
	let searchTerm = '';
	let statusFilter = 'all';
	let currentPage = 1;
	const itemsPerPage = 10;
	
	// Subscribe to leads store
	let allLeads: Lead[] = [];
	let filteredLeads: Lead[] = [];
	let totalLeads = 0;
	
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
		auth.init();
		
		const unsubscribe = auth.subscribe(async ($auth) => {
			if (!$auth.isAuthenticated && !$auth.isLoading) {
				goto('/login');
				return;
			}
			
			if ($auth.isAuthenticated && $auth.user) {
				user = $auth.user;
				await loadLeads();
			}
		});
		
		// Subscribe to leads store for reactive updates
		const unsubscribeLeads = leads.subscribe(($leads) => {
			allLeads = $leads.leads;
			totalLeads = $leads.pagination.total;
			filterLeads();
		});
		
		return () => {
			unsubscribe();
			unsubscribeLeads();
		};
	});
	
	async function loadLeads() {
		try {
			isLoading = true;
			const response = await api.leads.list({ 
				limit: 100,
				search: searchTerm || undefined,
				status: statusFilter !== 'all' ? statusFilter : undefined
			});
			leads.setLeads(response.leads, response.total);
		} catch (error) {
			console.error('Failed to load leads:', error);
			toast.error('Failed to load leads');
		} finally {
			isLoading = false;
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
			await api.leads.delete(leadId);
			await loadLeads(); // Reload the list
			toast.success('Lead deleted successfully');
		} catch (error) {
			console.error('Failed to delete lead:', error);
			toast.error('Failed to delete lead');
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

<Layout {user} title="Leads">
	<div class="mb-6">
		<div class="flex items-center justify-between">
			<h2 class="text-2xl font-bold text-gray-900">Leads</h2>
			<Button variant="primary" href="/leads/new">
				Add New Lead
			</Button>
		</div>
		<p class="mt-1 text-gray-600">
			Manage your lead database and track sales progress.
		</p>
	</div>
	
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
	
	{#if isLoading}
		<div class="flex items-center justify-center h-64">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
		</div>
	{:else if filteredLeads.length === 0}
		<Card padding="large">
			<div class="text-center">
				<h3 class="text-lg font-medium text-gray-900 mb-2">No leads found</h3>
				<p class="text-gray-600 mb-6">
					{#if searchTerm || statusFilter !== 'all'}
						Try adjusting your search criteria or clearing filters.
					{:else}
						Get started by adding your first lead to the database.
					{/if}
				</p>
				{#if !searchTerm && statusFilter === 'all'}
					<Button variant="primary" href="/leads/new">
						Add Your First Lead
					</Button>
				{/if}
			</div>
		</Card>
	{:else}
		<!-- Results Count -->
		<div class="mb-4">
			<p class="text-sm text-gray-700">
				Showing {paginatedLeads.length} of {filteredLeads.length} leads
				{#if totalLeads !== filteredLeads.length}
					(filtered from {totalLeads} total)
				{/if}
			</p>
		</div>
		
		<!-- Leads Table -->
		<Card>
			<div class="overflow-x-auto">
				<table class="min-w-full divide-y divide-gray-200">
					<thead class="bg-gray-50">
						<tr>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								Lead
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								Company
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								Status
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								Created
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								Actions
							</th>
						</tr>
					</thead>
					<tbody class="bg-white divide-y divide-gray-200">
						{#each paginatedLeads as lead}
							<tr class="hover:bg-gray-50">
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<div class="flex-shrink-0 h-10 w-10">
											<div class="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
												<span class="text-sm font-medium text-gray-700">
													{lead.first_name.charAt(0).toUpperCase()}{lead.last_name.charAt(0).toUpperCase()}
												</span>
											</div>
										</div>
										<div class="ml-4">
											<div class="text-sm font-medium text-gray-900">{getFullName(lead)}</div>
											<div class="text-sm text-gray-500">{lead.email}</div>
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm text-gray-900">{lead.company || 'N/A'}</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getStatusColor(lead.status)}">
										{statusOptions.find(opt => opt.value === lead.status)?.label || lead.status}
									</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
									{formatDate(lead.created_at)}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
									<div class="flex space-x-2">
										<a href="/leads/{lead.id}" class="text-blue-600 hover:text-blue-900">
											View
										</a>
										<a href="/leads/{lead.id}/edit" class="text-indigo-600 hover:text-indigo-900">
											Edit
										</a>
										<button
											on:click={() => deleteLead(lead.id)}
											class="text-red-600 hover:text-red-900"
										>
											Delete
										</button>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</Card>
		
		<!-- Pagination -->
		{#if totalPages > 1}
			<div class="mt-6 flex items-center justify-between">
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
							Showing page <span class="font-medium">{currentPage}</span> of <span class="font-medium">{totalPages}</span>
						</p>
					</div>
					<div>
						<nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
							<Button
								variant="outline"
								disabled={currentPage === 1}
								on:click={() => goToPage(currentPage - 1)}
								class="rounded-r-none"
							>
								Previous
							</Button>
							{#each Array(totalPages) as _, i}
								{#if i + 1 === currentPage}
									<button
										class="bg-blue-50 border-blue-500 text-blue-600 relative inline-flex items-center px-4 py-2 border text-sm font-medium"
									>
										{i + 1}
									</button>
								{:else if i + 1 === 1 || i + 1 === totalPages || Math.abs(i + 1 - currentPage) <= 1}
									<button
										on:click={() => goToPage(i + 1)}
										class="bg-white border-gray-300 text-gray-500 hover:bg-gray-50 relative inline-flex items-center px-4 py-2 border text-sm font-medium"
									>
										{i + 1}
									</button>
								{:else if i + 1 === 2 && currentPage > 4}
									<span class="bg-white border-gray-300 text-gray-500 relative inline-flex items-center px-4 py-2 border text-sm font-medium">
										...
									</span>
								{:else if i + 1 === totalPages - 1 && currentPage < totalPages - 3}
									<span class="bg-white border-gray-300 text-gray-500 relative inline-flex items-center px-4 py-2 border text-sm font-medium">
										...
									</span>
								{/if}
							{/each}
							<Button
								variant="outline"
								disabled={currentPage === totalPages}
								on:click={() => goToPage(currentPage + 1)}
								class="rounded-l-none"
							>
								Next
							</Button>
						</nav>
					</div>
				</div>
			</div>
		{/if}
	{/if}
</Layout> 