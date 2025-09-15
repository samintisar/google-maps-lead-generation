<script lang="ts">
	export let variant: 'default' | 'outline' | 'solid' | 'surface' = 'default';
	export let size: 'sm' | 'md' | 'lg' = 'md';

	const variants = {
		default: 'bg-muted text-muted-foreground',
		outline: 'outline-2 outline-foreground text-foreground',
		solid: 'bg-foreground text-background',
		surface: 'outline-2 bg-primary text-primary-foreground'
	};

	const sizes = {
		sm: 'px-2 py-1 text-xs',
		md: 'px-2.5 py-1.5 text-sm',
		lg: 'px-3 py-2 text-base'
	};

	$: classes = `inline-flex items-center rounded-none font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${variants[variant]} ${sizes[size]}`;
</script>

<span class={classes} {...$$restProps}>
	<slot />
</span>