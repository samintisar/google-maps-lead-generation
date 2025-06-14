<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { leadsStore, currentLead, leadsLoading, leadsError } from '$lib/stores/leads';
	import { LeadStatus, LeadSource } from '$lib/types';
	import type { Lead } from '$lib/types';

	// Get lead ID from URL
	$: leadId = parseInt($page.params.id);

	// Local state for editing
	let isEditing = false;
	let editForm: Partial<Lead> = {};

	// Enrichment state
	let isEnriching = false;
	let enrichmentPolling: NodeJS.Timeout | null = null;

	// Load lead on mount
	onMount(() => {
		if (leadId) {
			leadsStore.loadLead(leadId);
		}
	});

	// Cleanup polling on destroy
	onDestroy(() => {
		if (enrichmentPolling) {
			clearInterval(enrichmentPolling);
		}
	});

	// Watch for current lead changes
	$: if ($currentLead && $currentLead.id === leadId) {
		// Reset edit form when lead loads
		editForm = { ...$currentLead };
	}

	// Navigate back to leads list
	function goBack() {
		goto('/dashboard/leads');
	}

	// Start editing mode
	function startEdit() {
		if ($currentLead) {
			editForm = { ...$currentLead };
			isEditing = true;
		}
	}

	// Cancel editing
	function cancelEdit() {
		isEditing = false;
		if ($currentLead) {
			editForm = { ...$currentLead };
		}
	}

	// Save changes
	async function saveChanges() {
		if (!$currentLead) return;

		const updates = Object.fromEntries(
			Object.entries(editForm).filter(([key, value]) => {
				const currentValue = $currentLead[key as keyof Lead];
				return value !== currentValue;
			})
		);

		if (Object.keys(updates).length > 0) {
			const result = await leadsStore.updateLead($currentLead.id, updates);
			if (result) {
				isEditing = false;
			}
		} else {
			isEditing = false;
		}
	}

	// Delete lead
	async function deleteLead() {
		if (!$currentLead) return;

		if (confirm(`Are you sure you want to delete ${$currentLead.name}?`)) {
			const result = await leadsStore.deleteLead($currentLead.id);
			if (result) {
				goto('/dashboard/leads');
			}
		}
	}

	// Update lead status
	async function updateStatus(newStatus: LeadStatus) {
		if (!$currentLead) return;
		await leadsStore.updateLeadStatus($currentLead.id, newStatus);
	}

	// Enrich lead with Perplexity data
	async function enrichLead() {
		if (!$currentLead || isEnriching) return;

		isEnriching = true;
		const response = await leadsStore.enrichLead($currentLead.id);
		
		if (response?.success) {
			// Start polling for completion
			enrichmentPolling = setInterval(async () => {
				const status = await leadsStore.getEnrichmentStatus($currentLead!.id);
				
				if (status?.enrichment_status === 'completed') {
					// Reload lead to get updated data
					await leadsStore.loadLead($currentLead!.id);
					isEnriching = false;
					if (enrichmentPolling) {
						clearInterval(enrichmentPolling);
						enrichmentPolling = null;
					}
				} else if (status?.enrichment_status === 'failed') {
					isEnriching = false;
					if (enrichmentPolling) {
						clearInterval(enrichmentPolling);
						enrichmentPolling = null;
					}
				}
			}, 3000); // Poll every 3 seconds
		} else {
			isEnriching = false;
		}
	}

	// Format date
	function formatDate(dateString: string) {
		return new Date(dateString).toLocaleString();
	}

	// Get status badge color
	function getStatusColor(status: LeadStatus) {
		const colors: Record<LeadStatus, string> = {
			[LeadStatus.NEW]: 'bg-blue-100 text-blue-800',
			[LeadStatus.CONTACTED]: 'bg-yellow-100 text-yellow-800',
			[LeadStatus.QUALIFIED]: 'bg-green-100 text-green-800',
			[LeadStatus.PROPOSAL]: 'bg-purple-100 text-purple-800',
			[LeadStatus.NEGOTIATION]: 'bg-orange-100 text-orange-800',
			[LeadStatus.CLOSED_WON]: 'bg-green-100 text-green-800',
			[LeadStatus.CLOSED_LOST]: 'bg-red-100 text-red-800',
		};
		return colors[status] || 'bg-gray-100 text-gray-800';
	}

	// Get enrichment status color
	function getEnrichmentStatusColor(status?: string) {
		switch (status) {
			case 'completed': return 'bg-green-100 text-green-800';
			case 'pending': return 'bg-yellow-100 text-yellow-800';
			case 'failed': return 'bg-red-100 text-red-800';
			default: return 'bg-gray-100 text-gray-800';
		}
	}

	// Check if lead has enrichment data
	function hasEnrichmentData(lead: Lead): boolean {
		return !!(
			lead.linkedin_profile ||
			lead.twitter_profile ||
			lead.facebook_profile ||
			lead.instagram_profile ||
			lead.ideal_customer_profile ||
			lead.pain_points ||
			lead.key_goals ||
			lead.company_description ||
			lead.recent_news ||
			(lead.key_personnel && lead.key_personnel.length > 0)
		);
	}
</script>

<svelte:head>
	<title>
		{$currentLead ? $currentLead.name : 'Lead Details'} - LMA Platform
	</title>
</svelte:head>

<div class="py-6">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
		<!-- Back button -->
		<div class="mb-6">
			<button
				type="button"
				onclick={goBack}
				class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
			>
				<svg class="-ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
				</svg>
				Back to Leads
			</button>
		</div>

		<!-- Error message -->
		{#if $leadsError}
			<div class="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative">
				<strong class="font-bold">Error:</strong>
				<span class="block sm:inline">{$leadsError}</span>
			</div>
		{/if}

		<!-- Loading state -->
		{#if $leadsLoading.detail}
			<div class="py-12 text-center">
				<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
				<p class="mt-2 text-sm text-gray-500">Loading lead details...</p>
			</div>
		{:else if !$currentLead}
			<div class="py-12 text-center">
				<svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
				</svg>
				<h3 class="mt-2 text-sm font-medium text-gray-900">Lead not found</h3>
				<p class="mt-1 text-sm text-gray-500">The lead you're looking for doesn't exist or has been deleted.</p>
			</div>
		{:else}
			<!-- Page header -->
			<div class="md:flex md:items-center md:justify-between mb-6">
				<div class="flex-1 min-w-0">
					<div class="flex items-center">
						<div class="flex-shrink-0 h-12 w-12">
							<div class="h-12 w-12 rounded-full bg-gray-300 flex items-center justify-center">
								<span class="text-lg font-medium text-gray-700">
								{$currentLead.name?.[0]}
								</span>
							</div>
						</div>
						<div class="ml-4">
							<h1 class="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
							{$currentLead.name}
							</h1>
							<div class="mt-1 flex flex-col sm:mt-0 sm:flex-row sm:flex-wrap sm:space-x-4">
								<div class="mt-2 flex items-center text-sm text-gray-500">
									<svg class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
									</svg>
									{$currentLead.email}
								</div>
								{#if $currentLead.company}
									<div class="mt-2 flex items-center text-sm text-gray-500">
										<svg class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
										</svg>
										{$currentLead.company}
									</div>
								{/if}
							</div>
						</div>
					</div>
				</div>
				<div class="mt-4 flex md:mt-0 md:ml-4 space-x-3">
					<!-- Enrichment button -->
					{#if !isEditing}
						<button
							type="button"
							onclick={enrichLead}
							disabled={isEnriching || $leadsLoading.enrich}
							class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							{#if isEnriching || $leadsLoading.enrich}
								<svg class="-ml-1 mr-2 h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
								</svg>
								Enriching...
							{:else}
								<svg class="-ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
								</svg>
								Enrich Lead
							{/if}
						</button>
					{/if}

					{#if isEditing}
						<button
							type="button"
							onclick={cancelEdit}
							class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
						>
							Cancel
						</button>
						<button
							type="button"
							onclick={saveChanges}
							class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
						>
							Save Changes
						</button>
					{:else}
						<button
							type="button"
							onclick={startEdit}
							class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
						>
							<svg class="-ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
							</svg>
							Edit
						</button>
						<button
							type="button"
							onclick={deleteLead}
							class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
						>
							<svg class="-ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
							</svg>
							Delete
						</button>
					{/if}
				</div>
			</div>

			<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
				<!-- Main content -->
				<div class="lg:col-span-2 space-y-6">
					<!-- Contact Information -->
					<div class="bg-white shadow rounded-lg">
						<div class="px-4 py-5 sm:p-6">
							<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Contact Information</h3>
							
							{#if isEditing}
								<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
									<div>
										<label for="name" class="block text-sm font-medium text-gray-700">Name</label>
										<input
											type="text"
											id="name"
											bind:value={editForm.name}
											class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
										/>
									</div>
									<div>
										<label for="email" class="block text-sm font-medium text-gray-700">Email</label>
										<input
											type="email"
											id="email"
											bind:value={editForm.email}
											class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
										/>
									</div>
									<div>
										<label for="phone" class="block text-sm font-medium text-gray-700">Phone</label>
										<input
											type="tel"
											id="phone"
											bind:value={editForm.phone}
											class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
										/>
									</div>
								</div>
							{:else}
								<dl class="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
									<div>
										<dt class="text-sm font-medium text-gray-500">Email</dt>
										<dd class="mt-1 text-sm text-gray-900">{$currentLead.email}</dd>
									</div>
									{#if $currentLead.phone}
										<div>
											<dt class="text-sm font-medium text-gray-500">Phone</dt>
											<dd class="mt-1 text-sm text-gray-900">{$currentLead.phone}</dd>
										</div>
									{/if}
								</dl>
							{/if}
						</div>
					</div>

					<!-- Company Information -->
					<div class="bg-white shadow rounded-lg">
						<div class="px-4 py-5 sm:p-6">
							<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Company Information</h3>
							
							{#if isEditing}
								<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
									<div>
										<label for="company" class="block text-sm font-medium text-gray-700">Company</label>
										<input
											type="text"
											id="company"
											bind:value={editForm.company}
											class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
										/>
									</div>
									<div>
										<label for="industry" class="block text-sm font-medium text-gray-700">Industry</label>
										<input
											type="text"
											id="industry"
											bind:value={editForm.industry}
											class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
										/>
									</div>
									<div>
										<label for="website" class="block text-sm font-medium text-gray-700">Website</label>
										<input
											type="url"
											id="website"
											bind:value={editForm.website}
											class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
										/>
									</div>
									<div>
										<label for="address" class="block text-sm font-medium text-gray-700">Address</label>
										<input
											type="text"
											id="address"
											bind:value={editForm.address}
											class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
										/>
									</div>
								</div>
							{:else}
								<dl class="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
									<div>
										<dt class="text-sm font-medium text-gray-500">Company</dt>
										<dd class="mt-1 text-sm text-gray-900">{$currentLead.company || '-'}</dd>
									</div>
									{#if $currentLead.industry}
										<div>
											<dt class="text-sm font-medium text-gray-500">Industry</dt>
											<dd class="mt-1 text-sm text-gray-900">{$currentLead.industry}</dd>
										</div>
									{/if}
									{#if $currentLead.website}
										<div>
											<dt class="text-sm font-medium text-gray-500">Website</dt>
											<dd class="mt-1 text-sm text-gray-900">
												<a href={$currentLead.website} target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:text-indigo-500">
													{$currentLead.website}
												</a>
											</dd>
										</div>
									{/if}
									{#if $currentLead.address}
										<div>
											<dt class="text-sm font-medium text-gray-500">Address</dt>
											<dd class="mt-1 text-sm text-gray-900">{$currentLead.address}</dd>
										</div>
									{/if}
								</dl>
							{/if}
						</div>
					</div>

					<!-- Social Media Profiles -->
					{#if hasEnrichmentData($currentLead) || isEditing}
						<div class="bg-white shadow rounded-lg">
							<div class="px-4 py-5 sm:p-6">
								<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Social Media Profiles</h3>
								
								{#if isEditing}
									<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
										<div>
											<label for="linkedin_profile" class="block text-sm font-medium text-gray-700">LinkedIn Profile</label>
											<input
												type="url"
												id="linkedin_profile"
												bind:value={editForm.linkedin_profile}
												class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
											/>
										</div>
										<div>
											<label for="twitter_profile" class="block text-sm font-medium text-gray-700">Twitter Profile</label>
											<input
												type="url"
												id="twitter_profile"
												bind:value={editForm.twitter_profile}
												class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
											/>
										</div>
										<div>
											<label for="facebook_profile" class="block text-sm font-medium text-gray-700">Facebook Profile</label>
											<input
												type="url"
												id="facebook_profile"
												bind:value={editForm.facebook_profile}
												class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
											/>
										</div>
										<div>
											<label for="instagram_profile" class="block text-sm font-medium text-gray-700">Instagram Profile</label>
											<input
												type="url"
												id="instagram_profile"
												bind:value={editForm.instagram_profile}
												class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
											/>
										</div>
									</div>
								{:else}
									<dl class="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
										{#if $currentLead.linkedin_profile}
											<div>
												<dt class="text-sm font-medium text-gray-500">LinkedIn</dt>
												<dd class="mt-1 text-sm text-gray-900">
													<a href={$currentLead.linkedin_profile} target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:text-indigo-500">
														View Profile
													</a>
												</dd>
											</div>
										{/if}
										{#if $currentLead.twitter_profile}
											<div>
												<dt class="text-sm font-medium text-gray-500">Twitter</dt>
												<dd class="mt-1 text-sm text-gray-900">
													<a href={$currentLead.twitter_profile} target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:text-indigo-500">
														View Profile
													</a>
												</dd>
											</div>
										{/if}
										{#if $currentLead.facebook_profile}
											<div>
												<dt class="text-sm font-medium text-gray-500">Facebook</dt>
												<dd class="mt-1 text-sm text-gray-900">
													<a href={$currentLead.facebook_profile} target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:text-indigo-500">
														View Profile
													</a>
												</dd>
											</div>
										{/if}
										{#if $currentLead.instagram_profile}
											<div>
												<dt class="text-sm font-medium text-gray-500">Instagram</dt>
												<dd class="mt-1 text-sm text-gray-900">
													<a href={$currentLead.instagram_profile} target="_blank" rel="noopener noreferrer" class="text-indigo-600 hover:text-indigo-500">
														View Profile
													</a>
												</dd>
											</div>
										{/if}
									</dl>
								{/if}
							</div>
						</div>
					{/if}

					<!-- Business Intelligence -->
					{#if hasEnrichmentData($currentLead) || isEditing}
						<div class="bg-white shadow rounded-lg">
							<div class="px-4 py-5 sm:p-6">
								<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Business Intelligence</h3>
								
								{#if isEditing}
									<div class="space-y-4">
										<div>
											<label for="ideal_customer_profile" class="block text-sm font-medium text-gray-700">Ideal Customer Profile</label>
											<textarea
												id="ideal_customer_profile"
												bind:value={editForm.ideal_customer_profile}
												rows="3"
												class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
											></textarea>
										</div>
										<div>
											<label for="pain_points" class="block text-sm font-medium text-gray-700">Pain Points</label>
											<textarea
												id="pain_points"
												bind:value={editForm.pain_points}
												rows="3"
												class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
											></textarea>
										</div>
										<div>
											<label for="key_goals" class="block text-sm font-medium text-gray-700">Key Goals</label>
											<textarea
												id="key_goals"
												bind:value={editForm.key_goals}
												rows="3"
												class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
											></textarea>
										</div>
										<div>
											<label for="company_description" class="block text-sm font-medium text-gray-700">Company Description</label>
											<textarea
												id="company_description"
												bind:value={editForm.company_description}
												rows="4"
												class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
											></textarea>
										</div>
										<div>
											<label for="recent_news" class="block text-sm font-medium text-gray-700">Recent News</label>
											<textarea
												id="recent_news"
												bind:value={editForm.recent_news}
												rows="3"
												class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
											></textarea>
										</div>
									</div>
								{:else}
									<div class="space-y-6">
										{#if $currentLead.ideal_customer_profile}
											<div>
												<dt class="text-sm font-medium text-gray-500 mb-2">Ideal Customer Profile</dt>
												<dd class="text-sm text-gray-900 whitespace-pre-wrap">{$currentLead.ideal_customer_profile}</dd>
											</div>
										{/if}
										{#if $currentLead.pain_points}
											<div>
												<dt class="text-sm font-medium text-gray-500 mb-2">Pain Points</dt>
												<dd class="text-sm text-gray-900 whitespace-pre-wrap">{$currentLead.pain_points}</dd>
											</div>
										{/if}
										{#if $currentLead.key_goals}
											<div>
												<dt class="text-sm font-medium text-gray-500 mb-2">Key Goals</dt>
												<dd class="text-sm text-gray-900 whitespace-pre-wrap">{$currentLead.key_goals}</dd>
											</div>
										{/if}
										{#if $currentLead.company_description}
											<div>
												<dt class="text-sm font-medium text-gray-500 mb-2">Company Description</dt>
												<dd class="text-sm text-gray-900 whitespace-pre-wrap">{$currentLead.company_description}</dd>
											</div>
										{/if}
										{#if $currentLead.recent_news}
											<div>
												<dt class="text-sm font-medium text-gray-500 mb-2">Recent News</dt>
												<dd class="text-sm text-gray-900 whitespace-pre-wrap">{$currentLead.recent_news}</dd>
											</div>
										{/if}
									</div>
								{/if}
							</div>
						</div>
					{/if}

					<!-- Notes and Details -->
					{#if $currentLead.notes || isEditing}
						<div class="bg-white shadow rounded-lg">
							<div class="px-4 py-5 sm:p-6">
								<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Notes</h3>
								
								{#if isEditing}
									<textarea
										bind:value={editForm.notes}
										rows="4"
										class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 mt-1 block w-full sm:text-sm border-gray-300 rounded-md"
										placeholder="Add notes about this lead..."
									></textarea>
								{:else}
									<p class="text-sm text-gray-900 whitespace-pre-wrap">{$currentLead.notes || 'No notes available.'}</p>
								{/if}
							</div>
						</div>
					{/if}
				</div>

				<!-- Sidebar -->
				<div class="space-y-6">
					<!-- Status and Score -->
					<div class="bg-white shadow rounded-lg">
						<div class="px-4 py-5 sm:p-6">
							<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Lead Status</h3>
							
							<div class="space-y-4">
								<div>
									<dt class="text-sm font-medium text-gray-500">Current Status</dt>
									<dd class="mt-1">
										<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getStatusColor($currentLead.status)}">
											{($currentLead.status || 'unknown').replace('_', ' ').toUpperCase()}
										</span>
									</dd>
								</div>

								<div>
									<dt class="text-sm font-medium text-gray-500">Lead Score</dt>
									<dd class="mt-1">
										<div class="flex items-center">
											<div class="text-2xl font-bold text-gray-900">{$currentLead.score}/100</div>
											<div class="ml-3 flex-1">
												<div class="w-full bg-gray-200 rounded-full h-3">
													<div 
														class="bg-indigo-600 h-3 rounded-full" 
														style="width: {$currentLead.score}%"
													></div>
												</div>
											</div>
										</div>
									</dd>
								</div>

								<!-- Quick status change buttons -->
								<div>
									<dt class="text-sm font-medium text-gray-500 mb-2">Quick Actions</dt>
									<div class="grid grid-cols-2 gap-2">
										{#each Object.values(LeadStatus) as status}
											{#if status !== $currentLead.status}
												<button
													type="button"
													onclick={() => updateStatus(status)}
													class="text-xs px-2 py-1 border border-gray-300 rounded text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
												>
													{(status || 'unknown').replace('_', ' ').toUpperCase()}
												</button>
											{/if}
										{/each}
									</div>
								</div>
							</div>
						</div>
					</div>

					<!-- Enrichment Status -->
					<div class="bg-white shadow rounded-lg">
						<div class="px-4 py-5 sm:p-6">
							<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Enrichment Status</h3>
							
							<dl class="space-y-4">
								<div>
									<dt class="text-sm font-medium text-gray-500">Status</dt>
									<dd class="mt-1">
										<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getEnrichmentStatusColor($currentLead.enrichment_status)}">
											{($currentLead.enrichment_status || 'not enriched').replace('_', ' ').toUpperCase()}
										</span>
									</dd>
								</div>

								{#if $currentLead.enrichment_confidence}
									<div>
										<dt class="text-sm font-medium text-gray-500">Confidence Score</dt>
										<dd class="mt-1">
											<div class="flex items-center">
												<div class="text-lg font-bold text-gray-900">{Math.round(($currentLead.enrichment_confidence || 0) * 100)}%</div>
												<div class="ml-3 flex-1">
													<div class="w-full bg-gray-200 rounded-full h-2">
														<div 
															class="bg-purple-600 h-2 rounded-full" 
															style="width: {($currentLead.enrichment_confidence || 0) * 100}%"
														></div>
													</div>
												</div>
											</div>
										</dd>
									</div>
								{/if}

								{#if $currentLead.enriched_at}
									<div>
										<dt class="text-sm font-medium text-gray-500">Last Enriched</dt>
										<dd class="mt-1 text-sm text-gray-900">{formatDate($currentLead.enriched_at)}</dd>
									</div>
								{/if}
							</dl>
						</div>
					</div>

					<!-- Lead Details -->
					<div class="bg-white shadow rounded-lg">
						<div class="px-4 py-5 sm:p-6">
							<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Lead Details</h3>
							
							<dl class="space-y-4">
								<div>
									<dt class="text-sm font-medium text-gray-500">Source</dt>
									<dd class="mt-1 text-sm text-gray-900">{($currentLead.source || 'unknown').replace('_', ' ').toUpperCase()}</dd>
								</div>

								<div>
									<dt class="text-sm font-medium text-gray-500">Created</dt>
									<dd class="mt-1 text-sm text-gray-900">{formatDate($currentLead.created_at)}</dd>
								</div>

								<div>
									<dt class="text-sm font-medium text-gray-500">Last Updated</dt>
									<dd class="mt-1 text-sm text-gray-900">{formatDate($currentLead.updated_at)}</dd>
								</div>
							</dl>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>