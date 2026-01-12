<script>
	import { style } from '$lib/javascript/map';
	import { onMount, tick } from 'svelte';
	import { PUBLIC_GOOGLE_MAPS_API_KEY } from '$env/static/public';
	import { API_URL } from '$lib/config';

	let mapElement;
	let map;
	let searchInputElement; // Reference to the search input element
	let pinLatLng = { lat: 53.3811, lng: -1.4701 }; // Default to Sheffield
	let isCentering = false;
	let isLoading = $state(true);
	let isSubmitting = $state(false);
	let mapReady = $state(false);

	onMount(async () => {
		try {
			const authResponse = await fetch(`${API_URL}/check-auth`, {
				credentials: 'include'
			});
			const authData = await authResponse.json();
			if (!authData.authenticated) {
				window.location.href = `${API_URL}/login`;
				return;
			}
		} catch (error) {
			console.error('Error checking auth:', error);
			window.location.href = '/';
			return;
		}

		try {
			const response = await fetch(`${API_URL}/check-order`, {
				credentials: 'include'
			});
			if (response.ok) {
				const data = await response.json();
				if (data.exists) {
					window.location.href = '/viewrequest'; // Redirect to viewrequest
					return;
				}
			} else {
				console.error('Failed to check order existence');
			}
		} catch (error) {
			console.error('Error checking order:', error);
		}

		// Pre-load Google Maps API
		await loadGoogleMaps();
		
		isLoading = false;
		
		// Wait for DOM to update, then initialize map
		await tick();
		initMap();
	});

	async function loadGoogleMaps() {
		const pkg = await import('@googlemaps/js-api-loader');
		const { Loader } = pkg;

		const loader = new Loader({
			apiKey: PUBLIC_GOOGLE_MAPS_API_KEY,
			version: 'weekly',
			libraries: ['places', 'maps']
		});

		try {
			await loader.load();
			mapReady = true;
		} catch (e) {
			console.error('Error loading Google Maps', e);
		}
	}

	function initMap() {
		if (!mapElement || !mapReady) {
			console.error('Map element or Google Maps not ready');
			return;
		}
		
		const google = window.google;

		const mapOptions = {
			center: pinLatLng,
			zoom: 12,
			disableDefaultUI: true,
			gestureHandling: 'greedy',
			styles: style
		};

		map = new google.maps.Map(mapElement, mapOptions);

		if (navigator.geolocation) {
			navigator.geolocation.getCurrentPosition(({ coords: { latitude, longitude } }) => {
				map.setCenter({ lat: latitude, lng: longitude });
				map.setZoom(16);
				new google.maps.Marker({
					map,
					position: { lat: latitude, lng: longitude }
				});
			});
		}

		initSearchBar(google);

		map.addListener('idle', () => {
			if (!isCentering) {
				const center = map.getCenter();
				pinLatLng = { lat: center.lat(), lng: center.lng() };
				updateSearchBarLocation(google);
			}
		});
	}

	function initSearchBar(google) {
		const autocomplete = new google.maps.places.Autocomplete(searchInputElement, {
			types: ['geocode'],
			componentRestrictions: { country: 'uk' }
		});

		autocomplete.addListener('place_changed', () => {
			const place = autocomplete.getPlace();
			if (place.geometry && place.geometry.location) {
				isCentering = true;
				const location = place.geometry.location;
				map.setCenter(location);
				pinLatLng = { lat: location.lat(), lng: location.lng() };
				isCentering = false;
			} else {
				alert('No location details available for the selected place.');
			}
		});
	}

	function updateSearchBarLocation(google) {
		const geocoder = new google.maps.Geocoder();

		geocoder.geocode({ location: pinLatLng }, (results, status) => {
			if (status === 'OK' && results[0]) {
				searchInputElement.value = results[0].formatted_address;
			} else {
				console.error('Error finding address: ', status);
			}
		});
	}

	let time = $state('');
	let items = $state([{ name: '', quantity: 1 }]);
	let message = $state('');
	let address = $state('');

	function addItem() {
		items = [...items, { name: '', quantity: 1 }];
	}

	function removeItem(index) {
		items = items.filter((_, i) => i !== index);
	}

	async function submitRequest() {
		isSubmitting = true;
		
		const requestData = {
			message: message,
			lat: pinLatLng.lat,
			lng: pinLatLng.lng,
			address: searchInputElement.value,
			collectionTime: formatTime(time),
			items: items
		};

		try {
			const response = await fetch(`${API_URL}/create-request`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify(requestData)
			});

			if (response.ok) {
				window.location.href = '/viewrequest';
			} else {
				console.error('Failed to submit request');
				alert('Failed to submit request. Please try again.');
			}
		} catch (error) {
			console.error('Error submitting request: ', error);
			alert('Error submitting request. Please try again.');
		} finally {
			isSubmitting = false;
		}
	}

	function formatTime(time) {
		const [hours, minutes] = time.split(':');
		return `${hours}${minutes}`;
	}
</script>

<div class="bg-warm-50 pb-8">
	{#if isLoading}
		<div class="flex h-full items-center justify-center py-20">
			<div class="text-center">
				<div class="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-primary-500 border-t-transparent"></div>
				<p class="mt-4 text-warm-500">Loading...</p>
			</div>
		</div>
	{:else}
		<div class="container mx-auto max-w-3xl p-4">
			<div class="mb-6">
				<h1 class="text-3xl font-bold text-warm-900">Create a Request</h1>
				<p class="mt-2 text-warm-500">Let your neighbours know what you need help with</p>
			</div>

			<!-- Map Card -->
			<div class="card mb-6">
				<h2 class="text-lg font-semibold text-warm-900 mb-4 flex items-center gap-2">
					<span class="text-xl">📍</span> Delivery Location
				</h2>
				
				<!-- Search Bar -->
				<div class="mb-4">
					<input
						bind:this={searchInputElement}
						type="text"
						placeholder="Search for your address..."
						class="input w-full"
					/>
				</div>

				<!-- Map Section -->
				<div class="relative rounded-xl overflow-hidden">
					<div bind:this={mapElement} class="h-[350px] w-full bg-warm-200"></div>
					<!-- Fixed Pin -->
					<div
						class="absolute left-1/2 top-1/2 z-20 -translate-x-1/2 -translate-y-1/2 transform"
						style="pointer-events: none"
					>
						<div class="flex flex-col items-center">
							<div class="rounded-full bg-primary-500 p-2 shadow-lg">
								<svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>
								</svg>
							</div>
							<div class="h-2 w-0.5 bg-primary-500"></div>
						</div>
					</div>
				</div>
			</div>

			<!-- Form Section -->
			<form onsubmit={(e) => { e.preventDefault(); submitRequest(); }} class="space-y-6">
				<!-- Message Input -->
				<div class="card">
					<h2 class="text-lg font-semibold text-warm-900 mb-4 flex items-center gap-2">
						<span class="text-xl">💬</span> Additional Details
					</h2>
					<textarea
						id="message"
						bind:value={message}
						required
						rows="3"
						class="input w-full resize-none"
						placeholder="Any special instructions or details for the helper..."
					></textarea>
				</div>

				<!-- Time Input -->
				<div class="card">
					<h2 class="text-lg font-semibold text-warm-900 mb-4 flex items-center gap-2">
						<span class="text-xl">🕐</span> When do you need this?
					</h2>
					<input
						type="time"
						id="time"
						bind:value={time}
						required
						class="input w-full"
					/>
					<p class="text-sm text-warm-400 mt-2">Set a collection time for your items</p>
				</div>

				<!-- Item List -->
				<div class="card">
					<h2 class="text-lg font-semibold text-warm-900 mb-4 flex items-center gap-2">
						<span class="text-xl">🛒</span> Items Needed
					</h2>
					
					<div class="space-y-3">
						{#each items as { name, quantity }, i}
							<div class="flex items-center gap-3">
								<input
									type="text"
									placeholder="Item name (e.g. Milk, Bread)"
									bind:value={items[i].name}
									required
									class="flex-1 px-4 py-3 rounded-xl border border-warm-200 bg-white text-warm-900 placeholder-warm-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
								/>
								<input
									type="number"
									placeholder="Qty"
									min="1"
									bind:value={items[i].quantity}
									required
									class="w-20 px-2 py-3 rounded-xl border border-warm-200 bg-white text-warm-900 placeholder-warm-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-center"
								/>
								{#if items.length > 1}
									<button
										type="button"
										onclick={() => removeItem(i)}
										class="p-2 text-warm-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
									>
										<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
										</svg>
									</button>
								{:else}
									<div class="w-9"></div>
								{/if}
							</div>
						{/each}
					</div>
					
					<button 
						type="button" 
						onclick={addItem} 
						class="mt-4 flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium transition-colors"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
						</svg>
						Add another item
					</button>
				</div>

				<!-- Submit Button -->
				<button
					type="submit"
					disabled={isSubmitting}
					class="btn btn-primary w-full py-4 text-lg"
				>
					{#if isSubmitting}
						<span class="flex items-center justify-center gap-2">
							<div class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
							Submitting...
						</span>
					{:else}
						Submit Request 🚀
					{/if}
				</button>
			</form>
		</div>
	{/if}
</div>