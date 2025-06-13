<script lang="ts">
	export let title: string;
	export let value: string | number;
	export let subtitle: string = '';
	export let icon: string;
	export let iconColor: string = 'text-blue-600';
	export let iconBgColor: string = 'bg-blue-100';
	export let trend: { value: number; label: string; direction: 'up' | 'down' | 'neutral' } | null = null;
	export let clickable: boolean = true;
	export let loading: boolean = false;
	export let error: string | null = null;
	
	// Drill-down data
	export let drillDownData: Array<{ label: string; value: string | number; percentage?: number }> = [];
	export const showDrillDown: boolean = false;

	// Event callbacks
	export let onclick: ((data: { title: string; value: string | number }) => void) | undefined = undefined;
	export let ondrilldown: ((data: { title: string; item: string }) => void) | undefined = undefined;

	let expanded = false;

	function handleCardClick() {
		if (!clickable || loading || error) return;
		onclick?.({ title, value });
		if (drillDownData.length > 0) {
			expanded = !expanded;
		}
	}

	function handleDrillDownClick(item: { label: string; value: string | number }) {
		ondrilldown?.({ title, item: item.label });
	}

	function formatValue(val: string | number): string {
		if (typeof val === 'number') {
			return val.toLocaleString();
		}
		return val;
	}

	function getTrendColor(direction: 'up' | 'down' | 'neutral'): string {
		switch (direction) {
			case 'up': return 'text-green-600';
			case 'down': return 'text-red-600';
			default: return 'text-gray-600';
		}
	}

	function getTrendIcon(direction: 'up' | 'down' | 'neutral'): string {
		switch (direction) {
			case 'up': return 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6';
			case 'down': return 'M13 17h8m0 0V9m0 8l-8-8-4 4-6-6';
			default: return 'M20 12H4';
		}
	}
</script>

<svelte:element 
	this={clickable ? 'button' : 'div'}
	class="bg-white rounded-lg shadow-sm border border-gray-200 transition-all duration-200 text-left
		{clickable && !loading && !error ? 'hover:shadow-md hover:border-gray-300 cursor-pointer' : ''}
		{expanded ? 'ring-2 ring-blue-500 ring-opacity-50' : ''}
		{error ? 'border-red-200 bg-red-50' : ''}"
	on:click={handleCardClick}
	on:keydown={(e: KeyboardEvent) => e.key === 'Enter' && handleCardClick()}
	role={clickable ? undefined : 'button'}
	aria-expanded={expanded}
	aria-label="{title}: {value}"
>
	<div class="p-6">
		{#if loading}
			<!-- Loading state -->
			<div class="animate-pulse">
				<div class="flex items-center justify-between">
					<div class="space-y-2">
						<div class="h-4 bg-gray-200 rounded w-24"></div>
						<div class="h-6 bg-gray-200 rounded w-16"></div>
					</div>
					<div class="w-12 h-12 bg-gray-200 rounded-full"></div>
				</div>
			</div>
		{:else if error}
			<!-- Error state -->
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-red-600">{title}</p>
					<p class="text-xs text-red-500 mt-1">{error}</p>
				</div>
				<div class="p-3 bg-red-100 rounded-full">
					<svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
					</svg>
				</div>
			</div>
		{:else}
			<!-- Normal state -->
			<div class="flex items-center justify-between">
				<div class="flex-1 min-w-0">
					<p class="text-sm font-medium text-gray-600 truncate">{title}</p>
					<p class="text-2xl font-semibold text-gray-900 mt-1">{formatValue(value)}</p>
					{#if subtitle}
						<p class="text-xs text-gray-500 mt-1">{subtitle}</p>
					{/if}
				</div>
				<div class="flex-shrink-0 ml-4">
					<div class="p-3 {iconBgColor} rounded-full">
						<svg class="w-6 h-6 {iconColor}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={icon} />
						</svg>
					</div>
				</div>
			</div>

			<!-- Trend indicator -->
			{#if trend}
				<div class="mt-3 flex items-center text-sm">
					<svg class="w-4 h-4 {getTrendColor(trend.direction)} mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getTrendIcon(trend.direction)} />
					</svg>
					<span class="{getTrendColor(trend.direction)} font-medium">
						{trend.direction === 'up' ? '+' : trend.direction === 'down' ? '-' : ''}
						{Math.abs(trend.value)}
					</span>
					<span class="text-gray-600 ml-1">{trend.label}</span>
				</div>
			{/if}

			<!-- Expand indicator -->
			{#if clickable && drillDownData.length > 0}
				<div class="mt-3 flex items-center justify-center">
					<svg 
						class="w-4 h-4 text-gray-400 transition-transform duration-200 {expanded ? 'rotate-180' : ''}" 
						fill="none" 
						stroke="currentColor" 
						viewBox="0 0 24 24"
					>
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
					</svg>
				</div>
			{/if}
		{/if}
	</div>

	<!-- Drill-down section -->
	{#if expanded && drillDownData.length > 0}
		<div class="border-t border-gray-200 px-6 py-4 bg-gray-50">
			<h4 class="text-xs font-medium text-gray-700 uppercase tracking-wide mb-3">Breakdown</h4>
			<div class="space-y-2">
				{#each drillDownData as item}
					<button
						type="button"
						class="w-full flex items-center justify-between p-2 text-sm bg-white rounded-md border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-colors"
						on:click|stopPropagation={() => handleDrillDownClick(item)}
					>
						<span class="text-gray-700 truncate">{item.label}</span>
						<div class="flex items-center space-x-2 flex-shrink-0">
							<span class="font-medium text-gray-900">{formatValue(item.value)}</span>
							{#if item.percentage !== undefined}
								<span class="text-xs text-gray-500">({item.percentage.toFixed(1)}%)</span>
							{/if}
							<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
							</svg>
						</div>
					</button>
				{/each}
			</div>
		</div>
	{/if}
</svelte:element> 