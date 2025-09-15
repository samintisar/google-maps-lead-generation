<script lang="ts">
	export let clickable = false;

	$: classes = `border-2 border-foreground bg-background shadow-md rounded-none ${clickable ? 'cursor-pointer hover:shadow-none transition-shadow' : ''}`;
</script>

<div class={classes} on:click={clickable ? (event) => { /* Handle click */ } : undefined} {...$$restProps}>
	<slot />
</div>

<script context="module" lang="ts">
	import CardHeader from './CardHeader.svelte';
	import CardTitle from './CardTitle.svelte';
	import CardDescription from './CardDescription.svelte';
	import CardContent from './CardContent.svelte';

	export { CardHeader, CardTitle, CardDescription, CardContent };
</script>