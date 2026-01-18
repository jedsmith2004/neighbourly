<script>
	import { onMount } from 'svelte';
	import { API_URL } from '$lib/config';
	import ChatButton from '$lib/components/ChatButton.svelte';

	let isLoading = $state(true);
	let user = $state({
		email: '',
		name: '',
		picture: ''
	});
	let commitments = $state([]);
	let selectedCommitment = $state(null);
	let activeChatOrderId = $state(null);

	onMount(async () => {
		try {
			// Run auth check and commitments fetch in parallel
			const [authResponse, commitmentsResponse] = await Promise.all([
				fetch(`${API_URL}/check-auth`, { credentials: 'include' }),
				fetch(`${API_URL}/my-commitments`, { credentials: 'include' })
			]);
			
			if (!authResponse.ok) {
				window.location.href = `${API_URL}/login`;
				return;
			}

			const authData = await authResponse.json();
			
			if (!authData.authenticated) {
				window.location.href = `${API_URL}/login`;
				return;
			}

			user = {
				email: authData.email || '',
				name: authData.name || '',
				picture: authData.picture || ''
			};

			// Process commitments from parallel fetch
			if (commitmentsResponse.ok) {
				commitments = await commitmentsResponse.json();
			}
		} catch (error) {
			console.error('Error checking auth:', error);
			window.location.href = `${API_URL}/login`;
			return;
		} finally {
			isLoading = false;
		}
	});

	async function loadCommitments() {
		try {
			const response = await fetch(`${API_URL}/my-commitments`, {
				credentials: 'include'
			});
			if (response.ok) {
				commitments = await response.json();
			}
		} catch (error) {
			console.error('Error loading commitments:', error);
		}
	}

	async function cancelCommitment(orderId) {
		if (!confirm('Are you sure you want to stop helping with this request?')) return;
		
		try {
			const response = await fetch(`${API_URL}/unfulfil-request`, {
				method: 'POST',
				credentials: 'include',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ order_id: orderId })
			});
			
			if (response.ok) {
				selectedCommitment = null;
				await loadCommitments();
			} else {
				alert('Failed to cancel commitment');
			}
		} catch (error) {
			console.error('Error:', error);
			alert('An error occurred');
		}
	}

	async function markDelivered(orderId) {
		if (!confirm('Mark this request as delivered? This will complete the request.')) return;
		
		try {
			const response = await fetch(`${API_URL}/complete-commitment`, {
				method: 'POST',
				credentials: 'include',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ order_id: orderId })
			});
			
			if (response.ok) {
				selectedCommitment = null;
				await loadCommitments();
			} else {
				alert('Failed to mark as delivered');
			}
		} catch (error) {
			console.error('Error:', error);
			alert('An error occurred');
		}
	}

	function handleLogout() {
		window.location.href = `${API_URL}/logout`;
	}

	// Format time from "HHmm" to "HH:mm"
	function formatDisplayTime(time) {
		if (!time) return '';
		const str = String(time).padStart(4, '0');
		return `${str.slice(0, 2)}:${str.slice(2, 4)}`;
	}

	// Format date for display
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
			<p class="mt-4 text-warm-500">Loading account...</p>
		</div>
	</div>
{:else}
	<div class="min-h-full bg-warm-50 py-6">
		<div class="container mx-auto max-w-4xl px-4">
			<h1 class="text-3xl font-bold text-warm-900">My Account</h1>
			
			<!-- Profile Card -->
			<div class="mt-6 card">
				<div class="flex items-center gap-4">
					{#if user.picture}
						<img 
							src={user.picture} 
							alt="Profile" 
							class="h-20 w-20 rounded-2xl border-4 border-primary-100 shadow-soft"
						/>
					{:else}
						<div class="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500 to-primary-600 text-2xl font-bold text-white shadow-soft">
							{user.name ? user.name[0].toUpperCase() : user.email[0].toUpperCase()}
						</div>
					{/if}
					<div>
						<h2 class="text-xl font-bold text-warm-900">{user.name || 'Neighbour'}</h2>
						<p class="text-warm-500">{user.email}</p>
						<span class="mt-2 inline-flex items-center gap-1 text-sm text-primary-600 font-medium">
							<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
							</svg>
							Verified Account
						</span>
					</div>
				</div>
			</div>

			<!-- My Commitments (Orders I'm helping with) -->
			<div class="mt-6 card">
				<div class="flex items-center justify-between mb-4">
					<h3 class="text-lg font-bold text-warm-900 flex items-center gap-2">
						<span class="text-xl">🤝</span> My Commitments
					</h3>
					{#if commitments.length > 0}
						<span class="rounded-full bg-primary-100 px-3 py-1 text-sm font-semibold text-primary-700">{commitments.length} active</span>
					{/if}
				</div>
				
				{#if commitments.length === 0}
					<div class="text-center py-8 bg-warm-50 rounded-xl">
						<div class="text-4xl mb-3">🏠</div>
						<p class="text-warm-600 font-medium">No active commitments</p>
						<p class="text-warm-400 text-sm mt-1">You haven't volunteered to help anyone yet</p>
						<a href="/requests" data-sveltekit-reload class="btn btn-primary mt-4 inline-flex">
							Browse Requests
						</a>
					</div>
				{:else}
					<div class="space-y-4">
						{#each commitments as commitment}
							<div class="rounded-xl border-2 border-warm-200 p-4 hover:border-primary-300 transition-all bg-white">
								<div class="flex justify-between items-start gap-4">
									<div class="flex-1 min-w-0">
										<div class="flex items-center gap-2">
											<span class="text-lg">📍</span>
											<p class="font-semibold text-warm-900 truncate">{commitment.address}</p>
										</div>
										<div class="flex items-center gap-2 mt-2 text-sm text-warm-500">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
											</svg>
											{#if commitment.collectionDate}
												{formatDisplayDate(commitment.collectionDate)} at {formatDisplayTime(commitment.collectionTime)}
											{:else}
												{formatDisplayTime(commitment.collectionTime)}
											{/if}
										</div>
										{#if commitment.message}
											<p class="text-sm text-warm-600 mt-2 bg-warm-50 p-2 rounded-lg">{commitment.message}</p>
										{/if}
										<div class="mt-3">
											<p class="text-xs font-medium text-warm-400 uppercase tracking-wide mb-2">Items to collect</p>
											<div class="flex flex-wrap gap-2">
												{#each commitment.items || [] as item}
													<span class="inline-flex items-center rounded-full bg-primary-50 px-3 py-1 text-sm text-primary-700 font-medium">
														{item.name} × {item.quantity}
													</span>
												{/each}
											</div>
										</div>
									</div>
									<div class="flex flex-col gap-2">
										<button
											onclick={() => activeChatOrderId = commitment.id}
											class="btn btn-accent text-sm"
										>
											<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
											</svg>
											Chat
										</button>
										<button
											onclick={() => markDelivered(commitment.id)}
											class="btn btn-primary text-sm"
										>
											<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
											</svg>
											Delivered
										</button>
										<button
											onclick={() => cancelCommitment(commitment.id)}
											class="btn btn-secondary text-sm"
										>
											Cancel
										</button>
									</div>
								</div>
							</div>
						{/each}
					</div>
			{/if}
			</div>

			<!-- Quick Actions -->
			<div class="mt-6 card">
				<h3 class="text-lg font-bold text-warm-900 mb-4 flex items-center gap-2">
					<span class="text-xl">⚡</span> Quick Actions
				</h3>
				
				<div class="grid gap-3 sm:grid-cols-3">
					<a 
						href="/makerequest"
						data-sveltekit-reload
						class="btn btn-primary justify-center"
					>
						<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
						</svg>
						New Request
					</a>
					<a 
						href="/viewrequest"
						data-sveltekit-reload
						class="btn btn-secondary justify-center"
					>
						<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
						</svg>
						My Request
					</a>
					<a 
						href="/requests"
						data-sveltekit-reload
						class="btn btn-accent justify-center"
					>
						<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
						</svg>
						Help Others
					</a>
				</div>
			</div>

			<!-- Logout -->
			<div class="mt-6">
				<button
					onclick={handleLogout}
					class="btn btn-danger w-full justify-center"
				>
					<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
					</svg>
					Sign Out
				</button>
			</div>
		</div>
	</div>

	<!-- Chat Button for active commitment chat -->
	{#if activeChatOrderId}
		<ChatButton orderId={activeChatOrderId} />
	{/if}
{/if}
