<!-- Demo Page -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	// Auto-redirect to register with demo context
	onMount(() => {
		// Add a small delay to show the demo page briefly
		setTimeout(() => {
			goto('/register?ref=demo');
		}, 2000);
	});
</script>

<svelte:head>
	<title>Demo - LMA Platform</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
	<div class="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
		<div class="text-center">
			<div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-indigo-100 mb-4">
				<svg class="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
				</svg>
			</div>
			
			<h2 class="text-2xl font-bold text-gray-900 mb-2">Demo Coming Soon</h2>
			<p class="text-gray-600 mb-6">
				We're preparing an interactive demo for you. In the meantime, start your free trial to explore the full platform.
			</p>
			
			<div class="space-y-4">
				<div class="animate-pulse">
					<div class="flex items-center justify-center">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
						<span class="ml-3 text-gray-600">Redirecting to registration...</span>
					</div>
				</div>
				
				<div class="pt-4 border-t border-gray-200">
					<p class="text-sm text-gray-500 mb-3">Or choose an option:</p>
					<div class="space-y-2">
						<a 
							href="/register" 
							class="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
						>
							Start Free Trial
						</a>
						<a 
							href="/login" 
							class="w-full flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
						>
							Sign In
						</a>
						<a 
							href="/" 
							class="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-500"
						>
							Back to Home
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>
</div> 