<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import SearchBar from '$lib/components/SearchBar.svelte';
	import MapView from '$lib/components/MapView.svelte';
	import ResultsList from '$lib/components/ResultsList.svelte';
	import LeadsTable from '$lib/components/LeadsTable.svelte';
	import MobileTabs from '$lib/components/MobileTabs.svelte';
	import { searchResults, selectedPlace, isLoading, activeTab, isMobile } from '$lib/stores/app';
	import { searchPlaces } from '$lib/utils/maps';
	import type { PlaceResult } from '$lib/types';

	let apiKey = '';
	let apiKeyLoaded = false;

	onMount(async () => {
		if (browser) {
			try {
				const response = await fetch('/api/config');
				if (response.ok) {
					const config = await response.json();
					apiKey = config.apiKey;
					apiKeyLoaded = true;
					console.log('API key loaded successfully');
				} else {
					console.error('Failed to load API configuration');
				}
			} catch (error) {
				console.error('Error loading API configuration:', error);
			}
		}
	});

	async function handleSearch(event: CustomEvent<{ query: string; location: string; limit: number }>) {
		const { query, location, limit } = event.detail;

		isLoading.set(true);
		try {
			const places = await searchPlaces(query, location, limit);
			searchResults.set(places);

			// Switch to results tab on mobile after search
			if ($isMobile) {
				activeTab.set('results');
			}
		} catch (error) {
			console.error('Search failed:', error);
			alert('Search failed. Please try again.');
		} finally {
			isLoading.set(false);
		}
	}

	function handlePlaceSelected(event: CustomEvent<PlaceResult>) {
		selectedPlace.set(event.detail);
	}

	function handleTabChange(event: CustomEvent<'results' | 'leads'>) {
		activeTab.set(event.detail);
	}
</script>

<svelte:head>
	<title>Google Maps Lead Generation</title>
	<meta name="description" content="Search for businesses using Google Maps and save leads for export" />
</svelte:head>

<div class="min-h-screen flex flex-col">
	<!-- Page Title -->
	<div class="bg-background border-b-2 border-foreground py-6">
		<div class="container mx-auto px-4">
			<h1 class="text-3xl lg:text-4xl font-bold text-center hover:text-primary transition-colors duration-200">Google Maps Lead Generation</h1>
		</div>
	</div>

	<!-- Header with Search -->
	<header class="flex-shrink-0">
		<SearchBar on:search={handleSearch} />
	</header>

	<!-- Main Content Area -->
	<div class="flex-1 flex overflow-hidden max-h-[calc(100vh-180px)]">
		<!-- Desktop Layout -->
		<div class="hidden md:flex w-full p-4 gap-4">
			<!-- Map Side -->
			<div class="w-1/2 border-2 border-foreground bg-background p-2">
				{#if apiKeyLoaded && apiKey}
					<div class="h-full">
						<MapView {apiKey} on:placeSelected={handlePlaceSelected} />
					</div>
				{:else}
					<div class="w-full h-full bg-muted flex items-center justify-center">
						<div class="text-center p-4">
							<h3 class="text-lg font-semibold mb-2">Loading Map...</h3>
							<p class="text-sm text-muted-foreground">Initializing Google Maps</p>
						</div>
					</div>
				{/if}
			</div>

			<!-- Results/Leads Side -->
			<div class="w-1/2 flex flex-col border-2 border-foreground bg-background">
				<!-- Tab Headers for Desktop -->
				<div class="flex border-b-2 border-foreground bg-background">
					<button
						class="flex-1 py-2 px-4 text-center font-medium border-r-2 border-foreground transition-colors {$activeTab === 'results' ? 'bg-primary text-primary-foreground' : 'bg-background text-foreground hover:bg-muted'}"
						on:click={() => activeTab.set('results')}
					>
						Results ({$searchResults.length})
					</button>
					<button
						class="flex-1 py-2 px-4 text-center font-medium transition-colors {$activeTab === 'leads' ? 'bg-primary text-primary-foreground' : 'bg-background text-foreground hover:bg-muted'}"
						on:click={() => activeTab.set('leads')}
					>
						Saved Leads
					</button>
				</div>

				<!-- Tab Content -->
				<div class="flex-1 overflow-hidden">
					{#if $activeTab === 'results'}
						<ResultsList on:placeSelected={handlePlaceSelected} />
					{:else}
						<LeadsTable />
					{/if}
				</div>
			</div>
		</div>

		<!-- Mobile Layout -->
		<div class="md:hidden flex flex-col w-full p-4 gap-4">
			<!-- Map (always visible on mobile) -->
			<div class="h-80 border-2 border-foreground bg-background p-2">
				{#if apiKeyLoaded && apiKey}
					<div class="h-full">
						<MapView {apiKey} on:placeSelected={handlePlaceSelected} />
					</div>
				{:else}
					<div class="w-full h-full bg-muted flex items-center justify-center">
						<div class="text-center p-4">
							<h3 class="text-lg font-semibold mb-2">Loading Map...</h3>
							<p class="text-sm text-muted-foreground">Initializing Google Maps</p>
						</div>
					</div>
				{/if}
			</div>

			<!-- Bottom Content (based on active tab) -->
			<div class="h-48 border-2 border-foreground bg-background">
				{#if $activeTab === 'results'}
					<ResultsList on:placeSelected={handlePlaceSelected} />
				{:else}
					<LeadsTable />
				{/if}
			</div>
		</div>
	</div>

	<!-- Mobile Tab Navigation -->
	{#if $isMobile}
		<MobileTabs on:tabChange={handleTabChange} />
	{/if}
</div>