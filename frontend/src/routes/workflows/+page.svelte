<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api, leadApi, authApi } from '$lib/api';
	import { authStore } from '$lib/stores/auth';

	// UI State
	let activeTab = 'credentials';
	let isLoading = false;
	let saveStatus = '';
	let testStatus: Record<string, any> = {};
	let workflows: any[] = [];
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

	// Available workflows
	const availableWorkflows = [
		{
			id: 'lead-enrichment',
			title: 'Lead Enrichment',
			description: 'Automate lead enrichment using HubSpot, AI, and data validation. Enrich contact data with company information, job titles, and more.',
			icon: '🎯',
			category: 'Sales & Marketing',
			services: ['HubSpot', 'OpenAI', 'Google Sheets'],
			status: 'active',
			estimatedTime: '5-15 minutes',
			features: [
				'Fetch leads from HubSpot',
				'AI-powered data enrichment',
				'Data validation & confidence scoring',
				'Automatic HubSpot updates',
				'Google Sheets logging'
			]
		},
		{
			id: 'email-sequences',
			title: 'Email Sequences',
			description: 'Create and manage automated email sequences for lead nurturing and follow-ups.',
			icon: '📧',
			category: 'Sales & Marketing',
			services: ['HubSpot', 'OpenAI'],
			status: 'coming-soon',
			estimatedTime: '2-10 minutes',
			features: [
				'Personalized email templates',
				'Automated follow-up sequences',
				'Performance tracking',
				'A/B testing capabilities'
			]
		},
		{
			id: 'social-media-monitoring',
			title: 'Social Media Monitoring',
			description: 'Monitor social media mentions and engage with prospects automatically.',
			icon: '📱',
			category: 'Marketing',
			services: ['Twitter API', 'LinkedIn API', 'OpenAI'],
			status: 'coming-soon',
			estimatedTime: '3-8 minutes',
			features: [
				'Real-time mention tracking',
				'Sentiment analysis',
				'Automated responses',
				'Lead qualification'
			]
		},
		{
			id: 'google-maps-lead-gen',
			title: 'Google Maps Lead Generation',
			description: 'Scrape Google Maps for local businesses and generate high-quality leads with AI enrichment.',
			icon: '🗺️',
			category: 'Lead Generation',
			services: ['Google Maps', 'OpenAI'],
			status: 'active',
			estimatedTime: '10-30 minutes',
			features: [
				'Location-based business search',
				'Website scraping for contact info',
				'AI-powered lead enrichment',
				'Quality scoring & validation',
				'Direct CRM integration'
			]
		},
		{
			id: 'data-cleanup',
			title: 'Data Cleanup',
			description: 'Clean and standardize your CRM data with AI-powered validation and deduplication.',
			icon: '🧹',
			category: 'Data Management',
			services: ['HubSpot', 'OpenAI'],
			status: 'coming-soon',
			estimatedTime: '10-30 minutes',
			features: [
				'Duplicate detection',
				'Data standardization',
				'Missing field completion',
				'Data quality scoring'
			]
		}
	];

	onMount(async () => {
		// Check authentication
		if (!$authStore.user) {
			goto('/login');
			return;
		}
		
		// Note: This is the main workflows page that shows available workflows.
		// We don't load user-specific data (credentials, stats, executions) here.
		// That data is loaded when the user navigates to a specific workflow.
	});

	async function loadStoredCredentials() {
		try {
			const response = await api.get('/api/workflows/credentials');
			storedCredentials = response as any[];
			
			// Update status for each service
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

	function navigateToWorkflow(workflowId: string) {
		if (workflowId === 'lead-enrichment') {
			goto(`/workflows/${workflowId}`);
		} else if (workflowId === 'google-maps-lead-gen') {
			goto('/workflows/google-maps');
		} else {
			// For coming soon workflows
			alert('This workflow is coming soon! Stay tuned for updates.');
		}
	}

	function getStatusBadge(status: string) {
		switch (status) {
			case 'active':
				return 'bg-green-100 text-green-800';
			case 'coming-soon':
				return 'bg-yellow-100 text-yellow-800';
			default:
				return 'bg-gray-100 text-gray-800';
		}
	}
</script>

<svelte:head>
	<title>Workflows - LMA</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 py-8">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8">
			<h1 class="text-3xl font-bold text-gray-900">Automation Workflows</h1>
			<p class="mt-2 text-gray-600">
				Automate your sales and marketing processes with AI-powered workflows. 
				Choose from our collection of pre-built workflows or create your own.
			</p>
		</div>

		<!-- Workflow Categories -->
		<div class="mb-8">
			<div class="flex flex-wrap gap-4">
				<button class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
					All Workflows
				</button>
				<button class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors">
					Sales & Marketing
				</button>
				<button class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors">
					Lead Generation
				</button>
				<button class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors">
					Data Management
				</button>
				<button class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors">
					Marketing
				</button>
			</div>
		</div>

		<!-- Workflows Grid -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each availableWorkflows as workflow}
				<div class="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer"
					 on:click={() => navigateToWorkflow(workflow.id)}
					 on:keydown={(e) => e.key === 'Enter' && navigateToWorkflow(workflow.id)}
					 role="button"
					 tabindex="0">
					
					<!-- Workflow Header -->
					<div class="p-6">
						<div class="flex items-start justify-between mb-4">
							<div class="flex items-center space-x-3">
								<div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
									{workflow.icon}
								</div>
								<div>
									<h3 class="text-lg font-semibold text-gray-900">{workflow.title}</h3>
									<div class="flex items-center space-x-2 mt-1">
										<span class="text-xs px-2 py-1 rounded-full {getStatusBadge(workflow.status)}">
											{workflow.status === 'active' ? 'Available' : 'Coming Soon'}
										</span>
										<span class="text-xs text-gray-500">{workflow.category}</span>
									</div>
								</div>
							</div>
						</div>

						<p class="text-gray-600 text-sm mb-4 line-clamp-3">
							{workflow.description}
						</p>

						<!-- Services Used -->
						<div class="mb-4">
							<p class="text-xs font-medium text-gray-500 mb-2">INTEGRATIONS</p>
							<div class="flex flex-wrap gap-2">
								{#each workflow.services as service}
									<span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-700">
										{service}
									</span>
								{/each}
							</div>
						</div>

						<!-- Features -->
						<div class="mb-4">
							<p class="text-xs font-medium text-gray-500 mb-2">KEY FEATURES</p>
							<ul class="text-xs text-gray-600 space-y-1">
								{#each workflow.features.slice(0, 3) as feature}
									<li class="flex items-center">
										<span class="w-1 h-1 bg-blue-600 rounded-full mr-2"></span>
										{feature}
									</li>
								{/each}
								{#if workflow.features.length > 3}
									<li class="text-blue-600 font-medium">
										+{workflow.features.length - 3} more features
									</li>
								{/if}
							</ul>
						</div>

						<!-- Footer -->
						<div class="flex items-center justify-between pt-4 border-t border-gray-100">
							<div class="flex items-center text-xs text-gray-500">
								<span class="mr-1">⏱️</span>
								{workflow.estimatedTime}
							</div>
							<button class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors"
									disabled={workflow.status !== 'active'}>
								{workflow.status === 'active' ? 'Configure' : 'Preview'}
								<span class="ml-1">→</span>
							</button>
						</div>
					</div>
				</div>
			{/each}
		</div>

		<!-- Coming Soon Section -->
		<div class="mt-12 bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
			<div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
				<span class="text-blue-600 text-2xl">💡</span>
			</div>
			<h3 class="text-lg font-semibold text-gray-900 mb-2">Need a Custom Workflow?</h3>
			<p class="text-gray-600 mb-4">
				We're constantly adding new workflows. Have a specific automation need? 
				Let us know and we'll consider building it for you.
			</p>
			<button class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
				Request New Workflow
			</button>
		</div>
	</div>
</div> 