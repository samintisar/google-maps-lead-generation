<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth, type User } from '$lib/stores';
	
	let user: User | null = null;
	let isLoading = true;
	
	onMount(() => {
		auth.init();
		
		const unsubscribe = auth.subscribe(($auth) => {
			if (!$auth.isLoading) {
				isLoading = false;
				
				if (!$auth.isAuthenticated) {
					goto('/sign-in');
					return;
				}
				
				user = $auth.user;
			}
		});
		
		return unsubscribe;
	});
</script>

{#if isLoading}
	<div class="min-h-screen bg-gray-50 flex items-center justify-center">
		<div class="text-center">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
			<p class="mt-4 text-gray-600">Loading...</p>
		</div>
	</div>
{:else if user}
	<slot />
{/if} 