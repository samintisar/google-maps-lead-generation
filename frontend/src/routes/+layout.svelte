<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	// Initialize Chart.js components early
	import '$lib/utils/chartSetup';

	let { children } = $props();

	// Authentication initialization removed
</script>

{@render children()}
