<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { authStore } from '$lib/stores/auth';

	// UI State
	let activeTab = 'credentials';
	let isLoading = false;
	let saveStatus = '';
	let testStatus: Record<string, any> = {};
	let executions: any[] = [];
	let workflowStats: Record<string, any> = {};

	// Credentials
	let credentials = {
		hubspot: {
			hubspot_api_key: '',
			hubspot_access_token: ''
		},
		openai: {
			openai_api_key: ''
		},
		google: {
			type: 'service_account',
			project_id: '',
			private_key_id: '',
			private_key: '',
			client_email: '',
			client_id: '',
			auth_uri: 'https://accounts.google.com/o/oauth2/auth',
			token_uri: 'https://oauth2.googleapis.com/token',
			auth_provider_x509_cert_url: 'https://www.googleapis.com/oauth2/v1/certs'
		}
	};

	// Workflow execution settings
	let workflowSettings = {
		workflow_type: 'lead_enrichment',
		lead_filters: {
			limit: 100,
			status: 'new'
		},
		validation_threshold: 0.85
	};

	// Stored credentials status
	let storedCredentials: any[] = [];

	onMount(async () => {
		if (!$authStore.user) {
			goto('/login');
			return;
		}
		
		await loadStoredCredentials();
		await loadWorkflowStats();
		await loadExecutions();
	});

	async function loadStoredCredentials() {
		try {
			const response = await api.get('/api/workflows/credentials');
			storedCredentials = response as any[];
			
			testStatus = {};
			for (const cred of storedCredentials) {
				testStatus[cred.service_name] = {
					status: 'stored',
					message: 'Credentials stored'
				};
			}
		} catch (error) {
			console.error('Failed to load stored credentials:', error);
		}
	}

	async function loadWorkflowStats() {
		try {
			const response = await api.get('/api/workflows/stats');
			workflowStats = response as Record<string, any>;
		} catch (error) {
			console.error('Failed to load workflow stats:', error);
		}
	}

	async function loadExecutions() {
		try {
			const response = await api.get('/api/workflows/executions?limit=20');
			executions = response as any[];
		} catch (error) {
			console.error('Failed to load executions:', error);
		}
	}

	async function saveCredentials(serviceName: string) {
		isLoading = true;
		saveStatus = `Saving ${serviceName} credentials...`;
		
		try {
			await api.post(`/api/workflows/credentials/${serviceName}`, {
				credentials: (credentials as any)[serviceName]
			});
			
			saveStatus = `${serviceName} credentials saved successfully!`;
			await loadStoredCredentials();
			
			setTimeout(() => {
				saveStatus = '';
			}, 3000);
			
		} catch (error: any) {
			saveStatus = `Failed to save ${serviceName} credentials: ${error.detail || error.message}`;
			setTimeout(() => {
				saveStatus = '';
			}, 5000);
		} finally {
			isLoading = false;
		}
	}

	async function testCredentials(serviceName: string) {
		testStatus[serviceName] = {
			status: 'testing',
			message: 'Testing credentials...'
		};
		
		try {
			const response = await api.post(`/api/workflows/test-credentials/${serviceName}`) as any;
			testStatus[serviceName] = {
				status: response.status,
				message: response.message,
				details: response.test_result
			};
		} catch (error: any) {
			testStatus[serviceName] = {
				status: 'error',
				message: error.detail || error.message
			};
		}
	}

	async function runWorkflow() {
		if (!areCredentialsValid()) {
			alert('Please set up and test all credentials before running the workflow.');
			return;
		}

		isLoading = true;
		
		try {
			const response = await api.post('/api/workflows/run', {
				...workflowSettings,
				credentials: credentials
			}) as any;
			
			alert(`Workflow started successfully! Execution ID: ${response.execution_id}`);
			await loadExecutions();
			activeTab = 'monitor';
			
		} catch (error: any) {
			alert(`Failed to start workflow: ${error.detail || error.message}`);
		} finally {
			isLoading = false;
		}
	}

	function areCredentialsValid() {
		const requiredServices = ['hubspot', 'openai', 'google'];
		return requiredServices.every(service => 
			testStatus[service]?.status === 'success'
		);
	}

	function getStatusIcon(status: string) {
		switch (status) {
			case 'success': return '✅';
			case 'error': return '❌';
			case 'testing': return '🔄';
			case 'stored': return '💾';
			default: return '⚪';
		}
	}

	function formatDateTime(dateString: string) {
		if (!dateString) return 'N/A';
		return new Date(dateString).toLocaleString();
	}

	function getExecutionStatusColor(status: string) {
		switch (status) {
			case 'completed': return 'text-green-600';
			case 'failed': return 'text-red-600';
			case 'running': return 'text-blue-600';
			case 'pending': return 'text-yellow-600';
			case 'cancelled': return 'text-gray-600';
			default: return 'text-gray-500';
		}
	}
</script>

<svelte:head>
	<title>Lead Enrichment Workflow - LMA</title>
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
		Automate lead enrichment using HubSpot, AI, and data validation. Set up your credentials, 
		configure workflows, and monitor execution progress.
	</p>
</div>

<!-- Stats Cards -->
{#if workflowStats}
<div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
	<div class="bg-white rounded-lg shadow p-6">
		<div class="flex items-center">
			<div class="flex-shrink-0">
				<div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
					<span class="text-blue-600 font-semibold">📊</span>
				</div>
			</div>
			<div class="ml-4">
				<p class="text-sm font-medium text-gray-500">Total Executions</p>
				<p class="text-2xl font-semibold text-gray-900">{workflowStats.total_executions || 0}</p>
			</div>
		</div>
	</div>

	<div class="bg-white rounded-lg shadow p-6">
		<div class="flex items-center">
			<div class="flex-shrink-0">
				<div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
					<span class="text-green-600 font-semibold">✅</span>
				</div>
			</div>
			<div class="ml-4">
				<p class="text-sm font-medium text-gray-500">Success Rate</p>
				<p class="text-2xl font-semibold text-gray-900">{Math.round(workflowStats.success_rate || 0)}%</p>
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
				<p class="text-sm font-medium text-gray-500">Leads Enriched</p>
				<p class="text-2xl font-semibold text-gray-900">{workflowStats.total_leads_enriched || 0}</p>
			</div>
		</div>
	</div>

	<div class="bg-white rounded-lg shadow p-6">
		<div class="flex items-center">
			<div class="flex-shrink-0">
				<div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
					<span class="text-orange-600 font-semibold">🎯</span>
				</div>
			</div>
			<div class="ml-4">
				<p class="text-sm font-medium text-gray-500">Avg Confidence</p>
				<p class="text-2xl font-semibold text-gray-900">
					{workflowStats.average_confidence_score ? Math.round(workflowStats.average_confidence_score * 100) + '%' : 'N/A'}
				</p>
			</div>
		</div>
	</div>
</div>
{/if}

<!-- Tabs -->
<div class="bg-white rounded-lg shadow">
	<div class="border-b border-gray-200">
		<nav class="-mb-px flex space-x-8 px-6">
			<button
				class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'credentials' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				on:click={() => activeTab = 'credentials'}
			>
				1. Credentials Setup
			</button>
			<button
				class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'workflow' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				on:click={() => activeTab = 'workflow'}
			>
				2. Run Workflow
			</button>
			<button
				class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'monitor' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				on:click={() => activeTab = 'monitor'}
			>
				3. Monitor Executions
			</button>
		</nav>
	</div>

	<div class="p-6">
		<!-- Credentials Tab -->
		{#if activeTab === 'credentials'}
			<div class="space-y-8">
				<div>
					<h3 class="text-lg font-medium text-gray-900 mb-4">Service Credentials</h3>
					<p class="text-gray-600 mb-6">
						Set up your API credentials for each service. All credentials are encrypted and stored securely.
					</p>
				</div>

				<!-- HubSpot Credentials -->
				<div class="border border-gray-200 rounded-lg p-6">
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center space-x-3">
							<div class="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
								<span class="text-orange-600 font-semibold">H</span>
							</div>
							<div>
								<h4 class="text-lg font-medium text-gray-900">HubSpot</h4>
								<p class="text-sm text-gray-500">CRM and contact management</p>
							</div>
						</div>
						<div class="flex items-center space-x-2">
							<span class="text-lg">{getStatusIcon(testStatus.hubspot?.status)}</span>
							<span class="text-sm text-gray-600">{testStatus.hubspot?.message || 'Not configured'}</span>
						</div>
					</div>

					<div class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">API Key (Legacy)</label>
							<input
								type="password"
								bind:value={credentials.hubspot.hubspot_api_key}
								placeholder="pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">Access Token (OAuth)</label>
							<input
								type="password"
								bind:value={credentials.hubspot.hubspot_access_token}
								placeholder="pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							/>
						</div>
						<div class="flex space-x-4">
							<button
								on:click={() => saveCredentials('hubspot')}
								disabled={isLoading}
								class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
							>
								Save HubSpot Credentials
							</button>
							<button
								on:click={() => testCredentials('hubspot')}
								disabled={!storedCredentials.some(c => c.service_name === 'hubspot')}
								class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
							>
								Test Connection
							</button>
						</div>
					</div>
				</div>

				<!-- OpenAI Credentials -->
				<div class="border border-gray-200 rounded-lg p-6">
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center space-x-3">
							<div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
								<span class="text-green-600 font-semibold">AI</span>
							</div>
							<div>
								<h4 class="text-lg font-medium text-gray-900">OpenAI</h4>
								<p class="text-sm text-gray-500">AI-powered lead enrichment</p>
							</div>
						</div>
						<div class="flex items-center space-x-2">
							<span class="text-lg">{getStatusIcon(testStatus.openai?.status)}</span>
							<span class="text-sm text-gray-600">{testStatus.openai?.message || 'Not configured'}</span>
						</div>
					</div>

					<div class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">API Key</label>
							<input
								type="password"
								bind:value={credentials.openai.openai_api_key}
								placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							/>
						</div>
						<div class="flex space-x-4">
							<button
								on:click={() => saveCredentials('openai')}
								disabled={isLoading}
								class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
							>
								Save OpenAI Credentials
							</button>
							<button
								on:click={() => testCredentials('openai')}
								disabled={!storedCredentials.some(c => c.service_name === 'openai')}
								class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
							>
								Test Connection
							</button>
						</div>
					</div>
				</div>

				<!-- Google Credentials -->
				<div class="border border-gray-200 rounded-lg p-6">
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center space-x-3">
							<div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
								<span class="text-blue-600 font-semibold">G</span>
							</div>
							<div>
								<h4 class="text-lg font-medium text-gray-900">Google Services</h4>
								<p class="text-sm text-gray-500">Sheets logging and validation</p>
							</div>
						</div>
						<div class="flex items-center space-x-2">
							<span class="text-lg">{getStatusIcon(testStatus.google?.status)}</span>
							<span class="text-sm text-gray-600">{testStatus.google?.message || 'Not configured'}</span>
						</div>
					</div>

					<div class="space-y-4">
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-2">Project ID</label>
								<input
									type="text"
									bind:value={credentials.google.project_id}
									placeholder="your-project-id"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
								/>
							</div>
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-2">Client Email</label>
								<input
									type="email"
									bind:value={credentials.google.client_email}
									placeholder="service-account@project.iam.gserviceaccount.com"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
								/>
							</div>
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-2">Client ID</label>
								<input
									type="text"
									bind:value={credentials.google.client_id}
									placeholder="123456789012345678901"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
								/>
							</div>
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-2">Private Key ID</label>
								<input
									type="text"
									bind:value={credentials.google.private_key_id}
									placeholder="1234567890abcdef1234567890abcdef12345678"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
								/>
							</div>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">Private Key</label>
							<textarea
								bind:value={credentials.google.private_key}
								placeholder="-----BEGIN PRIVATE KEY-----&#10;...&#10;-----END PRIVATE KEY-----"
								rows="6"
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							></textarea>
						</div>
						<div class="flex space-x-4">
							<button
								on:click={() => saveCredentials('google')}
								disabled={isLoading}
								class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
							>
								Save Google Credentials
							</button>
							<button
								on:click={() => testCredentials('google')}
								disabled={!storedCredentials.some(c => c.service_name === 'google')}
								class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
							>
								Validate Structure
							</button>
						</div>
					</div>
				</div>

				{#if saveStatus}
					<div class="bg-blue-50 border border-blue-200 rounded-md p-4">
						<p class="text-blue-700">{saveStatus}</p>
					</div>
				{/if}
			</div>

		<!-- Workflow Tab -->
		{:else if activeTab === 'workflow'}
			<div class="space-y-6">
				<div>
					<h3 class="text-lg font-medium text-gray-900 mb-4">Lead Enrichment Configuration</h3>
					<p class="text-gray-600 mb-6">
						Configure and run the automated lead enrichment workflow. This will fetch leads from HubSpot, 
						enrich them using AI, validate the data, and update both HubSpot and Google Sheets.
					</p>
				</div>

				<!-- Workflow Settings -->
				<div class="border border-gray-200 rounded-lg p-6">
					<h4 class="text-md font-medium text-gray-900 mb-4">Workflow Settings</h4>
					
					<div class="space-y-4">
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-2">Max Leads to Process</label>
								<input
									type="number"
									bind:value={workflowSettings.lead_filters.limit}
									min="1"
									max="1000"
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
								/>
							</div>
							<div>
								<label class="block text-sm font-medium text-gray-700 mb-2">Lead Status Filter</label>
								<select
									bind:value={workflowSettings.lead_filters.status}
									class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
								>
									<option value="">All Statuses</option>
									<option value="new">New</option>
									<option value="contacted">Contacted</option>
									<option value="qualified">Qualified</option>
									<option value="proposal">Proposal</option>
								</select>
							</div>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Validation Threshold ({(workflowSettings.validation_threshold * 100).toFixed(0)}%)
							</label>
							<input
								type="range"
								bind:value={workflowSettings.validation_threshold}
								min="0.5"
								max="1.0"
								step="0.05"
								class="w-full"
							/>
							<p class="text-sm text-gray-500 mt-1">
								Only leads with confidence scores above this threshold will be updated in HubSpot.
							</p>
						</div>
					</div>
				</div>

				<!-- Workflow Steps Preview -->
				<div class="border border-gray-200 rounded-lg p-6">
					<h4 class="text-md font-medium text-gray-900 mb-4">Workflow Steps</h4>
					<div class="space-y-3">
						<div class="flex items-center space-x-3">
							<div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-semibold text-sm">1</div>
							<span class="text-sm">Fetch new contacts from HubSpot</span>
						</div>
						<div class="flex items-center space-x-3">
							<div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-semibold text-sm">2</div>
							<span class="text-sm">Filter leads that need enrichment</span>
						</div>
						<div class="flex items-center space-x-3">
							<div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center text-green-600 font-semibold text-sm">3</div>
							<span class="text-sm">Use OpenAI to enrich lead data</span>
						</div>
						<div class="flex items-center space-x-3">
							<div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 font-semibold text-sm">4</div>
							<span class="text-sm">Validate enriched data quality</span>
						</div>
						<div class="flex items-center space-x-3">
							<div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center text-orange-600 font-semibold text-sm">5</div>
							<span class="text-sm">Update HubSpot with enriched data</span>
						</div>
						<div class="flex items-center space-x-3">
							<div class="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 font-semibold text-sm">6</div>
							<span class="text-sm">Log results to Google Sheets</span>
						</div>
					</div>
				</div>

				<!-- Credentials Status Check -->
				<div class="border border-gray-200 rounded-lg p-6">
					<h4 class="text-md font-medium text-gray-900 mb-4">Prerequisites Check</h4>
					<div class="space-y-2">
						<div class="flex items-center justify-between">
							<span class="text-sm">HubSpot Credentials</span>
							<div class="flex items-center space-x-2">
								<span class="text-lg">{getStatusIcon(testStatus.hubspot?.status)}</span>
								<span class="text-sm {testStatus.hubspot?.status === 'success' ? 'text-green-600' : 'text-gray-500'}">
									{testStatus.hubspot?.status === 'success' ? 'Ready' : 'Required'}
								</span>
							</div>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-sm">OpenAI Credentials</span>
							<div class="flex items-center space-x-2">
								<span class="text-lg">{getStatusIcon(testStatus.openai?.status)}</span>
								<span class="text-sm {testStatus.openai?.status === 'success' ? 'text-green-600' : 'text-gray-500'}">
									{testStatus.openai?.status === 'success' ? 'Ready' : 'Required'}
								</span>
							</div>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-sm">Google Credentials</span>
							<div class="flex items-center space-x-2">
								<span class="text-lg">{getStatusIcon(testStatus.google?.status)}</span>
								<span class="text-sm {testStatus.google?.status === 'success' ? 'text-green-600' : 'text-gray-500'}">
									{testStatus.google?.status === 'success' ? 'Ready' : 'Required'}
								</span>
							</div>
						</div>
					</div>
				</div>

				<!-- Run Workflow Button -->
				<div class="flex justify-center">
					<button
						on:click={runWorkflow}
						disabled={isLoading || !areCredentialsValid()}
						class="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-lg font-medium"
					>
						{#if isLoading}
							🔄 Starting Workflow...
						{:else if areCredentialsValid()}
							🚀 Run Lead Enrichment Workflow
						{:else}
							⚠️ Complete Credentials Setup First
						{/if}
					</button>
				</div>
			</div>

		<!-- Monitor Tab -->
		{:else if activeTab === 'monitor'}
			<div class="space-y-6">
				<div>
					<h3 class="text-lg font-medium text-gray-900 mb-4">Workflow Executions</h3>
					<p class="text-gray-600 mb-6">
						Monitor the status and results of your workflow executions.
					</p>
				</div>

				{#if executions.length === 0}
					<div class="text-center py-12">
						<div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
							<span class="text-gray-400 text-2xl">📋</span>
						</div>
						<h3 class="text-lg font-medium text-gray-900 mb-2">No executions yet</h3>
						<p class="text-gray-500">Run your first workflow to see executions here.</p>
					</div>
				{:else}
					<div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
						<div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
							<h4 class="text-md font-medium text-gray-900">Recent Executions</h4>
						</div>
						<div class="divide-y divide-gray-200">
							{#each executions as execution}
								<div class="px-6 py-4">
									<div class="flex items-center justify-between">
										<div class="flex items-center space-x-4">
											<div class="flex-shrink-0">
												<div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
													<span class="text-blue-600 font-semibold text-sm">#{execution.id}</span>
												</div>
											</div>
											<div>
												<h5 class="text-sm font-medium text-gray-900">
													Lead Enrichment Workflow
												</h5>
												<div class="flex items-center space-x-4 mt-1">
													<span class="text-sm {getExecutionStatusColor(execution.status)} font-medium">
														{execution.status.toUpperCase()}
													</span>
													<span class="text-sm text-gray-500">
														Started: {formatDateTime(execution.started_at)}
													</span>
												</div>
											</div>
										</div>
										<div class="text-right">
											{#if execution.leads_processed !== null}
												<p class="text-sm text-gray-900">
													{execution.leads_enriched || 0} / {execution.leads_processed || 0} enriched
												</p>
											{/if}
											{#if execution.confidence_score}
												<p class="text-sm text-gray-500">
													{Math.round(execution.confidence_score * 100)}% confidence
												</p>
											{/if}
										</div>
									</div>
									{#if execution.error_message}
										<div class="mt-2 text-sm text-red-600 bg-red-50 rounded p-2">
											{execution.error_message}
										</div>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<div class="flex justify-center">
					<button
						on:click={loadExecutions}
						class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
					>
						🔄 Refresh Executions
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>
