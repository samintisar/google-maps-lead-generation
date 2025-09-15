<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import { isLoading, searchParams } from '$lib/stores/app';

	const dispatch = createEventDispatcher<{
		search: { query: string; location: string; limit: number };
	}>();

	let query = '';
	let location = '';
	let limit = 20;

	function handleSearch() {
		if (!query.trim() || !location.trim()) return;

		searchParams.set({ query: query.trim(), location: location.trim(), limit });
		dispatch('search', { query: query.trim(), location: location.trim(), limit });
	}

	function handleKeydown(event: any) {
		if (event.key === 'Enter') {
			handleSearch();
		}
	}
</script>

<div class="w-full bg-background border-b-2 border-foreground p-2">
	<div class="max-w-4xl mx-auto">
		<div class="flex flex-col md:flex-row gap-2">
			<div class="flex-1">
				<label for="search-query" class="sr-only">Search query</label>
				<Input
					id="search-query"
					name="query"
					bind:value={query}
					placeholder="What are you looking for? (e.g., restaurants, coffee shops)"
					disabled={$isLoading}
					on:keydown={handleKeydown}
				/>
			</div>
			<div class="flex-1">
				<label for="search-location" class="sr-only">Location</label>
				<Input
					id="search-location"
					name="location"
					bind:value={location}
					placeholder="Where? (e.g., New York, NY)"
					disabled={$isLoading}
					on:keydown={handleKeydown}
				/>
			</div>
			<div class="w-full md:w-44">
				<Select
					bind:value={limit}
					disabled={$isLoading}
					options={[
						{ label: '10 leads', value: 10 },
						{ label: '20 leads', value: 20 },
						{ label: '50 leads', value: 50 },
						{ label: '100 leads', value: 100 }
					]}
				/>
			</div>
			<button
				type="button"
				class="md:w-auto w-full inline-flex items-center justify-center whitespace-nowrap font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 rounded-none shadow-[4px_4px_0_0_#000] hover:shadow-none bg-primary hover:bg-primary-hover text-primary-foreground border-2 border-foreground px-4 py-1.5"
				on:click={handleSearch}
				disabled={$isLoading || !query.trim() || !location.trim()}
			>
				{$isLoading ? 'Searching...' : 'Search'}
			</button>
		</div>
	</div>
</div>