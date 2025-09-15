<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { leadsStore } from '$lib/stores/leads';
	import { isMobile } from '$lib/stores/app';

	let { children } = $props();

	onMount(() => {
		// Initialize leads from localStorage
		leadsStore.init();

		// Check for mobile screen size
		const checkMobile = () => {
			isMobile.set(window.innerWidth < 768);
		};

		checkMobile();
		window.addEventListener('resize', checkMobile);

		return () => {
			window.removeEventListener('resize', checkMobile);
		};
	});
</script>

<main class="min-h-screen bg-background">
	{@render children?.()}
</main>
