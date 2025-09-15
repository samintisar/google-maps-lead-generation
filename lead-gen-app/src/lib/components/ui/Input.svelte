<script lang="ts">
	export let value = '';
	export let placeholder = '';
	export let type = 'text';
	export let disabled = false;
	export let id = '';
	export let name = '';
	export let required = false;

	$: classes = 'flex h-10 w-full border-2 border-foreground bg-background px-3 py-2 text-sm text-foreground ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-foreground/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 rounded-none';
</script>

<input
	{id}
	{name}
	{type}
	{placeholder}
	{disabled}
	{required}
	bind:value
	class={classes}
	on:input
	on:change
	on:focus
	on:blur
	{...$$restProps}
/>