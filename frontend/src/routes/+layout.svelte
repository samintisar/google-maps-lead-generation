<script>
	import '../app.css';
	
	// Accept the form prop to prevent SvelteKit warnings
	export let form = null;
</script>

<main>
	<slot />
</main>

<style>
	main {
		min-height: 100vh;
		width: 100%;
	}
</style> 