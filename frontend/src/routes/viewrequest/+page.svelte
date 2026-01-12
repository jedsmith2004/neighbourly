<script>
	import { style } from '$lib/javascript/map';
	import { onMount, tick } from 'svelte';
	import { PUBLIC_GOOGLE_MAPS_API_KEY } from '$env/static/public';
	import { API_URL } from '$lib/config';
	import ChatButton from '$lib/components/ChatButton.svelte';

	let mapElement;
	let map;
	let isLoading = $state(true);
	let isCancelling = $state(false);
	let mapReady = $state(false);
	let order = $state({
		id: null,
		username: '',
		collectionTime: '',
		collectionDate: '',
		items: [],
		lat: 53.38182330444414,
		lng: -1.4816028478377632,
		message: '',
		address: '',
		fulfilled: null
	});

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
				if (!data.exists) {
					window.location.href = '/makerequest';
					return;
				}
			} else {
				console.error('Failed to check order existence');
			}
		} catch (error) {
			console.error('Error checking order:', error);
		}

		// Fetch user's order
		try {
			const response = await fetch(`${API_URL}/deliver-personal-order`, {
				credentials: 'include'
			});
			if (!response.ok) {
				throw new Error('Failed to fetch orders');
			}
			const orders = await response.json();

			if (orders.length > 0 && !orders[0].error) {
				order = {
					id: orders[0].id,
					username: orders[0].username || '',
					collectionTime: orders[0].collectionTime,
					collectionDate: orders[0].collectionDate,
					items: orders[0].items || [],
					lat: parseFloat(orders[0].lat),
					lng: parseFloat(orders[0].lng),
					message: orders[0].message || '',
					address: orders[0].address || '',
					fulfilled: orders[0].fulfilled
				};
			}
		} catch (error) {
			console.error('Request failed:', error);
		}

		await loadGoogleMaps();

		isLoading = false;
		
		await tick();
		if (mapReady) {
			initMap();
		}
	});

	// Loading Google Maps and Places Autocomplete API
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

	// Initialize the map centered on the order's location
	function initMap() {
		if (!mapElement || !mapReady) {
			console.error('Map element or Google Maps not ready', { mapElement, mapReady });
			return;
		}
		
		if (isNaN(order.lat) || isNaN(order.lng)) {
			console.error('Invalid lat/lng:', order.lat, order.lng);
			return;
		}
		
		const google = window.google;

		const mapOptions = {
			center: { lat: order.lat, lng: order.lng },
			zoom: 18,
			disableDefaultUI: true,
			gestureHandling: 'none', // Disable map interaction (drag, scroll zoom, etc.)
			zoomControl: false,
			draggable: false,
			scrollwheel: false,
			styles: style
		};

		map = new google.maps.Map(mapElement, mapOptions);

		new google.maps.Marker({
			position: { lat: order.lat, lng: order.lng },
			map: map
		});
	}

	function formatDisplayTime(time) {
		if (!time) return '';
		const str = String(time).padStart(4, '0');
		return `${str.slice(0, 2)}:${str.slice(2, 4)}`;
	}

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
			<p class="mt-4 text-warm-500">Loading your request...</p>
		</div>
	</div>
{:else}
	<div class="min-h-full bg-warm-50 py-6">
		<div class="container mx-auto max-w-3xl px-4">
			<div class="mb-6">
				<h1 class="text-3xl font-bold text-warm-900">Your Request</h1>
				<p class="mt-2 text-warm-500">View and manage your current request</p>
			</div>

			<!-- Status Banner -->
			{#if order.fulfilled}
				<div class="mb-6 rounded-2xl bg-success-100 border border-success-200 p-4 flex items-center gap-3">
					<div class="p-2 bg-success-500 rounded-full">
						<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
						</svg>
					</div>
					<div>
						<p class="font-semibold text-success-800">A neighbour is helping!</p>
						<p class="text-sm text-success-700">Someone has committed to help with your request</p>
					</div>
				</div>
			{:else}
				<div class="mb-6 rounded-2xl bg-accent-100 border border-accent-200 p-4 flex items-center gap-3">
					<div class="p-2 bg-accent-500 rounded-full">
						<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
						</svg>
					</div>
					<div>
						<p class="font-semibold text-accent-800">Waiting for a helper</p>
						<p class="text-sm text-accent-700">Your request is visible to neighbours nearby</p>
					</div>
				</div>
			{/if}

			<!-- Map Card -->
			<div class="card mb-6">
				<h2 class="text-lg font-semibold text-warm-900 mb-4 flex items-center gap-2">
					<span class="text-xl">📍</span> Delivery Location
				</h2>
				<div class="relative rounded-xl overflow-hidden">
					<div bind:this={mapElement} class="h-[250px] w-full bg-warm-200"></div>
				</div>
				<p class="mt-3 text-warm-700 font-medium">{order.address}</p>
			</div>

			<!-- Order Details -->
			<div class="card mb-6">
				<h2 class="text-lg font-semibold text-warm-900 mb-4 flex items-center gap-2">
					<span class="text-xl">📋</span> Request Details
				</h2>
				
				<div class="space-y-4">
					<div class="flex items-start gap-3 bg-warm-50 p-3 rounded-xl">
						<div class="p-2 bg-primary-100 rounded-lg">
							<svg class="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
							</svg>
						</div>
						<div>
							<p class="text-xs font-medium text-warm-400 uppercase tracking-wide">When</p>
							<p class="text-warm-900 font-medium">
								{#if order.collectionDate}
									{formatDisplayDate(order.collectionDate)} at {formatDisplayTime(order.collectionTime)}
								{:else}
									{formatDisplayTime(order.collectionTime)}
								{/if}
							</p>
						</div>
					</div>

					{#if order.message}
						<div class="bg-warm-50 p-3 rounded-xl">
							<p class="text-xs font-medium text-warm-400 uppercase tracking-wide mb-1">Your Message</p>
							<p class="text-warm-700">{order.message}</p>
						</div>
					{/if}
				</div>
			</div>

			<!-- Items Card -->
			<div class="card mb-6">
				<h2 class="text-lg font-semibold text-warm-900 mb-4 flex items-center gap-2">
					<span class="text-xl">🛒</span> Items Requested
				</h2>
				<div class="space-y-2">
					{#each order.items || [] as item}
						<div class="flex items-center justify-between bg-white border border-warm-200 rounded-xl px-4 py-3">
							<span class="font-medium text-warm-800">{item.name}</span>
							<span class="text-sm text-warm-500 bg-warm-100 px-2 py-1 rounded-full">×{item.quantity}</span>
						</div>
					{/each}
				</div>
			</div>

			<!-- Action Buttons -->
			<div class="space-y-3">
				<a 
					href="/account" 
					data-sveltekit-reload 
					class="btn btn-secondary w-full justify-center"
				>
					<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
					</svg>
					Back to Account
				</a>
				<button
					onclick={async () => {
						if (!confirm('Are you sure you want to cancel this request?')) return;
						isCancelling = true;
						try {
							const response = await fetch(`${API_URL}/completed-request`, {
								method: 'GET',
								credentials: 'include'
							});

							if (response.ok) {
								window.location.href = '/makerequest';
							} else {
								alert('Failed to cancel the request. Please try again.');
							}
						} catch (error) {
							console.error('Error:', error);
							alert('An error occurred. Please try again.');
						} finally {
							isCancelling = false;
						}
					}}
					disabled={isCancelling}
					class="btn btn-danger w-full justify-center"
				>
					{#if isCancelling}
						<div class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent mr-2"></div>
						Cancelling...
					{:else}
						<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
						</svg>
						Cancel Request
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Chat Button - show when there's an order -->
{#if order.id}
	<ChatButton orderId={order.id} hasHelper={!!order.fulfilled} />
{/if}