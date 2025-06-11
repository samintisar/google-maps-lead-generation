<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';
	import { api } from '$lib/api';
	// Note: Using manual toast implementation instead of svelte-sonner
	function toast(message: string, type: 'success' | 'error' = 'success') {
		// You can replace this with your preferred toast implementation
		if (type === 'error') {
			alert(`Error: ${message}`);
		} else {
			alert(`Success: ${message}`);
		}
	}
	toast.success = (message: string) => toast(message, 'success');
	toast.error = (message: string) => toast(message, 'error');

	// Component state
	let isRunning = false;
	let currentExecution: any = null;
	let executionId: number | null = null;
	let searchExecutionId: number | null = null;
	let leads: any[] = [];
	let workflowStatus = 'idle';

	// Form data
	let location = '';
	let industry = '';
	let maxResults = 20;
	let includeAiEnrichment = true;
	let openaiApiKey = '';

	// Progress tracking
	let currentStep = '';
	let progressPercentage = 0;
	let totalUrlsFound = 0;
	let websitesScraped = 0;
	let emailsFound = 0;
	let leadsEnriched = 0;
	let leadsConverted = 0;

	// Polling for status updates
	let statusInterval: NodeJS.Timeout | null = null;

	onMount(async () => {
		// Check authentication
		console.log('Current auth state:', $authStore.user);
		console.log('Auth token:', $authStore.token);
		
		if (!$authStore.user) {
			console.warn('No user found, redirecting to login');
			goto('/login');
			return;
		}

		console.log('User authenticated, proceeding...');
		
		// Load any stored API key (you might want to get this from workflow credentials)
		// For now, we'll ask the user to enter it
	});

	onDestroy(() => {
		if (statusInterval) {
			clearInterval(statusInterval);
		}
	});

	async function startWorkflow() {
		if (!location.trim() || !industry.trim()) {
			toast.error('Please enter both location and industry');
			return;
		}

		if (includeAiEnrichment && !openaiApiKey.trim()) {
			toast.error('OpenAI API key is required for AI enrichment');
			return;
		}

		try {
			isRunning = true;
			workflowStatus = 'starting';

			console.log('Starting workflow with data:', {
				location: location.trim(),
				industry: industry.trim(),
				max_results: maxResults,
				include_ai_enrichment: includeAiEnrichment,
				has_openai_key: includeAiEnrichment ? !!openaiApiKey.trim() : false
			});

			const response = await api.post('/workflows/google-maps/start', {
				location: location.trim(),
				industry: industry.trim(),
				max_results: maxResults,
				include_ai_enrichment: includeAiEnrichment,
				openai_api_key: includeAiEnrichment ? openaiApiKey.trim() : null
			}) as any;

			console.log('API Response:', response);

			if (response.success) {
				executionId = response.data.execution_id;
				searchExecutionId = response.data.search_execution_id;
				workflowStatus = 'running';
				
				toast.success('Google Maps lead generation started!');
				
				// Start polling for status updates
				startStatusPolling();
			} else {
				throw new Error(response.message || 'Failed to start workflow');
			}
		} catch (error: any) {
			console.error('Error starting workflow:', error);
			toast.error(error.message || 'Failed to start workflow');
			isRunning = false;
			workflowStatus = 'idle';
		}
	}

	function startStatusPolling() {
		if (statusInterval) clearInterval(statusInterval);
		
		statusInterval = setInterval(async () => {
			if (executionId) {
				await updateStatus();
			}
		}, 2000); // Poll every 2 seconds
	}

	async function updateStatus() {
		if (!executionId) return;

		try {
			const response = await api.get(`/workflows/google-maps/status/${executionId}`) as any;
			
			if (response.success) {
				const data = response.data;
				
				// Update progress tracking
				currentStep = data.current_step || '';
				progressPercentage = data.progress_percentage || 0;
				totalUrlsFound = data.total_urls_found || 0;
				websitesScraped = data.websites_scraped || 0;
				emailsFound = data.emails_found || 0;
				leadsEnriched = data.leads_enriched || 0;
				leadsConverted = data.leads_converted || 0;
				leads = data.leads || [];
				
				// Update workflow status
				workflowStatus = data.status;
				
				// Stop polling if completed or failed
				if (data.status === 'completed' || data.status === 'failed') {
					if (statusInterval) {
						clearInterval(statusInterval);
						statusInterval = null;
					}
					isRunning = false;
					
					if (data.status === 'completed') {
						toast.success(`Workflow completed! Generated ${leads.length} leads`);
					} else {
						toast.error(`Workflow failed: ${data.error_message || 'Unknown error'}`);
					}
				}
			}
		} catch (error: any) {
			console.error('Error updating status:', error);
			// Don't show toast for status update errors to avoid spam
		}
	}

	async function convertLead(leadId: number) {
		try {
			const response = await api.post(`/workflows/google-maps/leads/${leadId}/convert`) as any;
			
			if (response.success) {
				toast.success(`Lead converted successfully! New CRM lead ID: ${response.data.lead_id}`);
				
				// Update the lead status in our local array
				leads = leads.map(lead => 
					lead.id === leadId 
						? { ...lead, conversion_status: 'converted', converted_to_lead_id: response.data.lead_id }
						: lead
				);
			} else {
				throw new Error(response.message || 'Failed to convert lead');
			}
		} catch (error: any) {
			console.error('Error converting lead:', error);
			toast.error(error.message || 'Failed to convert lead');
		}
	}

	function resetWorkflow() {
		isRunning = false;
		currentExecution = null;
		executionId = null;
		searchExecutionId = null;
		leads = [];
		workflowStatus = 'idle';
		currentStep = '';
		progressPercentage = 0;
		totalUrlsFound = 0;
		websitesScraped = 0;
		emailsFound = 0;
		leadsEnriched = 0;
		leadsConverted = 0;

		if (statusInterval) {
			clearInterval(statusInterval);
			statusInterval = null;
		}
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'pending': return 'text-yellow-600';
			case 'running': return 'text-blue-600';
			case 'completed': return 'text-green-600';
			case 'failed': return 'text-red-600';
			default: return 'text-gray-600';
		}
	}

	function getEnrichmentStatusColor(status: string) {
		switch (status) {
			case 'pending': return 'bg-yellow-100 text-yellow-800';
			case 'enriched': return 'bg-green-100 text-green-800';
			case 'failed': return 'bg-red-100 text-red-800';
			case 'skipped': return 'bg-gray-100 text-gray-800';
			default: return 'bg-gray-100 text-gray-800';
		}
	}
</script>

<svelte:head>
	<title>Google Maps Lead Generation - LMA</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
	<!-- Header -->
	<div class="mb-8">
		<div class="flex items-center gap-4 mb-4">
			<button 
				on:click={() => goto('/workflows')}
				class="text-gray-600 hover:text-gray-800"
			>
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
				</svg>
			</button>
			<div>
				<h1 class="text-3xl font-bold text-gray-900">Google Maps Lead Generation</h1>
				<p class="text-gray-600 mt-1">Scrape Google Maps for businesses and generate leads with AI enrichment</p>
			</div>
		</div>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
		<!-- Configuration Panel -->
		<div class="lg:col-span-1">
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
				<h2 class="text-xl font-semibold text-gray-900 mb-6">Workflow Configuration</h2>
				
				<form on:submit|preventDefault={startWorkflow} class="space-y-6">
					<!-- Location -->
					<div>
						<label for="location" class="block text-sm font-medium text-gray-700 mb-2">
							Location *
						</label>
						<input
							id="location"
							type="text"
							bind:value={location}
							placeholder="e.g., Calgary, New York City"
							disabled={isRunning}
							class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
							required
						/>
						<p class="text-xs text-gray-500 mt-1">Geographic location to search</p>
					</div>

					<!-- Industry -->
					<div>
						<label for="industry" class="block text-sm font-medium text-gray-700 mb-2">
							Industry *
						</label>
						<input
							id="industry"
							type="text"
							bind:value={industry}
							placeholder="e.g., dentists, restaurants, lawyers"
							disabled={isRunning}
							class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
							required
						/>
						<p class="text-xs text-gray-500 mt-1">Business type or industry to search for</p>
					</div>

					<!-- Max Results -->
					<div>
						<label for="maxResults" class="block text-sm font-medium text-gray-700 mb-2">
							Max Results
						</label>
						<input
							id="maxResults"
							type="number"
							bind:value={maxResults}
							min="1"
							max="100"
							disabled={isRunning}
							class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
						/>
						<p class="text-xs text-gray-500 mt-1">Maximum number of leads to generate (1-100)</p>
					</div>

					<!-- AI Enrichment -->
					<div>
						<div class="flex items-center mb-2">
							<input
								id="includeAiEnrichment"
								type="checkbox"
								bind:checked={includeAiEnrichment}
								disabled={isRunning}
								class="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
							/>
							<label for="includeAiEnrichment" class="ml-2 text-sm font-medium text-gray-700">
								Enable AI Enrichment
							</label>
						</div>
						<p class="text-xs text-gray-500">Use OpenAI to enrich lead data with business intelligence</p>
					</div>

					<!-- OpenAI API Key -->
					{#if includeAiEnrichment}
						<div>
							<label for="openaiApiKey" class="block text-sm font-medium text-gray-700 mb-2">
								OpenAI API Key *
							</label>
							<input
								id="openaiApiKey"
								type="password"
								bind:value={openaiApiKey}
								placeholder="sk-..."
								disabled={isRunning}
								class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
								required={includeAiEnrichment}
							/>
							<p class="text-xs text-gray-500 mt-1">Required for AI enrichment features</p>
						</div>
					{/if}

					<!-- Action Buttons -->
					<div class="space-y-3">
						{#if !isRunning}
							<button
								type="submit"
								class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
							>
								Start Lead Generation
							</button>
						{:else}
							<button
								type="button"
								disabled
								class="w-full bg-gray-400 text-white py-2 px-4 rounded-md cursor-not-allowed"
							>
								Running...
							</button>
						{/if}

						{#if executionId && !isRunning}
							<button
								type="button"
								on:click={resetWorkflow}
								class="w-full bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
							>
								Reset Workflow
							</button>
						{/if}
					</div>
				</form>

				<!-- Workflow Status -->
				{#if workflowStatus !== 'idle'}
					<div class="mt-6 pt-6 border-t border-gray-200">
						<h3 class="text-lg font-medium text-gray-900 mb-4">Workflow Status</h3>
						
						<div class="space-y-3">
							<div class="flex justify-between items-center">
								<span class="text-sm text-gray-700">Status:</span>
								<span class="text-sm font-medium {getStatusColor(workflowStatus)}">
									{workflowStatus.charAt(0).toUpperCase() + workflowStatus.slice(1)}
								</span>
							</div>

							{#if currentStep}
								<div class="flex justify-between items-center">
									<span class="text-sm text-gray-700">Current Step:</span>
									<span class="text-sm text-gray-900">{currentStep}</span>
								</div>
							{/if}

							<div class="space-y-2">
								<div class="flex justify-between items-center">
									<span class="text-sm text-gray-700">Progress:</span>
									<span class="text-sm text-gray-900">{progressPercentage.toFixed(1)}%</span>
								</div>
								<div class="w-full bg-gray-200 rounded-full h-2">
									<div 
										class="bg-blue-600 h-2 rounded-full transition-all duration-300"
										style="width: {progressPercentage}%"
									></div>
								</div>
							</div>

							<!-- Statistics -->
							<div class="grid grid-cols-2 gap-3 text-xs">
								<div class="text-center">
									<div class="text-gray-500">URLs Found</div>
									<div class="font-medium text-gray-900">{totalUrlsFound}</div>
								</div>
								<div class="text-center">
									<div class="text-gray-500">Sites Scraped</div>
									<div class="font-medium text-gray-900">{websitesScraped}</div>
								</div>
								<div class="text-center">
									<div class="text-gray-500">Emails Found</div>
									<div class="font-medium text-gray-900">{emailsFound}</div>
								</div>
								<div class="text-center">
									<div class="text-gray-500">AI Enriched</div>
									<div class="font-medium text-gray-900">{leadsEnriched}</div>
								</div>
							</div>
						</div>
					</div>
				{/if}
			</div>
		</div>

		<!-- Results Panel -->
		<div class="lg:col-span-2">
			<div class="bg-white rounded-lg shadow-sm border border-gray-200">
				<div class="p-6 border-b border-gray-200">
					<h2 class="text-xl font-semibold text-gray-900">Generated Leads</h2>
					<p class="text-gray-600 mt-1">
						{leads.length} leads generated
						{#if leadsEnriched > 0}
							• {leadsEnriched} enriched with AI
						{/if}
					</p>
				</div>

				<div class="p-6">
					{#if leads.length === 0}
						<div class="text-center py-12">
							<svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-2m-2 0H7m5 0v-9" />
							</svg>
							<h3 class="mt-2 text-sm font-medium text-gray-900">No leads yet</h3>
							<p class="mt-1 text-sm text-gray-500">
								{workflowStatus === 'idle' ? 'Start a workflow to generate leads' : 'Leads will appear here as they are generated'}
							</p>
						</div>
					{:else}
						<div class="space-y-4">
							{#each leads as lead (lead.id)}
								<div class="border border-gray-200 rounded-lg p-4">
									<div class="flex justify-between items-start mb-3">
										<div>
											<h3 class="text-lg font-medium text-gray-900">{lead.business_name}</h3>
											<p class="text-sm text-gray-600">{lead.industry} • {lead.location}</p>
										</div>
										<div class="flex items-center gap-2">
											{#if lead.enrichment_status}
												<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getEnrichmentStatusColor(lead.enrichment_status)}">
													{lead.enrichment_status}
												</span>
											{/if}
											{#if lead.conversion_status !== 'converted'}
												<button
													on:click={() => convertLead(lead.id)}
													class="bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700 transition-colors"
												>
													Convert to CRM
												</button>
											{:else}
												<span class="bg-green-100 text-green-800 px-2.5 py-0.5 rounded-full text-xs font-medium">
													Converted
												</span>
											{/if}
										</div>
									</div>

									<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
										<!-- Contact Information -->
										<div>
											<h4 class="text-sm font-medium text-gray-900 mb-2">Contact Information</h4>
											<div class="space-y-1 text-sm">
												{#if lead.email}
													<div>
														<span class="text-gray-500">Email:</span>
														<a href="mailto:{lead.email}" class="text-blue-600 hover:text-blue-800 ml-1">{lead.email}</a>
													</div>
												{/if}
												{#if lead.phone}
													<div>
														<span class="text-gray-500">Phone:</span>
														<a href="tel:{lead.phone}" class="text-blue-600 hover:text-blue-800 ml-1">{lead.phone}</a>
													</div>
												{/if}
												{#if lead.website_url}
													<div>
														<span class="text-gray-500">Website:</span>
														<a href={lead.website_url} target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 ml-1">
															{lead.website_url}
														</a>
													</div>
												{/if}
											</div>
										</div>

										<!-- AI Enriched Data -->
										{#if lead.ai_enriched_data}
											<div>
												<h4 class="text-sm font-medium text-gray-900 mb-2">AI Insights</h4>
												<div class="space-y-1 text-sm">
													{#if lead.ai_enriched_data.estimated_company_size}
														<div>
															<span class="text-gray-500">Company Size:</span>
															<span class="ml-1">{lead.ai_enriched_data.estimated_company_size}</span>
														</div>
													{/if}
													{#if lead.ai_enriched_data.lead_quality_score}
														<div>
															<span class="text-gray-500">Quality Score:</span>
															<span class="ml-1">{lead.ai_enriched_data.lead_quality_score}/10</span>
														</div>
													{/if}
													{#if lead.ai_enriched_data.business_description}
														<div>
															<span class="text-gray-500">Description:</span>
															<span class="ml-1 text-gray-700">{lead.ai_enriched_data.business_description}</span>
														</div>
													{/if}
													{#if lead.confidence_score}
														<div>
															<span class="text-gray-500">Confidence:</span>
															<span class="ml-1">{(lead.confidence_score * 100).toFixed(0)}%</span>
														</div>
													{/if}
												</div>
											</div>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>
</div> 