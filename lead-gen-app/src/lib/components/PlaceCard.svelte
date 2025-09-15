<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import CardHeader from '$lib/components/ui/CardHeader.svelte';
	import CardTitle from '$lib/components/ui/CardTitle.svelte';
	import CardDescription from '$lib/components/ui/CardDescription.svelte';
	import CardContent from '$lib/components/ui/CardContent.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import { Star, MapPin, Phone, Globe, Check } from 'lucide-svelte';
	import type { PlaceResult } from '$lib/types';
	import { leadsStore } from '$lib/stores/leads';

	export let place: PlaceResult;
	export let compact = false;

	const dispatch = createEventDispatcher<{
		select: PlaceResult;
		save: PlaceResult;
	}>();

	let justSaved = false;
	let saveDisabled = false;

	function handleSave(event: Event) {
		event.stopPropagation();
		leadsStore.add(place);
		dispatch('save', place);
		justSaved = true;
		saveDisabled = true;
		const timer = setTimeout(() => {
			justSaved = false;
			saveDisabled = false;
			clearTimeout(timer);
		}, 1600);
	}

	function handleSelect(event: Event) {
		event.stopPropagation();
		dispatch('select', place);
	}

	function formatPhone(phone?: string) {
		if (!phone) return null;
		// Simple phone formatting for international numbers
		if (phone.startsWith('+1')) {
			return phone.replace(/^\+1/, '').replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
		}
		return phone; // Return as-is for non-US numbers
	}

	function getStatusVariant(status?: string) {
		switch (status) {
			case 'OPERATIONAL':
				return 'default';
			case 'CLOSED_TEMPORARILY':
				return 'outline';
			case 'CLOSED_PERMANENTLY':
				return 'solid';
			default:
				return 'surface';
		}
	}
</script>

<Card clickable on:click={handleSelect}>
	<CardHeader>
		<div class="flex justify-between items-start">
			<CardTitle class="text-lg">{place.displayName}</CardTitle>
			{#if place.rating}
				<div class="text-sm flex items-center gap-1">
					<Star class="w-4 h-4" alt="Rating star" />
					{place.rating} ({place.userRatingCount || 0})
				</div>
			{/if}
		</div>
		<div class="flex items-center gap-2 flex-wrap">
			{#if place.primaryTypeDisplayName}
				<Badge variant="surface" size="sm">
					{place.primaryTypeDisplayName}
				</Badge>
			{/if}
			{#if place.businessStatus}
				<Badge variant="surface" size="sm">
					{place.businessStatus.replace(/_/g, ' ').toLowerCase()}
				</Badge>
			{/if}
		</div>
	</CardHeader>

	<CardContent>
		<div class="space-y-3">
			<CardDescription>
				<div class="flex items-center gap-2">
					<MapPin class="w-4 h-4" />
					{place.formattedAddress}
				</div>
			</CardDescription>

			{#if place.editorialSummary && !compact}
				<p class="text-sm text-muted-foreground italic">
					{place.editorialSummary}
				</p>
			{/if}

			<div class="flex flex-wrap gap-2 text-sm">
				{#if place.internationalPhoneNumber}
					<span class="flex items-center gap-1">
						<Phone class="w-4 h-4" />
						{formatPhone(place.internationalPhoneNumber)}
					</span>
				{/if}
				{#if place.websiteUri}
					<a
						href={place.websiteUri}
						target="_blank"
						rel="noopener noreferrer"
						class="flex items-center gap-1 text-primary hover:underline"
					>
						<Globe class="w-4 h-4" />
						Website
					</a>
				{/if}
			</div>

			<div class="flex gap-2 pt-2 items-center flex-wrap">
				<Button variant="outline" on:click={handleSelect}>
					View
				</Button>
				<Button on:click={handleSave} disabled={saveDisabled}>
					Save Lead
				</Button>
				{#if justSaved}
					<Badge variant="surface" size="sm" aria-live="polite" class="inline-flex items-center gap-1">
						<Check class="w-4 h-4" />
						Lead saved
					</Badge>
				{/if}
			</div>
		</div>
	</CardContent>
</Card>