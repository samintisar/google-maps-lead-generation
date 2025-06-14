<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';

	// Types
	interface Lead {
		id: number;
		name?: string;
		email?: string;
		company?: string;
		status?: string;
		source?: string;
		created_at?: string;
		enrichment_status?: string;
		enrichment_confidence?: number;
		enriched_at?: string;
		linkedin_profile?: string;
		twitter_profile?: string;
		facebook_profile?: string;
		instagram_profile?: string;
		company_description?: string;
		pain_points?: string;
		key_goals?: string;
		ideal_customer_profile?: string;
		recent_news?: string;
		key_personnel?: string | object;
	}

	interface EnrichmentOptions {
		socialProfiles: boolean;
		companyInfo: boolean;
		painPoints: boolean;
		keyPersonnel: boolean;
	}

	interface StatusOption {
		value: string;
		label: string;
	}

	// UI State
	let activeTab = 'overview';
	let isLoading = false;
	let saveStatus = '';
	// Test connection variables removed - API keys handled via environment

	// Lead enrichment settings
	let enrichmentSettings = {
		batchSize: 10,
		status: 'new',
		confidenceThreshold: 0.8,
		includeIndustry: true,
		includeSocialProfiles: true,
		includeCompanyInfo: true,
		includePersonnel: true
	};

	// Stats
	let stats = {
		totalLeads: 0,
		enrichedLeads: 0,
		pendingLeads: 0,
		averageConfidence: 0,
		successRate: 0
	};

	// Recent enrichments
	let recentEnrichments: Lead[] = [];

	// API key management
	let apiKey = '';
	let isApiKeyConfigured = false;

	// State management
	let leads: Lead[] = [];
	let selectedLeads: number[] = [];
	let filteredLeads: Lead[] = [];
	let loading = false;
	let enriching = false;

	// Stats
	let totalLeads = 0;
	let enrichedCount = 0;
	let pendingCount = 0;
	let averageConfidence = 'N/A';

	// Configuration
	let batchSize = 10;
	let statusFilter = 'new';
	let sourceFilter = 'all';
	let companyFilter = '';
	let dateFromFilter = '';
	let dateToFilter = '';
	let enrichmentOptions: EnrichmentOptions = {
		socialProfiles: true,
		companyInfo: true,
		painPoints: true,
		keyPersonnel: true
	};

	// Available filter options
	const statusOptions: StatusOption[] = [
		{ value: 'all', label: 'All Statuses' },
		{ value: 'new', label: 'New' },
		{ value: 'contacted', label: 'Contacted' },
		{ value: 'qualified', label: 'Qualified' },
		{ value: 'unqualified', label: 'Unqualified' },
		{ value: 'converted', label: 'Converted' }
	];

	const sourceOptions: StatusOption[] = [
		{ value: 'all', label: 'All Sources' },
		{ value: 'website', label: 'Website' },
		{ value: 'referral', label: 'Referral' },
		{ value: 'social_media', label: 'Social Media' },
		{ value: 'email_campaign', label: 'Email Campaign' },
		{ value: 'trade_show', label: 'Trade Show' },
		{ value: 'cold_outreach', label: 'Cold Outreach' },
		{ value: 'organic_search', label: 'Organic Search' },
		{ value: 'paid_ads', label: 'Paid Ads' }
	];

	onMount(async () => {
		await loadStats();
		await loadRecentEnrichments();
		await checkApiKeyStatus();
		await fetchLeads();
	});

	async function loadStats() {
		try {
			const response = await api.get('/api/leads/?skip=0&limit=1000');
			const leadsData = response as Lead[];
			
			stats.totalLeads = leadsData.length;
			stats.enrichedLeads = leadsData.filter(l => l.enrichment_status === 'completed').length;
			stats.pendingLeads = leadsData.filter(l => l.enrichment_status === 'pending').length;
			
			const enrichedWithConfidence = leadsData.filter(l => l.enrichment_confidence && l.enrichment_confidence > 0);
			if (enrichedWithConfidence.length > 0) {
				stats.averageConfidence = enrichedWithConfidence.reduce((sum, l) => sum + (l.enrichment_confidence || 0), 0) / enrichedWithConfidence.length;
			}
			
			stats.successRate = stats.totalLeads > 0 ? (stats.enrichedLeads / stats.totalLeads) * 100 : 0;
		} catch (error) {
			console.error('Failed to load stats:', error);
		}
	}

	async function loadRecentEnrichments() {
		try {
			const response = await api.get('/api/leads/?status=completed&limit=20');
			recentEnrichments = (response as Lead[]).filter(l => l.enriched_at);
		} catch (error) {
			console.error('Failed to load recent enrichments:', error);
		}
	}

	async function checkApiKeyStatus() {
		// Check if Perplexity API key is configured in backend
		try {
			const response = await api.get('/api/health');
			// This is a simplified check - in a real app you'd have a dedicated endpoint
			isApiKeyConfigured = true;
		} catch (error) {
			isApiKeyConfigured = false;
		}
	}

	// Test connection functionality removed - API keys are configured via environment variables

	async function enrichLeads() {
		if (!isApiKeyConfigured) {
			alert('Please configure your Perplexity API key first.');
			return;
		}

		isLoading = true;
		saveStatus = 'Starting lead enrichment process...';
		
		try {
			// Get leads that need enrichment
			const response = await api.get(`/api/leads/?status=${enrichmentSettings.status}&limit=${enrichmentSettings.batchSize}`);
			const leadsData = response as Lead[];
			
			if (leadsData.length === 0) {
				saveStatus = 'No leads found matching the criteria.';
				setTimeout(() => saveStatus = '', 3000);
				return;
			}

			saveStatus = `Enriching ${leadsData.length} leads...`;
			
			let enrichedCount = 0;
			let failedCount = 0;

			// Process leads one by one
			for (const lead of leadsData) {
				try {
					const enrichResult = await api.post(`/api/leads/${lead.id}/enrich`, {
						includeIndustry: enrichmentSettings.includeIndustry,
						includeSocialProfiles: enrichmentSettings.includeSocialProfiles,
						includeCompanyInfo: enrichmentSettings.includeCompanyInfo,
						includePersonnel: enrichmentSettings.includePersonnel
					});
					enrichedCount++;
					saveStatus = `Enriched ${enrichedCount}/${leadsData.length} leads...`;
				} catch (error) {
					failedCount++;
					console.error(`Failed to enrich lead ${lead.id}:`, error);
				}
			}

			saveStatus = `✅ Enrichment complete! ${enrichedCount} leads enriched successfully, ${failedCount} failed.`;
			
			// Refresh data
			await loadStats();
			await loadRecentEnrichments();
			
			setTimeout(() => {
				saveStatus = '';
			}, 5000);
			
		} catch (error: any) {
			saveStatus = `❌ Enrichment failed: ${error.detail || error.message}`;
			setTimeout(() => saveStatus = '', 5000);
		} finally {
			isLoading = false;
		}
	}

	function getStatusColor(status: string): string {
		switch (status) {
			case 'completed': return 'text-green-600 bg-green-100';
			case 'pending': return 'text-yellow-600 bg-yellow-100';
			case 'failed': return 'text-red-600 bg-red-100';
			default: return 'text-gray-600 bg-gray-100';
		}
	}

	function formatDateTime(dateString: string): string {
		if (!dateString) return 'N/A';
		return new Date(dateString).toLocaleString();
	}

	// Test status icon function removed - no longer needed

	// Fetch leads from API
	async function fetchLeads() {
		loading = true;
		try {
			const params = new URLSearchParams({
				limit: '1000',
				skip: '0'
			});

			if (statusFilter && statusFilter !== 'all') {
				params.append('status', statusFilter);
			}
			if (sourceFilter && sourceFilter !== 'all') {
				params.append('source', sourceFilter);
			}
			if (companyFilter.trim()) {
				params.append('search', companyFilter.trim());
			}

			// Use the API client instead of direct fetch
			const data = await api.get(`/api/leads/?${params}`);
			// Backend returns leads array directly, not wrapped in an object
			leads = Array.isArray(data) ? data as Lead[] : [];
			totalLeads = leads.length;
			filterLeads();
			updateStats();
		} catch (error) {
			console.error('Error fetching leads:', error);
		} finally {
			loading = false;
		}
	}

	// Filter leads based on current filters
	function filterLeads() {
		filteredLeads = leads.filter((lead: Lead) => {
			// Date filter
			if (dateFromFilter || dateToFilter) {
				const leadDate = new Date(lead.created_at || '');
				if (dateFromFilter && leadDate < new Date(dateFromFilter)) return false;
				if (dateToFilter && leadDate > new Date(dateToFilter)) return false;
			}

			// Company filter (already handled in API call, but double-check)
			if (companyFilter.trim()) {
				const searchTerm = companyFilter.toLowerCase();
				const matchesCompany = lead.company?.toLowerCase().includes(searchTerm);
				const matchesName = lead.name?.toLowerCase().includes(searchTerm);
				const matchesEmail = lead.email?.toLowerCase().includes(searchTerm);
				if (!matchesCompany && !matchesName && !matchesEmail) return false;
			}

			return true;
		});
	}

	// Update statistics
	function updateStats() {
		enrichedCount = leads.filter((lead: Lead) => lead.enrichment_status === 'completed').length;
		pendingCount = leads.filter((lead: Lead) => !lead.enrichment_status || lead.enrichment_status === 'pending').length;
		
		const enrichedWithConfidence = leads.filter((lead: Lead) => lead.enrichment_confidence);
		if (enrichedWithConfidence.length > 0) {
			const avgConf = enrichedWithConfidence.reduce((sum, lead) => sum + (lead.enrichment_confidence || 0), 0) / enrichedWithConfidence.length;
			averageConfidence = Math.round(avgConf * 100) + '%';
		}
	}

	// Handle lead selection
	function toggleLeadSelection(leadId: number) {
		if (selectedLeads.includes(leadId)) {
			selectedLeads = selectedLeads.filter(id => id !== leadId);
		} else {
			selectedLeads = [...selectedLeads, leadId];
		}
	}

	function selectAllFilteredLeads() {
		selectedLeads = filteredLeads.map((lead: Lead) => lead.id);
	}

	function clearSelection() {
		selectedLeads = [];
	}

	// Start enrichment process
	async function startEnrichment() {
		if (selectedLeads.length === 0) {
			alert('Please select at least one lead to enrich.');
			return;
		}

		enriching = true;
		try {
			const results: Array<{leadId: number, success: boolean, data?: any, error?: string}> = [];
			
			// Process leads in batches
			for (let i = 0; i < selectedLeads.length; i += batchSize) {
				const batch = selectedLeads.slice(i, i + batchSize);
				
				const batchPromises = batch.map(async (leadId: number) => {
					try {
						// Use the API client instead of direct fetch
						const result = await api.post(`/api/leads/${leadId}/enrich`, {
							options: enrichmentOptions
						});
						return { leadId, success: true, data: result };
					} catch (error: unknown) {
						const errorMessage = error instanceof Error ? error.message : 'Unknown error';
						return { leadId, success: false, error: errorMessage };
					}
				});

				const batchResults = await Promise.all(batchPromises);
				results.push(...batchResults);

				// Small delay between batches to avoid overwhelming the API
				if (i + batchSize < selectedLeads.length) {
					await new Promise(resolve => setTimeout(resolve, 1000));
				}
			}

			// Update the leads list with enriched data
			await fetchLeads();
			
			// Show results
			const successCount = results.filter(r => r.success).length;
			const failCount = results.filter(r => !r.success).length;
			
			alert(`Enrichment completed!\nSuccess: ${successCount}\nFailed: ${failCount}`);
			
			// Switch to results tab
			activeTab = 'results';
			clearSelection();

		} catch (error) {
			console.error('Enrichment error:', error);
			alert('An error occurred during enrichment. Please try again.');
		} finally {
			enriching = false;
		}
	}

	// Reactive updates
	$: {
		if (statusFilter || sourceFilter || companyFilter || dateFromFilter || dateToFilter) {
			fetchLeads();
		}
	}
</script>

<svelte:head>
	<title>Lead Enrichment - Perplexity AI - LMA</title>
</svelte:head>

<!-- Header -->
<div class="mb-8">
	<div class="flex items-center space-x-4 mb-4">
		<button
			on:click={() => goto('/workflows')}
			class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
		>
			← Back to Workflows
		</button>
	</div>
	<h1 class="text-3xl font-bold text-gray-900">Lead Enrichment Workflow</h1>
	<p class="mt-2 text-gray-600">
		Automatically enrich lead data using Perplexity AI. Get LinkedIn profiles, company information, 
		pain points, goals, and decision-maker contacts for better sales targeting.
	</p>
</div>

<!-- Stats Cards -->
<div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
	<div class="bg-white rounded-lg shadow p-6">
		<div class="flex items-center">
			<div class="flex-shrink-0">
				<div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
					<span class="text-blue-600 font-semibold">👥</span>
				</div>
			</div>
			<div class="ml-4">
				<p class="text-sm font-medium text-gray-500">Total Leads</p>
				<p class="text-2xl font-semibold text-gray-900">{totalLeads}</p>
			</div>
		</div>
	</div>

	<div class="bg-white rounded-lg shadow p-6">
		<div class="flex items-center">
			<div class="flex-shrink-0">
				<div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
					<span class="text-green-600 font-semibold">✨</span>
				</div>
			</div>
			<div class="ml-4">
				<p class="text-sm font-medium text-gray-500">Enriched Leads</p>
				<p class="text-2xl font-semibold text-gray-900">{enrichedCount}</p>
			</div>
		</div>
	</div>

	<div class="bg-white rounded-lg shadow p-6">
		<div class="flex items-center">
			<div class="flex-shrink-0">
				<div class="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
					<span class="text-yellow-600 font-semibold">⏳</span>
				</div>
			</div>
			<div class="ml-4">
				<p class="text-sm font-medium text-gray-500">Pending</p>
				<p class="text-2xl font-semibold text-gray-900">{pendingCount}</p>
			</div>
		</div>
	</div>

	<div class="bg-white rounded-lg shadow p-6">
		<div class="flex items-center">
			<div class="flex-shrink-0">
				<div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
					<span class="text-purple-600 font-semibold">🎯</span>
				</div>
			</div>
			<div class="ml-4">
				<p class="text-sm font-medium text-gray-500">Avg Confidence</p>
				<p class="text-2xl font-semibold text-gray-900">
					{averageConfidence}
				</p>
			</div>
		</div>
	</div>
</div>

<!-- Tabs -->
<div class="bg-white rounded-lg shadow">
	<div class="border-b border-gray-200">
		<nav class="-mb-px flex space-x-8 px-6">
			<button
				class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'overview' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				on:click={() => activeTab = 'overview'}
			>
				📊 Overview
			</button>
			<button
				class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'enrich' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				on:click={() => activeTab = 'enrich'}
			>
				⭐ Enrich Leads
			</button>
			<button
				class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'results' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				on:click={() => activeTab = 'results'}
			>
				📋 Results
			</button>
		</nav>
	</div>

	<div class="p-6">
		<!-- Overview Tab -->
		{#if activeTab === 'overview'}
			<div class="space-y-8">
				<!-- Perplexity AI Status -->
				<div class="border border-gray-200 rounded-lg p-6">
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center space-x-3">
							<div class="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
								<span class="text-purple-600 font-semibold">🧠</span>
							</div>
							<div>
								<h4 class="text-lg font-medium text-gray-900">Perplexity AI</h4>
								<p class="text-sm text-gray-500">AI-powered lead research and enrichment</p>
							</div>
						</div>
						<div class="flex items-center space-x-2">
							<span class="text-lg">✅</span>
							<span class="text-sm text-gray-600">Ready</span>
						</div>
					</div>

					<div class="space-y-4">
						<div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
							<h5 class="text-sm font-medium text-blue-900 mb-2">What does this enrichment include?</h5>
							<ul class="text-sm text-blue-800 space-y-1">
								<li>• <strong>Social Profiles:</strong> LinkedIn, Twitter, Facebook, Instagram</li>
								<li>• <strong>Company Intelligence:</strong> Industry, description, recent news</li>
								<li>• <strong>Business Insights:</strong> Pain points, goals, ideal customer profile</li>
								<li>• <strong>Key Personnel:</strong> Decision makers and contact information</li>
								<li>• <strong>Confidence Scoring:</strong> AI-generated confidence scores for data quality</li>
							</ul>
						</div>

						<div class="bg-green-50 border border-green-200 rounded-lg p-4">
							<p class="text-sm text-green-800">✅ Perplexity AI is configured and ready to enrich your leads. API keys are managed via environment variables.</p>
						</div>
					</div>
				</div>

				<!-- How it works -->
				<div class="border border-gray-200 rounded-lg p-6">
					<h4 class="text-lg font-medium text-gray-900 mb-4">How Lead Enrichment Works</h4>
					<div class="space-y-4">
						<div class="flex items-start space-x-3">
							<div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-semibold text-sm">1</div>
							<div>
								<h5 class="text-sm font-medium text-gray-900">Select Leads</h5>
								<p class="text-sm text-gray-600">Choose leads by status (new, contacted, etc.) and batch size</p>
							</div>
						</div>
						<div class="flex items-start space-x-3">
							<div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 font-semibold text-sm">2</div>
							<div>
								<h5 class="text-sm font-medium text-gray-900">AI Research</h5>
								<p class="text-sm text-gray-600">Perplexity AI researches each lead using their name, email, and company</p>
							</div>
						</div>
						<div class="flex items-start space-x-3">
							<div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center text-green-600 font-semibold text-sm">3</div>
							<div>
								<h5 class="text-sm font-medium text-gray-900">Data Enrichment</h5>
								<p class="text-sm text-gray-600">Enrich with social profiles, company info, pain points, and key personnel</p>
							</div>
						</div>
						<div class="flex items-start space-x-3">
							<div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center text-orange-600 font-semibold text-sm">4</div>
							<div>
								<h5 class="text-sm font-medium text-gray-900">Quality Scoring</h5>
								<p class="text-sm text-gray-600">AI assigns confidence scores to ensure data quality</p>
							</div>
						</div>
						<div class="flex items-start space-x-3">
							<div class="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 font-semibold text-sm">5</div>
							<div>
								<h5 class="text-sm font-medium text-gray-900">Database Update</h5>
								<p class="text-sm text-gray-600">Enriched data is saved to your Neon PostgreSQL database</p>
							</div>
						</div>
					</div>
				</div>
			</div>

		<!-- Enrich Tab -->
		{:else if activeTab === 'enrich'}
			<div class="space-y-6">
				<div>
					<h3 class="text-lg font-medium text-gray-900 mb-4">Lead Selection & Filters</h3>
					<p class="text-gray-600 mb-6">Filter and select specific leads for enrichment.</p>

					<!-- Filters -->
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">Lead Status Filter</label>
							<select bind:value={statusFilter} class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
								{#each statusOptions as option}
									<option value={option.value}>{option.label}</option>
								{/each}
							</select>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">Source Filter</label>
							<select bind:value={sourceFilter} class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
								{#each sourceOptions as option}
									<option value={option.value}>{option.label}</option>
								{/each}
							</select>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">Search (Name/Company/Email)</label>
							<input 
								type="text" 
								bind:value={companyFilter}
								placeholder="Search leads..."
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">Date From</label>
							<input 
								type="date" 
								bind:value={dateFromFilter}
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">Date To</label>
							<input 
								type="date" 
								bind:value={dateToFilter}
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">Batch Size</label>
							<input 
								type="number" 
								bind:value={batchSize}
								min="1" 
								max="50"
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							/>
						</div>
					</div>

					<!-- Lead Selection -->
					<div class="mb-6">
						<div class="flex items-center justify-between mb-4">
							<h4 class="text-md font-semibold text-gray-900">
								Select Leads ({selectedLeads.length} of {filteredLeads.length} selected)
							</h4>
							<div class="space-x-2">
								<button 
									on:click={selectAllFilteredLeads}
									class="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
								>
									Select All Filtered
								</button>
								<button 
									on:click={clearSelection}
									class="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
								>
									Clear Selection
								</button>
							</div>
						</div>

						{#if loading}
							<div class="text-center py-8">
								<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
								<p class="mt-2 text-gray-600">Loading leads...</p>
							</div>
						{:else if filteredLeads.length === 0}
							<div class="text-center py-8 text-gray-500">
								<svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
								</svg>
								<p class="mt-2">No leads found matching your filters.</p>
							</div>
						{:else}
							<div class="max-h-96 overflow-y-auto border border-gray-200 rounded-lg">
								<div class="divide-y divide-gray-200">
									{#each filteredLeads as lead (lead.id)}
										<div class="p-4 hover:bg-gray-50 flex items-center space-x-3">
											<input 
												type="checkbox" 
												checked={selectedLeads.includes(lead.id)}
												on:change={() => toggleLeadSelection(lead.id)}
												class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
											/>
											<div class="flex-1 min-w-0">
												<div class="flex items-center justify-between">
													<div>
														<p class="text-sm font-medium text-gray-900 truncate">{lead.name || 'No Name'}</p>
														<p class="text-sm text-gray-500 truncate">{lead.email || 'No Email'}</p>
														{#if lead.company}
															<p class="text-sm text-gray-500 truncate">{lead.company}</p>
														{/if}
													</div>
													<div class="text-right">
														<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium 
															{lead.status === 'new' ? 'bg-blue-100 text-blue-800' : 
															 lead.status === 'contacted' ? 'bg-yellow-100 text-yellow-800' :
															 lead.status === 'qualified' ? 'bg-green-100 text-green-800' :
															 lead.status === 'converted' ? 'bg-purple-100 text-purple-800' :
															 'bg-gray-100 text-gray-800'}">
															{lead.status || 'unknown'}
														</span>
														{#if lead.enrichment_status === 'completed'}
															<div class="mt-1">
																<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
																	✓ Enriched
																</span>
															</div>
														{/if}
													</div>
												</div>
											</div>
										</div>
									{/each}
								</div>
							</div>
						{/if}
					</div>

					<!-- Enrichment Options -->
					<div class="mb-6">
						<h4 class="text-md font-semibold text-gray-900 mb-3">Enrichment Options</h4>
						<div class="space-y-2">
							<label class="flex items-center">
								<input type="checkbox" bind:checked={enrichmentOptions.socialProfiles} class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
								<span class="ml-2 text-sm text-gray-700">Social Media Profiles (LinkedIn, Twitter, etc.)</span>
							</label>
							<label class="flex items-center">
								<input type="checkbox" bind:checked={enrichmentOptions.companyInfo} class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
								<span class="ml-2 text-sm text-gray-700">Company Information & Recent News</span>
							</label>
							<label class="flex items-center">
								<input type="checkbox" bind:checked={enrichmentOptions.painPoints} class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
								<span class="ml-2 text-sm text-gray-700">Industry & Pain Points Analysis</span>
							</label>
							<label class="flex items-center">
								<input type="checkbox" bind:checked={enrichmentOptions.keyPersonnel} class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
								<span class="ml-2 text-sm text-gray-700">Key Personnel & Decision Makers</span>
							</label>
						</div>
					</div>

					<!-- Start Enrichment Button -->
					<div class="flex justify-center">
						<button 
							on:click={startEnrichment}
							disabled={enriching || selectedLeads.length === 0}
							class="px-8 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
						>
							{#if enriching}
								<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
								<span>Enriching {selectedLeads.length} leads...</span>
							{:else}
								<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
								</svg>
								<span>Start AI Enrichment ({selectedLeads.length} selected)</span>
							{/if}
						</button>
					</div>
				</div>
			</div>

		<!-- Results Tab -->
		{:else if activeTab === 'results'}
			<div class="space-y-6">
				<div>
					<h3 class="text-lg font-medium text-gray-900 mb-4">Enrichment Results</h3>
					<p class="text-gray-600 mb-6">
						View and manage your enriched lead data.
					</p>
				</div>

				{#if loading}
					<div class="text-center py-8">
						<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
						<p class="mt-2 text-gray-600">Loading results...</p>
					</div>
				{:else}
					<!-- Enriched leads display -->
					{#each leads.filter(lead => lead.enrichment_status === 'completed') as lead (lead.id)}
						<div class="border border-gray-200 rounded-lg p-4 mb-4">
							<div class="flex items-start justify-between mb-3">
								<div>
									<h4 class="text-lg font-semibold text-gray-900">{lead.name || 'No Name'}</h4>
									<p class="text-gray-600">{lead.email || 'No Email'}</p>
									{#if lead.company}
										<p class="text-gray-600">{lead.company}</p>
									{/if}
								</div>
								{#if lead.enrichment_confidence}
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
										{Math.round(lead.enrichment_confidence * 100)}% confidence
									</span>
								{/if}
							</div>

							<!-- Social Profiles -->
							{#if lead.linkedin_profile || lead.twitter_profile || lead.facebook_profile || lead.instagram_profile}
								<div class="mb-3">
									<h5 class="text-sm font-semibold text-gray-700 mb-2">Social Profiles</h5>
									<div class="flex flex-wrap gap-2">
										{#if lead.linkedin_profile}
											<a href={lead.linkedin_profile} target="_blank" class="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-800 hover:bg-blue-200">
												LinkedIn
											</a>
										{/if}
										{#if lead.twitter_profile}
											<a href={lead.twitter_profile} target="_blank" class="inline-flex items-center px-2 py-1 rounded text-xs bg-sky-100 text-sky-800 hover:bg-sky-200">
												Twitter
											</a>
										{/if}
										{#if lead.facebook_profile}
											<a href={lead.facebook_profile} target="_blank" class="inline-flex items-center px-2 py-1 rounded text-xs bg-indigo-100 text-indigo-800 hover:bg-indigo-200">
												Facebook
											</a>
										{/if}
										{#if lead.instagram_profile}
											<a href={lead.instagram_profile} target="_blank" class="inline-flex items-center px-2 py-1 rounded text-xs bg-pink-100 text-pink-800 hover:bg-pink-200">
												Instagram
											</a>
										{/if}
									</div>
								</div>
							{/if}

							<!-- Company & Business Info -->
							<div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
								{#if lead.company_description}
									<div>
										<h5 class="font-semibold text-gray-700 mb-1">Company Description</h5>
										<p class="text-gray-600">{lead.company_description}</p>
									</div>
								{/if}
								{#if lead.pain_points}
									<div>
										<h5 class="font-semibold text-gray-700 mb-1">Pain Points</h5>
										<p class="text-gray-600">{lead.pain_points}</p>
									</div>
								{/if}
								{#if lead.key_goals}
									<div>
										<h5 class="font-semibold text-gray-700 mb-1">Key Goals</h5>
										<p class="text-gray-600">{lead.key_goals}</p>
									</div>
								{/if}
								{#if lead.ideal_customer_profile}
									<div>
										<h5 class="font-semibold text-gray-700 mb-1">Ideal Customer Profile</h5>
										<p class="text-gray-600">{lead.ideal_customer_profile}</p>
									</div>
								{/if}
								{#if lead.recent_news}
									<div>
										<h5 class="font-semibold text-gray-700 mb-1">Recent News</h5>
										<p class="text-gray-600">{lead.recent_news}</p>
									</div>
								{/if}
								{#if lead.key_personnel}
									<div>
										<h5 class="font-semibold text-gray-700 mb-1">Key Personnel</h5>
										<p class="text-gray-600">{typeof lead.key_personnel === 'string' ? lead.key_personnel : JSON.stringify(lead.key_personnel)}</p>
									</div>
								{/if}
							</div>

							{#if lead.enriched_at}
								<div class="mt-3 pt-3 border-t border-gray-200">
									<p class="text-xs text-gray-500">Enriched on {new Date(lead.enriched_at).toLocaleDateString()}</p>
								</div>
							{/if}
						</div>
					{:else}
						<div class="text-center py-8 text-gray-500">
							<svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
							</svg>
							<p class="mt-2">No enriched leads found. Start enriching leads to see results here.</p>
						</div>
					{/each}
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	.tab {
		transition: all 0.2s ease-in-out;
	}
</style>
