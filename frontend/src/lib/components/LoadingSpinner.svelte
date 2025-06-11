<script lang="ts">
	interface Props {
		size?: 'sm' | 'md' | 'lg';
		message?: string;
		show?: boolean;
	}

	let { size = 'md', message = '', show = true }: Props = $props();

	// Size classes
	const sizeClasses = {
		sm: 'h-4 w-4',
		md: 'h-6 w-6',
		lg: 'h-8 w-8'
	};

	const textSizeClasses = {
		sm: 'text-sm',
		md: 'text-base',
		lg: 'text-lg'
	};
</script>

{#if show}
	<div class="flex items-center justify-center space-x-2">
		<div class="animate-spin rounded-full {sizeClasses[size]} border-2 border-gray-300 border-t-indigo-600"></div>
		{#if message}
			<span class="text-gray-600 {textSizeClasses[size]}">{message}</span>
		{/if}
	</div>
{/if} 