<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	// Auth store removed
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
	let maxResults = 10;

	// Progress tracking
	let currentStep = '';
	let progressPercentage = 0;
	let leadsGenerated = 0;

	// Polling for status updates
	let statusInterval: NodeJS.Timeout | null = null;

	onMount(async () => {
		// Authentication check removed
		console.log('Starting Google Maps workflow...');
		
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

		try {
			isRunning = true;
			workflowStatus = 'starting';

			console.log('Starting workflow with data:', {
				location: location.trim(),
				industry: industry.trim(),
				max_results: maxResults
			});

			const response = await api.post('/api/v1/workflows/google-maps/start', {
				location: location.trim(),
				industry: industry.trim(),
				max_results: maxResults
			}) as any;

			console.log('API Response:', response);

			if (response.success) {
				executionId = response.data.execution_id;
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
			const response = await api.get(`/api/v1/workflows/executions/${executionId}/status`) as any;
			
			if (response.success) {
				const data = response.data;
				
				// Update progress tracking
				currentStep = data.current_step || '';
				progressPercentage = data.progress_percentage || 0;
				
				// Extract leads from execution_data
				const executionData = data.execution_data || {};
				leadsGenerated = executionData.leads_generated || 0;
				leads = executionData.leads || [];
				
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

	async function convertLead(leadIndex: number) {
		try {
			const lead = leads[leadIndex];
			if (!lead) return;

			// Create a CRM lead from the Google Maps lead data
			const leadData: any = {
				name: lead.company_name || 'Unknown Company',
				company: lead.company_name || '',
				industry: lead.industry || '',
				website: lead.website || '',
				address: lead.address || '',
				google_maps_url: lead.google_maps_url || '',
				notes: `Generated from Google Maps workflow. Rating: ${lead.rating} (${lead.review_count} reviews)`,
				source: 'Google Maps Workflow',
				status: 'new',
				organization_id: 1, // Default organization for demo purposes
				score: lead.rating ? parseFloat(lead.rating) || 0.0 : 0.0
			};

			// Only add email if it exists and is valid
			if (lead.emails?.[0] && lead.emails[0].trim()) {
				leadData.email = lead.emails[0];
			}

			// Only add phone if it exists
			if (lead.phone && lead.phone.trim()) {
				leadData.phone = lead.phone;
			}

			const response = await api.post(`/api/v1/leads/`, leadData) as any;
			
			if (response.id) {
				toast.success(`Lead converted successfully! New CRM lead ID: ${response.id}`);
				
				// Update the lead status in our local array
				leads = leads.map((l, index) => 
					index === leadIndex 
						? { ...l, conversion_status: 'converted', converted_to_lead_id: response.id }
						: l
				);
			} else {
				throw new Error('Failed to create lead');
			}
		} catch (error: any) {
			console.error('Error converting lead:', error);
			
			// Try to extract meaningful error message
			let errorMessage = 'Failed to convert lead';
			if (error.message && typeof error.message === 'string') {
				errorMessage = error.message;
			} else if (error.detail) {
				errorMessage = error.detail;
			} else if (error.toString && error.toString() !== '[object Object]') {
				errorMessage = error.toString();
			}
			
			toast.error(errorMessage);
		}
	}

	function resetWorkflow() {
		isRunning = false;
		currentExecution = null;
		executionId = null;
		leads = [];
		workflowStatus = 'idle';
		currentStep = '';
		progressPercentage = 0;
		leadsGenerated = 0;

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
				aria-label="Back to workflows"
			>
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
				</svg>
			</button>
			<div>
				<h1 class="text-3xl font-bold text-gray-900">Google Maps Lead Generation</h1>
				<p class="text-gray-600 mt-1">Generate high-quality business leads using Google Places API with real business data</p>
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
							max="20"
							disabled={isRunning}
							class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
						/>
						<p class="text-xs text-gray-500 mt-1">Maximum number of leads to generate (1-20)</p>
					</div>

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
							<div class="grid grid-cols-1 gap-3 text-xs">
								<div class="text-center">
									<div class="text-gray-500">Leads Generated</div>
									<div class="font-medium text-gray-900">{leadsGenerated}</div>
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
						{leads.length} leads generated from Google Places API
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
							{#each leads as lead, index (index)}
								<div class="border border-gray-200 rounded-lg p-4">
									<div class="flex justify-between items-start mb-3">
										<div>
											<h3 class="text-lg font-medium text-gray-900">{lead.company_name || 'Unknown Business'}</h3>
											<div class="flex items-center gap-2 text-sm text-gray-600">
												<span>{lead.industry || 'Business'}</span>
												{#if lead.rating}
													<span>•</span>
													<span>⭐ {lead.rating}</span>
													{#if lead.review_count}
														<span>({lead.review_count} reviews)</span>
													{/if}
												{/if}
											</div>
										</div>
										<div class="flex items-center gap-2">
											<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
												{lead.source || 'Google Places API'}
											</span>
											{#if lead.conversion_status !== 'converted'}
												<button
													on:click={() => convertLead(index)}
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
									{#if lead.phone}
									<div>
									<span class="text-gray-500">Phone:</span>
									<a href="tel:{lead.phone}" class="text-blue-600 hover:text-blue-800 ml-1">{lead.phone}</a>
									</div>
									{/if}
									{#if lead.website}
									<div>
									<span class="text-gray-500">Website:</span>
									<a href={lead.website} target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 ml-1">
									  {lead.website}
									  </a>
									 </div>
									{/if}
									{#if lead.address}
									<div>
									<span class="text-gray-500">Address:</span>
									<span class="ml-1">{lead.address}</span>
									</div>
									{/if}
									 {#if lead.emails && lead.emails.length > 0}
									   <div>
															<span class="text-gray-500">Email:</span>
															{#each lead.emails as email}
																<a href="mailto:{email}" class="text-blue-600 hover:text-blue-800 ml-1">{email}</a>
															{/each}
														</div>
													{/if}
												</div>
											</div>

										<!-- Google Places Data -->
										<div>
										<h4 class="text-sm font-medium text-gray-900 mb-2">Business Details</h4>
										<div class="space-y-1 text-sm">
										{#if lead.business_status}
										<div>
										<span class="text-gray-500">Status:</span>
										<span class="ml-1 {lead.business_status === 'OPERATIONAL' ? 'text-green-600' : 'text-red-600'}">
										{lead.business_status === 'OPERATIONAL' ? 'Open' : lead.business_status}
										</span>
										</div>
										{/if}
										{#if lead.place_id}
										<div>
										<span class="text-gray-500">Place ID:</span>
										<span class="ml-1 font-mono text-xs">{lead.place_id}</span>
										</div>
										{/if}
										{#if lead.google_maps_url}
										<div>
										<span class="text-gray-500">Google Maps:</span>
										<a href={lead.google_maps_url} target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 ml-1">
										  View on Maps
										 </a>
										</div>
										{/if}
										</div>
										</div>
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