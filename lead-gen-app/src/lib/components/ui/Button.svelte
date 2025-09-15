<script lang="ts">
	export let variant: 'default' | 'secondary' | 'outline' | 'link' | 'destructive' = 'default';
	export let size: 'sm' | 'md' | 'lg' | 'icon' = 'md';
	export let disabled = false;
	export let type: 'button' | 'submit' | 'reset' = 'button';

	const variants = {
		default: 'shadow-[4px_4px_0_0_#000] hover:shadow-none bg-primary hover:bg-primary-hover text-primary-foreground border-2 border-black transition duration-200 hover:translate-x-1 hover:translate-y-1',
		secondary: 'shadow-[4px_4px_0_0_#000] hover:shadow-none bg-secondary text-secondary-foreground border-2 border-black transition duration-200 hover:translate-x-1 hover:translate-y-1',
		outline: 'shadow-[4px_4px_0_0_#000] hover:shadow-none bg-transparent text-foreground border-2 border-black transition duration-200 hover:translate-x-1 hover:translate-y-1',
		destructive: 'shadow-[4px_4px_0_0_#000] hover:shadow-none bg-destructive text-destructive-foreground border-2 border-black transition duration-200 hover:translate-x-1 hover:translate-y-1',
		link: 'bg-transparent hover:underline text-foreground'
	};

	const sizes = {
		sm: 'px-3 py-1 text-sm shadow',
		md: 'px-4 py-1.5 text-base',
		lg: 'px-8 py-3 text-lg',
		icon: 'p-2'
	};

	$: classes = `inline-flex items-center justify-center whitespace-nowrap font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 rounded-none ${variants[variant]} ${sizes[size]}`;
</script>

<button
	{type}
	{disabled}
	class={classes}
	on:click
	{...$$restProps}
>
	<slot />
</button>