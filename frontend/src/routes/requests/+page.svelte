<script>
	import { onMount, tick } from 'svelte';
	import { Loader } from '@googlemaps/js-api-loader';
	import { PUBLIC_GOOGLE_MAPS_API_KEY } from '$env/static/public';
	import { style } from '$lib/javascript/map';
	import { API_URL } from '$lib/config';

	let isLoading = $state(true);
	let requests = $state([]);
	let selectedRequest = $state(null);
	let isFulfilling = $state(false);
	let mapReady = $state(false);
	let mapElement;
	let map;
	let markers = [];
	let searchCircle = null;
	let userLocationMarker = null;
	let userLocation = $state(null); // User's actual GPS location
	let locationLoading = $state(false);
	
	// Search center (user's location or default)
	let searchCenter = $state({ lat: 53.3811, lng: -1.4701 }); // Default to Sheffield
	let searchRadius = $state(10); // Default 10km radius
	
	// Computed: requests with distance, filtered and sorted
	let requestsWithDistance = $derived(
		requests.map(r => ({
			...r,
			distance: calculateDistance(searchCenter.lat, searchCenter.lng, r.lat, r.lng)
		}))
	);
	
	let isUnlimited = $derived(searchRadius >= 50);
	
	let filteredRequests = $derived(
		requestsWithDistance
			.filter(r => isUnlimited || r.distance <= searchRadius)
			.sort((a, b) => a.distance - b.distance)
	);

	const loader = new Loader({
		apiKey: PUBLIC_GOOGLE_MAPS_API_KEY,
		version: 'weekly',
		libraries: ['places']
	});

	onMount(async () => {
		try {
			// Start loading requests, auth check, and Google Maps in parallel
			const [authResponse, requestsResponse, _] = await Promise.all([
				fetch(`${API_URL}/check-auth`, { credentials: 'include' }),
				fetch(`${API_URL}/requests`, { credentials: 'include' }),
				loader.load() // Load Google Maps in parallel
			]);
			
			mapReady = true;
			
			if (!authResponse.ok) {
				window.location.href = `${API_URL}/login`;
				return;
			}

			const authData = await authResponse.json();
			
			if (!authData.authenticated) {
				window.location.href = `${API_URL}/login`;
				return;
			}

			// Process requests data
			if (requestsResponse.ok) {
				const data = await requestsResponse.json();
				const unfulfilledOrders = data[1] || [];
				requests = unfulfilledOrders.filter(order => !order.error).map(order => ({
					id: order.order_id,
					message: order.message,
					lat: parseFloat(order.lat),
					lng: parseFloat(order.lng),
					address: order.address,
					collectionTime: order.time,
					collectionDate: order.date,
					items: order.items || []
				}));
			}
			
			// Try to get user's location
			if (navigator.geolocation) {
				navigator.geolocation.getCurrentPosition(
					(position) => {
						userLocation = {
							lat: position.coords.latitude,
							lng: position.coords.longitude
						};
						searchCenter = { ...userLocation };
						if (map) {
							map.setCenter(searchCenter);
							updateMarkers();
							updateSearchCircle();
							updateUserLocationMarker();
						}
					},
					() => {
						// Geolocation failed, use default
						console.log('Geolocation not available, using default location');
					}
				);
			}

		} catch (error) {
			console.error('Error:', error);
		} finally {
			isLoading = false;
			// Wait for DOM to update, then initialize map
			await tick();
			initMap();
		}
	});
	
	// Calculate distance between two points in km (Haversine formula)
	function calculateDistance(lat1, lng1, lat2, lng2) {
		const R = 6371; // Earth's radius in km
		const dLat = (lat2 - lat1) * Math.PI / 180;
		const dLng = (lng2 - lng1) * Math.PI / 180;
		const a = 
			Math.sin(dLat/2) * Math.sin(dLat/2) +
			Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
			Math.sin(dLng/2) * Math.sin(dLng/2);
		const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
		return R * c;
	}
	
	// Format distance for display
	function formatDistance(km) {
		if (km < 1) {
			return `${Math.round(km * 1000)}m`;
		}
		return `${km.toFixed(1)}km`;
	}

	function initMap() {
		if (!mapElement || !mapReady) {
			console.error('Map element or Google Maps not ready');
			return;
		}
		
		map = new google.maps.Map(mapElement, {
			center: searchCenter,
			zoom: 12,
			disableDefaultUI: true,
			gestureHandling: 'greedy',
			styles: style
		});
		
		// Add markers for each request
		updateMarkers();
		updateSearchCircle();
		updateUserLocationMarker();
	}
	
	function updateUserLocationMarker() {
		if (!map) return;
		
		// Remove existing user location marker
		if (userLocationMarker) {
			userLocationMarker.setMap(null);
		}
		
		// Only show marker if we have user's location
		if (userLocation) {
			userLocationMarker = new google.maps.Marker({
				position: userLocation,
				map: map,
				title: 'Your location',
				icon: {
					path: google.maps.SymbolPath.CIRCLE,
					scale: 10,
					fillColor: '#3B82F6',
					fillOpacity: 1,
					strokeColor: '#ffffff',
					strokeWeight: 3,
				},
				zIndex: 100
			});
		}
	}
	
	function goToCurrentLocation() {
		if (!navigator.geolocation) {
			alert('Geolocation is not supported by your browser');
			return;
		}
		
		locationLoading = true;
		navigator.geolocation.getCurrentPosition(
			(position) => {
				userLocation = {
					lat: position.coords.latitude,
					lng: position.coords.longitude
				};
				searchCenter = { ...userLocation };
				
				if (map) {
					// Smooth pan to location
					map.panTo(searchCenter);
					map.setZoom(13);
					updateMarkers();
					updateSearchCircle();
					updateUserLocationMarker();
				}
				locationLoading = false;
			},
			(error) => {
				locationLoading = false;
				alert('Unable to get your location. Please check your browser permissions.');
			},
			{ enableHighAccuracy: true }
		);
	}
	
	function zoomIn() {
		if (map) {
			map.setZoom(map.getZoom() + 1);
		}
	}
	
	function zoomOut() {
		if (map) {
			map.setZoom(map.getZoom() - 1);
		}
	}
	
	function updateSearchCircle() {
		if (!map) return;
		
		// Remove existing circle
		if (searchCircle) {
			searchCircle.setMap(null);
			searchCircle = null;
		}
		
		// Don't show circle when unlimited
		if (searchRadius >= 50) return;
		
		// Create new circle
		searchCircle = new google.maps.Circle({
			strokeColor: '#10B981',
			strokeOpacity: 0.8,
			strokeWeight: 2,
			fillColor: '#10B981',
			fillOpacity: 0.1,
			map: map,
			center: searchCenter,
			radius: searchRadius * 1000 // Convert km to meters
		});
	}
	
	function handleRadiusChange(e) {
		searchRadius = parseFloat(e.target.value);
		updateMarkers();
		updateSearchCircle();
	}

	async function loadRequests() {
		const response = await fetch(`${API_URL}/requests`, {
			credentials: 'include'
		});

		if (response.ok) {
			const data = await response.json();
			// Backend returns [my_orders_list, unfulfilled_orders_list]
			// We want unfulfilled orders (index 1)
			const unfulfilledOrders = data[1] || [];
			// Filter out any error objects and ensure lat/lng are numbers
			requests = unfulfilledOrders.filter(order => !order.error).map(order => ({
				id: order.order_id,
				message: order.message,
				lat: parseFloat(order.lat),
				lng: parseFloat(order.lng),
				address: order.address,
				collectionTime: order.time,
				collectionDate: order.date,
				items: order.items,
				fulfilled: order.fulfilled
			}));
		}
	}

	function updateMarkers() {
		// Clear existing markers
		markers.forEach(marker => marker.setMap(null));
		markers = [];

		// Add new markers with color based on distance
		requestsWithDistance.forEach((request) => {
			if (request.lat && request.lng && !isNaN(request.lat) && !isNaN(request.lng)) {
				const isInRange = searchRadius >= 50 || request.distance <= searchRadius;
				const marker = new google.maps.Marker({
					position: { lat: request.lat, lng: request.lng },
					map: map,
					title: request.address,
					icon: {
						url: isInRange 
							? 'http://maps.google.com/mapfiles/ms/icons/green-dot.png'
							: 'http://maps.google.com/mapfiles/ms/icons/grey-dot.png'
					},
					zIndex: isInRange ? 10 : 1 // In-range markers on top
				});

				marker.addListener('click', () => {
					selectedRequest = request;
					map.panTo({ lat: request.lat, lng: request.lng });
				});

				markers.push(marker);
			}
		});

		// Fit bounds to show search area
		if (map && searchCircle) {
			// Optionally fit to circle bounds
		}
	}

	function selectRequest(request) {
		selectedRequest = request;
		if (map && request.lat && request.lng) {
			map.panTo({ lat: request.lat, lng: request.lng });
			map.setZoom(15);
		}
	}

	async function fulfillRequest(orderId) {
		isFulfilling = true;
		try {
			const response = await fetch(`${API_URL}/fulfil-request`, {
				method: 'POST',
				credentials: 'include',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ order_id: orderId })
			});

			if (response.ok) {
				// Close modal and refresh
				selectedRequest = null;
				await loadRequests();
				updateMarkers();
				alert('You\'ve committed to help! Check your Account page to see your commitments.');
			} else {
				const error = await response.json();
				alert(error.message || 'Failed to fulfill request');
			}
		} catch (error) {
			console.error('Error:', error);
			alert('An error occurred. Please try again.');
		} finally {
			isFulfilling = false;
		}
	}

	// Format time from "HHmm" to "HH:mm"
	function formatDisplayTime(time) {
		if (!time) return '';
		const str = String(time).padStart(4, '0');
		return `${str.slice(0, 2)}:${str.slice(2, 4)}`;
	}

	// Format date from "YYYY-MM-DD" to a readable format
	function formatDisplayDate(dateStr) {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		const today = new Date();
		const tomorrow = new Date(today);
		tomorrow.setDate(tomorrow.getDate() + 1);
		
		if (date.toDateString() === today.toDateString()) return 'Today';
		if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';
		
		return date.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });
	}
</script>

{#if isLoading}
	<div class="flex h-full items-center justify-center bg-warm-50">
		<div class="text-center">
			<div class="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-primary-500 border-t-transparent"></div>
			<p class="mt-4 text-warm-500">Loading requests...</p>
		</div>
	</div>
{:else}
	<div class="flex h-full flex-col lg:flex-row">
		<!-- Map Section -->
		<div class="h-[300px] lg:h-full lg:w-2/3 relative">
			<div bind:this={mapElement} class="h-full w-full"></div>
			<!-- Map overlay controls - Left side -->
			<div class="absolute top-4 left-4 right-4 lg:right-auto flex flex-col gap-2">
				<div class="bg-white/95 backdrop-blur-sm rounded-xl px-4 py-3 shadow-soft">
					<div class="flex items-center justify-between gap-4 mb-2">
						<span class="text-sm font-medium text-warm-700">Search Radius</span>
						<span class="text-sm font-bold text-primary-600">{isUnlimited ? 'Unlimited' : `${searchRadius}km`}</span>
					</div>
					<input 
						type="range" 
						min="1" 
						max="50" 
						value={searchRadius}
						oninput={handleRadiusChange}
						class="w-full h-2 bg-warm-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
					/>
					<div class="flex justify-between text-xs text-warm-400 mt-1">
						<span>1km</span>
						<span>∞</span>
					</div>
				</div>
				<div class="bg-white/95 backdrop-blur-sm rounded-full px-4 py-2 shadow-soft">
					<span class="text-sm font-medium text-warm-700">
						<span class="text-primary-600 font-bold">{filteredRequests.length}</span> {isUnlimited ? 'total requests' : `requests within ${searchRadius}km`}
					</span>
				</div>
			</div>
			
			<!-- Map tools - Right side -->
			<div class="absolute top-4 right-4 hidden lg:flex flex-col gap-2">
				<!-- Go to current location -->
				<button
					onclick={goToCurrentLocation}
					disabled={locationLoading}
					class="bg-white/95 backdrop-blur-sm rounded-xl p-3 shadow-soft hover:bg-white transition-colors disabled:opacity-50"
					title="Go to my location"
				>
					{#if locationLoading}
						<div class="w-5 h-5 animate-spin rounded-full border-2 border-primary-500 border-t-transparent"></div>
					{:else}
						<svg class="w-5 h-5 text-warm-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
						</svg>
					{/if}
				</button>
				
				<!-- Zoom controls -->
				<div class="bg-white/95 backdrop-blur-sm rounded-xl shadow-soft overflow-hidden">
					<button
						onclick={zoomIn}
						class="p-3 hover:bg-warm-100 transition-colors block w-full border-b border-warm-200"
						title="Zoom in"
					>
						<svg class="w-5 h-5 text-warm-700 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
						</svg>
					</button>
					<button
						onclick={zoomOut}
						class="p-3 hover:bg-warm-100 transition-colors block w-full"
						title="Zoom out"
					>
						<svg class="w-5 h-5 text-warm-700 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"/>
						</svg>
					</button>
				</div>
			</div>
			
			<!-- Mobile map tools - Bottom -->
			<div class="absolute bottom-4 right-4 flex lg:hidden gap-2">
				<button
					onclick={goToCurrentLocation}
					disabled={locationLoading}
					class="bg-white/95 backdrop-blur-sm rounded-xl p-3 shadow-soft hover:bg-white transition-colors disabled:opacity-50"
					title="Go to my location"
				>
					{#if locationLoading}
						<div class="w-5 h-5 animate-spin rounded-full border-2 border-primary-500 border-t-transparent"></div>
					{:else}
						<svg class="w-5 h-5 text-warm-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
						</svg>
					{/if}
				</button>
				<button
					onclick={zoomIn}
					class="bg-white/95 backdrop-blur-sm rounded-xl p-3 shadow-soft hover:bg-white transition-colors"
					title="Zoom in"
				>
					<svg class="w-5 h-5 text-warm-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
					</svg>
				</button>
				<button
					onclick={zoomOut}
					class="bg-white/95 backdrop-blur-sm rounded-xl p-3 shadow-soft hover:bg-white transition-colors"
					title="Zoom out"
				>
					<svg class="w-5 h-5 text-warm-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"/>
					</svg>
				</button>
			</div>
		</div>

		<!-- Sidebar -->
		<div class="flex-1 overflow-y-auto bg-warm-50 p-4 lg:w-1/3">
			<div class="mb-4">
				<h2 class="text-2xl font-bold text-warm-900 flex items-center gap-2">
					<span>🤝</span> Neighbours Need Help
				</h2>
				<p class="text-warm-500 text-sm mt-1">{isUnlimited ? 'Showing all requests' : `Showing requests within ${searchRadius}km`}, sorted by distance</p>
			</div>
			
			{#if filteredRequests.length === 0}
				<div class="text-center py-12 card">
					<div class="text-4xl mb-3">🔍</div>
					<p class="text-warm-600 font-medium">No requests in this area</p>
					<p class="text-sm text-warm-400 mt-2">Try increasing your search radius.</p>
				</div>
			{:else}
				<div class="space-y-3">
					{#each filteredRequests as request}
						<button
							onclick={() => selectRequest(request)}
							class="w-full text-left card hover:shadow-soft-lg transition-all {selectedRequest?.id === request.id ? 'ring-2 ring-primary-500 bg-primary-50' : ''}"
						>
							<div class="flex justify-between items-start gap-3">
								<div class="flex-1 min-w-0">
									<div class="flex items-center gap-2">
										<p class="font-semibold text-warm-900 truncate">{request.address}</p>
										<span class="flex-shrink-0 rounded-full bg-primary-100 px-2 py-0.5 text-xs font-semibold text-primary-700">
											{formatDistance(request.distance)}
										</span>
									</div>
									<div class="flex items-center gap-2 mt-1 text-sm text-warm-500">
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
										</svg>
										{#if request.collectionDate}
											{formatDisplayDate(request.collectionDate)} at {formatDisplayTime(request.collectionTime)}
										{:else}
											{formatDisplayTime(request.collectionTime)}
										{/if}
									</div>
									<p class="text-sm text-warm-600 mt-2 line-clamp-2">{request.message || 'No additional message'}</p>
								</div>
								<span class="flex-shrink-0 rounded-full bg-accent-100 px-3 py-1 text-xs font-semibold text-accent-700">
									{request.items?.length || 0} items
								</span>
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<!-- Selected Request Modal -->
	{#if selectedRequest}
		<div class="fixed inset-0 z-50 flex items-start justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
			<div class="w-full max-w-lg card shadow-xl animate-in fade-in zoom-in duration-200 my-auto">
				<div class="flex justify-between items-start mb-4">
					<div>
						<div class="flex items-center gap-2">
							<h3 class="text-xl font-bold text-warm-900">Request Details</h3>
							{#if selectedRequest.distance !== undefined}
								<span class="rounded-full bg-primary-100 px-2.5 py-1 text-xs font-semibold text-primary-700">
									{formatDistance(selectedRequest.distance)} away
								</span>
							{/if}
						</div>
						<p class="text-sm text-warm-500">Help your neighbour out!</p>
					</div>
					<button 
						onclick={() => selectedRequest = null}
						class="p-2 text-warm-400 hover:text-warm-600 hover:bg-warm-100 rounded-lg transition-colors"
						aria-label="Close"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
						</svg>
					</button>
				</div>

				<div class="space-y-4">
					<div class="flex items-start gap-3 bg-warm-50 p-3 rounded-xl">
						<div class="p-2 bg-primary-100 rounded-lg">
							<svg class="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
							</svg>
						</div>
						<div>
							<p class="text-xs font-medium text-warm-400 uppercase tracking-wide">Location</p>
							<p class="text-warm-900 font-medium">{selectedRequest.address}</p>
						</div>
					</div>
					
					<div class="flex items-start gap-3 bg-warm-50 p-3 rounded-xl">
						<div class="p-2 bg-accent-100 rounded-lg">
							<svg class="w-5 h-5 text-accent-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
							</svg>
						</div>
						<div>
							<p class="text-xs font-medium text-warm-400 uppercase tracking-wide">When</p>
							<p class="text-warm-900 font-medium">
								{#if selectedRequest.collectionDate}
									{formatDisplayDate(selectedRequest.collectionDate)} at {formatDisplayTime(selectedRequest.collectionTime)}
								{:else}
									{formatDisplayTime(selectedRequest.collectionTime)}
								{/if}
							</p>
						</div>
					</div>

					{#if selectedRequest.message}
						<div class="bg-warm-50 p-3 rounded-xl">
							<p class="text-xs font-medium text-warm-400 uppercase tracking-wide mb-1">Message</p>
							<p class="text-warm-700">{selectedRequest.message}</p>
						</div>
					{/if}

					<div>
						<p class="text-xs font-medium text-warm-400 uppercase tracking-wide mb-3">Items Needed</p>
						<div class="space-y-2">
							{#each selectedRequest.items || [] as item}
								<div class="flex items-center justify-between bg-white border border-warm-200 rounded-xl px-4 py-3">
									<span class="font-medium text-warm-800">{item.name}</span>
									<span class="text-sm text-warm-500 bg-warm-100 px-2 py-1 rounded-full">×{item.quantity}</span>
								</div>
							{/each}
						</div>
					</div>
				</div>

				<div class="mt-6 flex gap-3">
					<button
						onclick={() => selectedRequest = null}
						class="btn btn-secondary flex-1"
					>
						Close
					</button>
					<button
						onclick={() => fulfillRequest(selectedRequest.id)}
						disabled={isFulfilling}
						class="btn btn-primary flex-1"
					>
						{#if isFulfilling}
							<div class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent mr-2"></div>
							Committing...
						{:else}
							<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
							</svg>
							I'll Help!
						{/if}
					</button>
				</div>
			</div>
		</div>
	{/if}
{/if}

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
