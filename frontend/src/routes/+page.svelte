<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth, type AuthState } from '$lib/stores/auth';
	import { get } from 'svelte/store';

	let isLoading = true;

	onMount(async () => {
		// Initialize auth and check if user is authenticated
		auth.init();
		const authState: AuthState = get(auth);
		
		// Simple check for now - will be enhanced with actual auth
		if (authState.isAuthenticated) {
			await goto('/dashboard');
		} else {
			await goto('/sign-in');
		}
		
		isLoading = false;
	});
</script>

<svelte:head>
	<title>Lead Management Automation Platform</title>
	<meta name="description" content="Comprehensive lead management ecosystem with intelligent automation" />
</svelte:head>

{#if isLoading}
	<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
		<div class="text-center">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
			<h1 class="text-2xl font-bold text-gray-900 mb-2">Lead Management Automation Platform</h1>
			<p class="text-gray-600">Loading your dashboard...</p>
		</div>
	</div>
{:else}
	<!-- Fallback content if redirect fails -->
	<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
		<div class="text-center">
			<h1 class="text-3xl font-bold text-gray-900 mb-4">Welcome to LMA Platform</h1>
			<p class="text-gray-600 mb-8">Your comprehensive lead management solution</p>
			<div class="space-x-4">
				<a href="/sign-in" class="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition-colors">
					Sign In
				</a>
				<a href="/sign-up" class="bg-white text-indigo-600 px-6 py-2 rounded-lg border border-indigo-600 hover:bg-indigo-50 transition-colors">
					Sign Up
				</a>
			</div>
		</div>
	</div>
{/if}
