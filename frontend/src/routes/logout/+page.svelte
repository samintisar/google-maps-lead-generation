<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/stores/auth';

	onMount(() => {
		// Automatically logout when this page loads
		auth.logout();
	});
</script>

<svelte:head>
	<title>Logging out... - LMA Platform</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50">
	<div class="max-w-md w-full space-y-8">
		<div class="text-center">
			<h2 class="mt-6 text-3xl font-extrabold text-gray-900">
				Logging out...
			</h2>
			<p class="mt-2 text-sm text-gray-600">
				Please wait while we log you out.
			</p>
			<div class="mt-4">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
			</div>
		</div>
	</div>
</div> 