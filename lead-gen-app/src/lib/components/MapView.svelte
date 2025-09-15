<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';
	import { mapState, searchResults, selectedPlace } from '$lib/stores/app';
	import { initializeGoogleMaps, createMarker, geocodeLocation } from '$lib/utils/maps';
	import type { PlaceResult } from '$lib/types';

	export let apiKey: string = '';

	const dispatch = createEventDispatcher<{
		placeSelected: PlaceResult;
	}>();

	let mapContainer: HTMLElement;
	let map: any | null = null;
	let markers: any[] = [];
	let googleMaps: any | null = null;
	let isInitializing = false;

	// Only initialize when we have both apiKey and mapContainer
	$: if (browser && apiKey && mapContainer && !googleMaps && !isInitializing) {
		isInitializing = true;
		console.log('Initializing Google Maps with API key:', apiKey.substring(0, 10) + '...');
		initializeGoogleMaps(apiKey).then(maps => {
			googleMaps = maps;
			isInitializing = false;
			if (maps && mapContainer) {
				console.log('Google Maps initialized successfully');
				initializeMap();
			} else {
				console.error('Google Maps failed to initialize');
				showErrorState();
			}
		}).catch(error => {
			console.error('Google Maps initialization error:', error);
			isInitializing = false;
			showErrorState();
		});
	}

	function initializeMap() {
		if (!googleMaps || !mapContainer) {
			console.error('Cannot initialize map: missing googleMaps or mapContainer');
			return;
		}

		try {
			const { center, zoom } = $mapState;
			console.log('Creating map with center:', center, 'zoom:', zoom);

			map = new googleMaps.Map(mapContainer, {
				center,
				zoom,
				styles: [
					{
						featureType: 'all',
						elementType: 'geometry.fill',
						stylers: [{ color: '#f5f5f5' }]
					},
					{
						featureType: 'road',
						elementType: 'geometry',
						stylers: [{ color: '#ffffff' }]
					}
				]
			});

			map.addListener('bounds_changed', () => {
				if (map) {
					const center = map?.getCenter();
					if (center && map) {
						mapState.update(state => ({
							...state,
							center: { lat: center.lat(), lng: center.lng() },
							zoom: map.getZoom() || state.zoom
						}));
					}
				}
			});

			console.log('Map created successfully');
		} catch (error) {
			console.error('Error creating map:', error);
			showErrorState();
		}
	}

	function showErrorState() {
		if (mapContainer) {
			mapContainer.innerHTML = `
				<div class="w-full h-full bg-muted flex items-center justify-center">
					<div class="text-center p-4">
						<h3 class="text-lg font-semibold mb-2 text-red-600">Map Unavailable</h3>
						<p class="text-sm text-muted-foreground">Google Maps API key is required to display the map.</p>
						<p class="text-sm text-muted-foreground mt-2">Please configure your API key in the .env file.</p>
					</div>
				</div>
			`;
		}
	}

	function clearMarkers() {
		markers.forEach(marker => marker.setMap(null));
		markers = [];
	}

	function addMarkers(places: PlaceResult[]) {
		if (!googleMaps || !map) return;

		clearMarkers();

		places.forEach(place => {
			const marker = createMarker(map!, place, (selectedPlace) => {
				dispatch('placeSelected', selectedPlace);
			});
			if (marker) {
				markers.push(marker);
			}
		});

		// Fit map to show all markers
		if (markers.length > 0) {
			const bounds = new googleMaps.LatLngBounds();
			places.forEach(place => {
				bounds.extend({ lat: place.location.latitude, lng: place.location.longitude });
			});
			map.fitBounds(bounds);
		}
	}

	// React to search results changes
	$: if ($searchResults.length > 0) {
		if (map) {
			addMarkers($searchResults);
		}
	}

	// Center map on selected place
	$: if ($selectedPlace && map) {
		map.setCenter({
			lat: $selectedPlace.location.latitude,
			lng: $selectedPlace.location.longitude
		});
		map.setZoom(16);
	}
</script>

<div class="h-full w-full">
	<div bind:this={mapContainer} class="h-full w-full bg-background"></div>
</div>