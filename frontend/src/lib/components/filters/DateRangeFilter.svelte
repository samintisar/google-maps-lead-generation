<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let startDate: string = '';
	export let endDate: string = '';
	export let disabled: boolean = false;

	const dispatch = createEventDispatcher<{
		change: { startDate: string; endDate: string };
	}>();

	// Predefined date ranges
	const presetRanges = [
		{ label: 'Last 7 days', days: 7 },
		{ label: 'Last 30 days', days: 30 },
		{ label: 'Last 3 months', days: 90 },
		{ label: 'Last 6 months', days: 180 },
		{ label: 'This year', days: 365 }
	];

	// Get date string in YYYY-MM-DD format
	function getDateString(daysBack: number): string {
		const date = new Date();
		date.setDate(date.getDate() - daysBack);
		return date.toISOString().split('T')[0];
	}

	// Handle preset selection
	function selectPreset(days: number) {
		if (disabled) return;
		
		const newEndDate = new Date().toISOString().split('T')[0];
		const newStartDate = getDateString(days);
		
		startDate = newStartDate;
		endDate = newEndDate;
		
		dispatch('change', { startDate, endDate });
	}

	// Handle manual date input
	function handleDateChange() {
		if (disabled) return;
		dispatch('change', { startDate, endDate });
	}

	// Initialize with default range (last 30 days)
	if (!startDate || !endDate) {
		startDate = getDateString(30);
		endDate = new Date().toISOString().split('T')[0];
	}
</script>

<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
		<div class="flex items-center space-x-2">
			<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
			</svg>
			<h3 class="text-sm font-medium text-gray-900">Date Range</h3>
		</div>
		
		<!-- Preset buttons -->
		<div class="flex flex-wrap gap-2">
			{#each presetRanges as range}
				<button
					type="button"
					class="px-3 py-1 text-xs font-medium rounded-full border transition-colors
						{disabled 
							? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
							: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
						}"
					on:click={() => selectPreset(range.days)}
					{disabled}
				>
					{range.label}
				</button>
			{/each}
		</div>
	</div>

	<!-- Custom date inputs -->
	<div class="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
		<div>
			<label for="start-date" class="block text-xs font-medium text-gray-700 mb-1">
				Start Date
			</label>
			<input
				id="start-date"
				type="date"
				bind:value={startDate}
				on:change={handleDateChange}
				class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md shadow-sm
					{disabled 
						? 'bg-gray-100 text-gray-400 cursor-not-allowed'
						: 'bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
					}"
				{disabled}
			/>
		</div>
		
		<div>
			<label for="end-date" class="block text-xs font-medium text-gray-700 mb-1">
				End Date
			</label>
			<input
				id="end-date"
				type="date"
				bind:value={endDate}
				on:change={handleDateChange}
				class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md shadow-sm
					{disabled 
						? 'bg-gray-100 text-gray-400 cursor-not-allowed'
						: 'bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
					}"
				{disabled}
			/>
		</div>
	</div>
</div> 