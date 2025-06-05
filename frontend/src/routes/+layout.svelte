<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { auth } from '$lib/stores/auth';

	let { children } = $props();

	// Initialize auth on app startup
	onMount(() => {
		auth.init();
	});
</script>

{@render children()}
