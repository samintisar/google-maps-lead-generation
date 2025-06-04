<script>
	// This is the root component of your SvelteKit app
	// It wraps the entire application
</script>

<!-- The %sveltekit.head% and %sveltekit.body% are replaced by SvelteKit -->
<div id="svelte">
	{#if typeof document !== 'undefined'}
		<!-- Client-side rendering -->
		<slot />
	{:else}
		<!-- Server-side rendering fallback -->
		<slot />
	{/if}
</div>

<style>
	#svelte {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}
</style>
