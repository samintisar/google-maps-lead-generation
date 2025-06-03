<script lang="ts">
	import { onMount } from 'svelte';
	import { Layout, Card, Button } from '$lib/components';
	import { auth, leads, leadStats, type User } from '$lib/stores';
	import { api } from '$lib/api';
	import { goto } from '$app/navigation';
	import toast from 'svelte-french-toast';
	
	let user: User | null = null;
	let isLoading = true;
	let stats = {
		totalLeads: 0,
		newLeads: 0,
		qualifiedLeads: 0,
		closedWon: 0
	};
	
	async function loadDashboardData() {
		try {
			isLoading = true;
			
			// Load leads data
			const response = await api.leads.list({ limit: 100 });
			leads.setLeads(response.leads, response.total);
			
		} catch (error) {
			console.error('Failed to load dashboard data:', error);
			toast.error('Failed to load dashboard data');
		} finally {
			isLoading = false;
		}
	}
	
	// Initialize and check authentication
	onMount(() => {
		auth.init();
		
		const unsubscribe = auth.subscribe(async ($auth) => {
			if (!$auth.isAuthenticated && !$auth.isLoading) {
				goto('/login');
				return;
			}
			
			if ($auth.isAuthenticated && $auth.user) {
				user = $auth.user;
				await loadDashboardData();
			}
		});
		
		// Subscribe to lead stats for reactive updates
		const unsubscribeLeadStats = leadStats.subscribe(($stats) => {
			stats.totalLeads = $stats.total;
			stats.newLeads = $stats.byStatus.new || 0;
			stats.qualifiedLeads = $stats.byStatus.qualified || 0;
			stats.closedWon = $stats.byStatus.closed_won || 0;
		});
		
		return () => {
			unsubscribe();
			unsubscribeLeadStats();
		};
	});
	
	function getGreeting() {
		const hour = new Date().getHours();
		if (hour < 12) return 'Good morning';
		if (hour < 18) return 'Good afternoon';
		return 'Good evening';
	}
	
	const quickActions = [
		{ title: 'Add New Lead', description: 'Quickly add a new lead to your pipeline', href: '/leads/new', icon: '👤' },
		{ title: 'View All Leads', description: 'Browse and manage your lead database', href: '/leads', icon: '📋' },
		{ title: 'Run Workflow', description: 'Execute automation workflows', href: '/workflows', icon: '⚡' },
		{ title: 'View Analytics', description: 'Check your performance metrics', href: '/analytics', icon: '📊' }
	];
	
	const recentActivities = [
		{ text: 'New lead John Smith was added to the database', time: '2 minutes ago', type: 'lead' },
		{ text: 'Email campaign "Welcome Series" was executed', time: '15 minutes ago', type: 'workflow' },
		{ text: 'Lead Jane Doe moved to "Qualified" status', time: '1 hour ago', type: 'lead' },
		{ text: 'Weekly report generated successfully', time: '2 hours ago', type: 'report' }
	];
</script>

<Layout {user} title="Dashboard">
	{#if isLoading}
		<div class="flex items-center justify-center h-64">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
		</div>
	{:else}
		<!-- Welcome Section -->
		<div class="mb-8">
			<h2 class="text-2xl font-bold text-gray-900">
				{getGreeting()}, {user?.name || 'User'}! 👋
			</h2>
			<p class="mt-1 text-gray-600">
				Here's what's happening with your leads today.
			</p>
		</div>
		
		<!-- Statistics Cards -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
			<Card hover>
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
							<span class="text-white text-sm font-medium">📊</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">Total Leads</dt>
							<dd class="text-lg font-medium text-gray-900">{stats.totalLeads}</dd>
						</dl>
					</div>
				</div>
			</Card>
			
			<Card hover>
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
							<span class="text-white text-sm font-medium">🆕</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">New Leads</dt>
							<dd class="text-lg font-medium text-gray-900">{stats.newLeads}</dd>
						</dl>
					</div>
				</div>
			</Card>
			
			<Card hover>
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
							<span class="text-white text-sm font-medium">✅</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">Qualified</dt>
							<dd class="text-lg font-medium text-gray-900">{stats.qualifiedLeads}</dd>
						</dl>
					</div>
				</div>
			</Card>
			
			<Card hover>
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
							<span class="text-white text-sm font-medium">🎉</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">Closed Won</dt>
							<dd class="text-lg font-medium text-gray-900">{stats.closedWon}</dd>
						</dl>
					</div>
				</div>
			</Card>
		</div>
		
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
			<!-- Quick Actions -->
			<div>
				<h3 class="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
					{#each quickActions as action}
						<Card hover padding="medium">
							<a href={action.href} class="block">
								<div class="flex items-start">
									<span class="text-2xl mr-3">{action.icon}</span>
									<div>
										<h4 class="text-sm font-medium text-gray-900">{action.title}</h4>
										<p class="text-sm text-gray-500 mt-1">{action.description}</p>
									</div>
								</div>
							</a>
						</Card>
					{/each}
				</div>
			</div>
			
			<!-- Recent Activity -->
			<div>
				<h3 class="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
				<Card>
					<div class="flow-root">
						<ul class="-my-5 divide-y divide-gray-200">
							{#each recentActivities as activity}
								<li class="py-4">
									<div class="flex items-center space-x-4">
										<div class="flex-shrink-0">
											<div class="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
												{#if activity.type === 'lead'}
													<span class="text-gray-600">👤</span>
												{:else if activity.type === 'workflow'}
													<span class="text-gray-600">⚡</span>
												{:else if activity.type === 'report'}
													<span class="text-gray-600">📊</span>
												{:else}
													<span class="text-gray-600">📝</span>
												{/if}
											</div>
										</div>
										<div class="flex-1 min-w-0">
											<p class="text-sm text-gray-900">{activity.text}</p>
											<p class="text-sm text-gray-500">{activity.time}</p>
										</div>
									</div>
								</li>
							{/each}
						</ul>
					</div>
				</Card>
			</div>
		</div>
		
		<!-- Call to Action -->
		{#if stats.totalLeads === 0}
			<div class="mt-8">
				<Card padding="large">
					<div class="text-center">
						<h3 class="text-lg font-medium text-gray-900 mb-2">Get Started with Your First Lead</h3>
						<p class="text-gray-600 mb-6">
							Add your first lead to begin building your sales pipeline and see the power of automation.
						</p>
						<Button variant="primary" href="/leads/new">
							Add Your First Lead
						</Button>
					</div>
				</Card>
			</div>
		{/if}
	{/if}
</Layout> 