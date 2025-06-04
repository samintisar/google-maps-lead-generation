<script lang="ts">
	import { onMount } from 'svelte';
	import { Layout, Card } from '$lib/components';
	import { auth } from '$lib/stores';
	import { goto } from '$app/navigation';
	import type { User } from '$lib/stores';

	let user: User | null = null;
	let isLoading = true;

	onMount(() => {
		auth.init();
		
		const unsubscribe = auth.subscribe(async ($auth) => {
			if (!$auth.isAuthenticated && !$auth.isLoading) {
				goto('/sign-in');
				return;
			}
			
			if ($auth.isAuthenticated && $auth.user) {
				user = $auth.user;
				isLoading = false;
			}
		});
		
		return unsubscribe;
	});
</script>

<Layout title="Workflows">
	<div class="max-w-4xl">
		{#if isLoading}
			<div class="flex items-center justify-center h-64">
				<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
			</div>
		{:else}
			<Card padding="large">
				<div class="text-center">
					<h2 class="text-2xl font-bold text-gray-900 mb-4">Workflow Automation</h2>
					<p class="text-gray-600">
						Powerful automation workflows will be configured and managed here.
					</p>
				</div>
			</Card>
		{/if}
	</div>
</Layout> 