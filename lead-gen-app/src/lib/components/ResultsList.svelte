<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import PlaceCard from './PlaceCard.svelte';
	import type { PlaceResult } from '$lib/types';
	import { searchResults } from '$lib/stores/app';

	const dispatch = createEventDispatcher<{
		placeSelected: PlaceResult;
	}>();

	function handlePlaceSelect(event: CustomEvent<PlaceResult>) {
		dispatch('placeSelected', event.detail);
	}
</script>

<div class="h-full overflow-y-auto bg-background">
	<div class="p-4">
		<h2 class="text-xl font-semibold mb-4 border-b-2 border-foreground pb-2">
			Search Results ({$searchResults.length})
		</h2>

		{#if $searchResults.length === 0}
			<div class="text-center py-8">
				<p class="text-muted-foreground">
					No results found. Try searching for businesses in your area.
				</p>
			</div>
		{:else}
			<div class="space-y-4">
				{#each $searchResults as place (place.id)}
					<PlaceCard
						{place}
						on:select={handlePlaceSelect}
						on:save
					/>
				{/each}
			</div>
		{/if}
	</div>
</div>