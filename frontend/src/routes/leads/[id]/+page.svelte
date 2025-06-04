<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Layout, Card, Button } from '$lib/components';
	import SignedIn from 'clerk-sveltekit/client/SignedIn.svelte';
	import SignedOut from 'clerk-sveltekit/client/SignedOut.svelte';
	import ClerkLoading from 'clerk-sveltekit/client/ClerkLoading.svelte';
	import ClerkLoaded from 'clerk-sveltekit/client/ClerkLoaded.svelte';
	import { leads, type Lead } from '$lib/stores';
	import { api } from '$lib/api';
	import toast from 'svelte-french-toast';
	
	let lead: Lead | null = null;
	let isLoading = true;
	let leadId: string;
	
	// Status color mapping
	const statusColors: Record<string, string> = {
		'new': 'bg-blue-100 text-blue-800',
		'contacted': 'bg-yellow-100 text-yellow-800',
		'qualified': 'bg-green-100 text-green-800',
		'proposal': 'bg-purple-100 text-purple-800',
		'negotiation': 'bg-orange-100 text-orange-800',
		'closed_won': 'bg-emerald-100 text-emerald-800',
		'closed_lost': 'bg-red-100 text-red-800'
	};
	
	// Status labels
	const statusLabels: Record<string, string> = {
		'new': 'New',
		'contacted': 'Contacted',
		'qualified': 'Qualified',
		'proposal': 'Proposal',
		'negotiation': 'Negotiation',
		'closed_won': 'Closed Won',
		'closed_lost': 'Closed Lost'
	};
	
	onMount(() => {
		leadId = $page.params.id;
		loadLead();
	});
	
	async function loadLead() {
		try {
			isLoading = true;
			lead = await api.leads.get(leadId);
		} catch (error) {
			console.error('Failed to load lead:', error);
			if (error instanceof Error) {
				toast.error(error.message);
			} else {
				toast.error('Failed to load lead details');
			}
			goto('/leads');
		} finally {
			isLoading = false;
		}
	}
	
	async function deleteLead() {
		if (!lead || !confirm('Are you sure you want to delete this lead? This action cannot be undone.')) {
			return;
		}
		
		try {
			await leads.deleteLead(lead.id);
			goto('/leads');
		} catch (error) {
			console.error('Failed to delete lead:', error);
			// Error handling is done in the store with toast
		}
	}
	
	function formatDate(dateString: string) {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
	
	function getFullName(lead: Lead) {
		return `${lead.first_name} ${lead.last_name}`.trim();
	}
	
	function getStatusColor(status: string) {
		return statusColors[status] || 'bg-gray-100 text-gray-800';
	}
	
	function getStatusLabel(status: string) {
		return statusLabels[status] || status;
	}
</script>

<svelte:head>
	<title>{lead ? `${getFullName(lead)} - Lead Details` : 'Lead Details'} - LMA Platform</title>
</svelte:head>

<ClerkLoading>
	<div class="flex items-center justify-center h-64">
		<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
	</div>
</ClerkLoading>

<ClerkLoaded>
	<SignedIn>
		<Layout title="Lead Details">
			{#if isLoading}
				<div class="flex items-center justify-center h-64">
					<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
				</div>
			{:else if lead}
				<!-- Header -->
				<div class="mb-6">
					<div class="flex items-center justify-between">
						<div class="flex items-center space-x-4">
							<Button variant="outline" href="/leads">
								← Back to Leads
							</Button>
							<div>
								<h1 class="text-2xl font-bold text-gray-900">{getFullName(lead)}</h1>
								<p class="text-gray-600">{lead.email}</p>
							</div>
						</div>
						<div class="flex items-center space-x-3">
							<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getStatusColor(lead.status)}">
								{getStatusLabel(lead.status)}
							</span>
							<Button variant="primary" href="/leads/{lead.id}/edit">
								Edit Lead
							</Button>
							<Button variant="danger" on:click={deleteLead}>
								Delete
							</Button>
						</div>
					</div>
				</div>
				
				<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
					<!-- Main Information -->
					<div class="lg:col-span-2 space-y-6">
						<!-- Contact Information -->
						<Card>
							<div class="px-6 py-4 border-b border-gray-200">
								<h3 class="text-lg font-medium text-gray-900">Contact Information</h3>
							</div>
							<div class="px-6 py-4">
								<dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
									<div>
										<dt class="text-sm font-medium text-gray-500">Full Name</dt>
										<dd class="mt-1 text-sm text-gray-900">{getFullName(lead)}</dd>
									</div>
									<div>
										<dt class="text-sm font-medium text-gray-500">Email</dt>
										<dd class="mt-1 text-sm text-gray-900">
											<a href="mailto:{lead.email}" class="text-blue-600 hover:text-blue-800">
												{lead.email}
											</a>
										</dd>
									</div>
									{#if lead.phone}
										<div>
											<dt class="text-sm font-medium text-gray-500">Phone</dt>
											<dd class="mt-1 text-sm text-gray-900">
												<a href="tel:{lead.phone}" class="text-blue-600 hover:text-blue-800">
													{lead.phone}
												</a>
											</dd>
										</div>
									{/if}
									{#if lead.company}
										<div>
											<dt class="text-sm font-medium text-gray-500">Company</dt>
											<dd class="mt-1 text-sm text-gray-900">{lead.company}</dd>
										</div>
									{/if}
									{#if lead.position}
										<div>
											<dt class="text-sm font-medium text-gray-500">Position</dt>
											<dd class="mt-1 text-sm text-gray-900">{lead.position}</dd>
										</div>
									{/if}
									{#if lead.linkedin_url}
										<div>
											<dt class="text-sm font-medium text-gray-500">LinkedIn</dt>
											<dd class="mt-1 text-sm text-gray-900">
												<a href="{lead.linkedin_url}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800">
													{lead.linkedin_url}
												</a>
											</dd>
										</div>
									{/if}
								</dl>
							</div>
						</Card>
						
						<!-- Lead Details -->
						<Card>
							<div class="px-6 py-4 border-b border-gray-200">
								<h3 class="text-lg font-medium text-gray-900">Lead Details</h3>
							</div>
							<div class="px-6 py-4">
								<dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
									<div>
										<dt class="text-sm font-medium text-gray-500">Status</dt>
										<dd class="mt-1">
											<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getStatusColor(lead.status)}">
												{getStatusLabel(lead.status)}
											</span>
										</dd>
									</div>
									{#if lead.source}
										<div>
											<dt class="text-sm font-medium text-gray-500">Source</dt>
											<dd class="mt-1 text-sm text-gray-900 capitalize">{lead.source}</dd>
										</div>
									{/if}
									{#if lead.score !== undefined}
										<div>
											<dt class="text-sm font-medium text-gray-500">Lead Score</dt>
											<dd class="mt-1 text-sm text-gray-900">{lead.score}/100</dd>
										</div>
									{/if}
									{#if lead.lead_temperature}
										<div>
											<dt class="text-sm font-medium text-gray-500">Temperature</dt>
											<dd class="mt-1 text-sm text-gray-900 capitalize">{lead.lead_temperature}</dd>
										</div>
									{/if}
									<div>
										<dt class="text-sm font-medium text-gray-500">Created</dt>
										<dd class="mt-1 text-sm text-gray-900">{formatDate(lead.created_at)}</dd>
									</div>
									<div>
										<dt class="text-sm font-medium text-gray-500">Last Updated</dt>
										<dd class="mt-1 text-sm text-gray-900">{formatDate(lead.updated_at)}</dd>
									</div>
								</dl>
							</div>
						</Card>
						
						<!-- Notes -->
						{#if lead.notes}
							<Card>
								<div class="px-6 py-4 border-b border-gray-200">
									<h3 class="text-lg font-medium text-gray-900">Notes</h3>
								</div>
								<div class="px-6 py-4">
									<p class="text-sm text-gray-900 whitespace-pre-wrap">{lead.notes}</p>
								</div>
							</Card>
						{/if}
					</div>
					
					<!-- Sidebar -->
					<div class="space-y-6">
						<!-- Quick Actions -->
						<Card>
							<div class="px-6 py-4 border-b border-gray-200">
								<h3 class="text-lg font-medium text-gray-900">Quick Actions</h3>
							</div>
							<div class="px-6 py-4 space-y-3">
								<Button variant="outline" class="w-full" href="mailto:{lead.email}">
									Send Email
								</Button>
								{#if lead.phone}
									<Button variant="outline" class="w-full" href="tel:{lead.phone}">
										Call Lead
									</Button>
								{/if}
								<Button variant="outline" class="w-full" href="/leads/{lead.id}/edit">
									Edit Details
								</Button>
								<Button variant="outline" class="w-full">
									Add Note
								</Button>
								<Button variant="outline" class="w-full">
									Schedule Follow-up
								</Button>
							</div>
						</Card>
						
						<!-- Lead Statistics -->
						<Card>
							<div class="px-6 py-4 border-b border-gray-200">
								<h3 class="text-lg font-medium text-gray-900">Statistics</h3>
							</div>
							<div class="px-6 py-4 space-y-4">
								<div class="flex justify-between items-center">
									<span class="text-sm text-gray-500">Days in Pipeline</span>
									<span class="text-sm font-medium text-gray-900">
										{Math.floor((new Date().getTime() - new Date(lead.created_at).getTime()) / (1000 * 60 * 60 * 24))}
									</span>
								</div>
								{#if lead.score !== undefined}
									<div class="flex justify-between items-center">
										<span class="text-sm text-gray-500">Lead Score</span>
										<span class="text-sm font-medium text-gray-900">{lead.score}/100</span>
									</div>
								{/if}
								<div class="flex justify-between items-center">
									<span class="text-sm text-gray-500">Last Activity</span>
									<span class="text-sm font-medium text-gray-900">
										{formatDate(lead.updated_at)}
									</span>
								</div>
							</div>
						</Card>
					</div>
				</div>
			{:else}
				<Card padding="large">
					<div class="text-center">
						<h3 class="text-lg font-medium text-gray-900 mb-2">Lead not found</h3>
						<p class="text-gray-600 mb-6">
							The lead you're looking for doesn't exist or you don't have permission to view it.
						</p>
						<Button variant="primary" href="/leads">
							Back to Leads
						</Button>
					</div>
				</Card>
			{/if}
		</Layout>
	</SignedIn>
	
	<SignedOut>
		<Layout title="Access Denied">
			<Card padding="large">
				<div class="text-center">
					<h3 class="text-lg font-medium text-gray-900 mb-2">Authentication Required</h3>
					<p class="text-gray-600 mb-6">
						You need to be signed in to access this page.
					</p>
					<Button variant="primary" href="/sign-in">
						Sign In
					</Button>
				</div>
			</Card>
		</Layout>
	</SignedOut>
</ClerkLoaded> 