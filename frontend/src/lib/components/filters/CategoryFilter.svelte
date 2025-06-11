<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let title: string = 'Filter';
	export let icon: string = 'filter';
	export let options: Array<{ value: string; label: string; count?: number }> = [];
	export let selectedValues: string[] = [];
	export let multiSelect: boolean = true;
	export let disabled: boolean = false;
	export let showCounts: boolean = true;

	const dispatch = createEventDispatcher<{
		change: { selectedValues: string[] };
	}>();

	// Handle selection changes
	function handleSelection(value: string) {
		if (disabled) return;

		let newSelectedValues: string[];
		
		if (multiSelect) {
			if (selectedValues.includes(value)) {
				newSelectedValues = selectedValues.filter(v => v !== value);
			} else {
				newSelectedValues = [...selectedValues, value];
			}
		} else {
			newSelectedValues = selectedValues.includes(value) ? [] : [value];
		}
		
		selectedValues = newSelectedValues;
		dispatch('change', { selectedValues });
	}

	// Clear all selections
	function clearAll() {
		if (disabled) return;
		selectedValues = [];
		dispatch('change', { selectedValues });
	}

	// Select all options
	function selectAll() {
		if (disabled) return;
		selectedValues = options.map(option => option.value);
		dispatch('change', { selectedValues });
	}

	// Get appropriate icon based on type
	function getIcon(iconType: string): string {
		const icons: Record<string, string> = {
			filter: 'M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z',
			status: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
			source: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1',
			users: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z',
			tag: 'M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z'
		};
		return icons[iconType] || icons.filter;
	}

	$: allSelected = selectedValues.length === options.length;
	$: someSelected = selectedValues.length > 0 && selectedValues.length < options.length;
</script>

<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
	<!-- Header -->
	<div class="flex items-center justify-between mb-4">
		<div class="flex items-center space-x-2">
			<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getIcon(icon)} />
			</svg>
			<h3 class="text-sm font-medium text-gray-900">{title}</h3>
			{#if selectedValues.length > 0}
				<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
					{selectedValues.length}
				</span>
			{/if}
		</div>

		<!-- Control buttons -->
		{#if multiSelect && options.length > 0}
			<div class="flex space-x-2">
				<button
					type="button"
					class="text-xs text-gray-500 hover:text-gray-700 {disabled ? 'cursor-not-allowed opacity-50' : ''}"
					on:click={selectAll}
					{disabled}
				>
					All
				</button>
				<span class="text-gray-300">|</span>
				<button
					type="button"
					class="text-xs text-gray-500 hover:text-gray-700 {disabled ? 'cursor-not-allowed opacity-50' : ''}"
					on:click={clearAll}
					{disabled}
				>
					None
				</button>
			</div>
		{/if}
	</div>

	<!-- Options list -->
	{#if options.length > 0}
		<div class="space-y-2 max-h-48 overflow-y-auto">
			{#each options as option}
				<label class="flex items-center space-x-2 cursor-pointer {disabled ? 'cursor-not-allowed opacity-50' : ''}">
					<input
						type={multiSelect ? 'checkbox' : 'radio'}
						class="rounded {multiSelect ? 'text-blue-600' : 'text-blue-600'} focus:ring-blue-500 focus:ring-2 {disabled ? 'cursor-not-allowed' : ''}"
						checked={selectedValues.includes(option.value)}
						on:change={() => handleSelection(option.value)}
						{disabled}
					/>
					<span class="text-sm text-gray-700 flex-1">{option.label}</span>
					{#if showCounts && option.count !== undefined}
						<span class="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
							{option.count}
						</span>
					{/if}
				</label>
			{/each}
		</div>
	{:else}
		<div class="text-sm text-gray-500 text-center py-4">
			No options available
		</div>
	{/if}

	<!-- Summary -->
	{#if selectedValues.length > 0 && multiSelect}
		<div class="mt-4 pt-3 border-t border-gray-200">
			<div class="text-xs text-gray-600">
				{selectedValues.length} of {options.length} selected
				{#if allSelected}
					<span class="text-green-600 font-medium">(All)</span>
				{:else if someSelected}
					<span class="text-blue-600 font-medium">(Partial)</span>
				{/if}
			</div>
		</div>
	{/if}
</div> 