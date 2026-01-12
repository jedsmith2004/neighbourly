<script>
	import { onMount } from 'svelte';
	import { API_URL } from '$lib/config';

	let isAuthenticated = $state(false);
	let isLoading = $state(true);
	let user = $state(null);

	onMount(async () => {
		try {
			const response = await fetch(`${API_URL}/check-auth`, {
				credentials: 'include'
			});
			const data = await response.json();
			isAuthenticated = data.authenticated;
			if (isAuthenticated) {
				user = data;
			}
		} catch (error) {
			console.error('Error checking auth:', error);
		} finally {
			isLoading = false;
		}
	});

	function handleLogin() {
		window.location.href = `${API_URL}/login`;
	}
</script>

{#if isLoading}
	<div class="flex h-full items-center justify-center bg-warm-50">
		<div class="text-center">
			<div class="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-primary-500 border-t-transparent"></div>
			<p class="mt-4 text-warm-500">Loading...</p>
		</div>
	</div>
{:else}
	<!-- Hero Section -->
	<div class="flex flex-col overflow-y-auto">
		<div class="relative flex min-h-[80vh] flex-col items-center justify-center px-4 py-20 text-center overflow-hidden">
			<!-- Background decoration -->
			<div class="absolute inset-0 bg-gradient-to-br from-primary-50 via-warm-50 to-accent-50"></div>
			<div class="absolute top-20 left-10 w-72 h-72 bg-primary-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse"></div>
			<div class="absolute bottom-20 right-10 w-72 h-72 bg-accent-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse"></div>
			
			<div class="relative z-10">
				<div class="mb-6 inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 shadow-soft">
					<span class="text-2xl">🏘️</span>
					<span class="text-sm font-medium text-warm-600">Community-powered help</span>
				</div>
				
				<h1 class="mb-6 text-5xl font-extrabold text-warm-900 md:text-7xl leading-tight">
					Help from your<br>
					<span class="bg-gradient-to-r from-primary-600 to-accent-500 bg-clip-text text-transparent">neighbours</span>
				</h1>
				
				<p class="mb-10 max-w-xl text-xl text-warm-600 leading-relaxed">
					Need groceries? A hand with something? Connect with helpful people nearby who want to make your day easier.
				</p>
				
				<div class="flex flex-col gap-4 sm:flex-row justify-center">
					<button
						onclick={handleLogin}
						class="btn btn-primary text-lg px-8 py-4 rounded-2xl"
					>
						Get Started — It's Free
					</button>
					<button
						onclick={handleLogin}
						class="btn btn-secondary text-lg px-8 py-4 rounded-2xl"
					>
						I want to help others
					</button>
				</div>
			</div>
		</div>

		<!-- How it Works Section -->
		<div class="bg-white py-20">
			<div class="container mx-auto px-4">
				<div class="text-center mb-16">
					<h2 class="text-4xl font-bold text-warm-900 mb-4">How It Works</h2>
					<p class="text-warm-500 text-lg">Three simple steps to get help from your community</p>
				</div>
				
				<div class="grid gap-8 md:grid-cols-3 max-w-5xl mx-auto">
					<div class="relative text-center p-8">
						<div class="absolute top-8 left-1/2 w-full h-0.5 bg-warm-200 -z-10 hidden md:block"></div>
						<div class="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-primary-100 text-4xl shadow-soft">
							📝
						</div>
						<span class="inline-block mb-2 text-sm font-bold text-primary-600 bg-primary-50 px-3 py-1 rounded-full">Step 1</span>
						<h3 class="mb-3 text-xl font-bold text-warm-900">Create a Request</h3>
						<p class="text-warm-500">
							Describe what you need and set your location. It only takes a minute.
						</p>
					</div>
					
					<div class="relative text-center p-8">
						<div class="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-accent-100 text-4xl shadow-soft">
							🤝
						</div>
						<span class="inline-block mb-2 text-sm font-bold text-accent-600 bg-accent-50 px-3 py-1 rounded-full">Step 2</span>
						<h3 class="mb-3 text-xl font-bold text-warm-900">Get Matched</h3>
						<p class="text-warm-500">
							Neighbours see your request and volunteer to help. You'll get notified instantly.
						</p>
					</div>
					
					<div class="relative text-center p-8">
						<div class="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-success-100 text-4xl shadow-soft">
							✨
						</div>
						<span class="inline-block mb-2 text-sm font-bold text-success-600 bg-success-50 px-3 py-1 rounded-full">Step 3</span>
						<h3 class="mb-3 text-xl font-bold text-warm-900">Receive & Thank</h3>
						<p class="text-warm-500">
							Get your items delivered and build meaningful connections in your community.
						</p>
					</div>
				</div>
			</div>
		</div>

		<!-- Features Section -->
		<div class="bg-warm-100 py-20">
			<div class="container mx-auto px-4">
				<div class="text-center mb-16">
					<h2 class="text-4xl font-bold text-warm-900 mb-4">Why Neighbourly?</h2>
					<p class="text-warm-500 text-lg">Built for real communities, by people who care</p>
				</div>
				
				<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-4 max-w-6xl mx-auto">
					<div class="card hover:shadow-soft-lg hover:-translate-y-1">
						<div class="mb-4 h-12 w-12 rounded-xl bg-primary-100 flex items-center justify-center text-2xl">🏠</div>
						<h3 class="mb-2 font-bold text-warm-900">Hyperlocal</h3>
						<p class="text-sm text-warm-500">Help and get help from people right in your neighbourhood.</p>
					</div>
					<div class="card hover:shadow-soft-lg hover:-translate-y-1">
						<div class="mb-4 h-12 w-12 rounded-xl bg-accent-100 flex items-center justify-center text-2xl">🔒</div>
						<h3 class="mb-2 font-bold text-warm-900">Trusted</h3>
						<p class="text-sm text-warm-500">Verified accounts keep your community safe and secure.</p>
					</div>
					<div class="card hover:shadow-soft-lg hover:-translate-y-1">
						<div class="mb-4 h-12 w-12 rounded-xl bg-success-100 flex items-center justify-center text-2xl">📍</div>
						<h3 class="mb-2 font-bold text-warm-900">Map View</h3>
						<p class="text-sm text-warm-500">See requests near you on an interactive map.</p>
					</div>
					<div class="card hover:shadow-soft-lg hover:-translate-y-1">
						<div class="mb-4 h-12 w-12 rounded-xl bg-primary-100 flex items-center justify-center text-2xl">💜</div>
						<h3 class="mb-2 font-bold text-warm-900">Community</h3>
						<p class="text-sm text-warm-500">Build real relationships with the people around you.</p>
					</div>
				</div>
			</div>
		</div>

		<!-- CTA Section -->
		<div class="relative py-24 text-center overflow-hidden">
			<div class="absolute inset-0 gradient-primary"></div>
			
			<div class="relative z-10 container mx-auto px-4">
				<h2 class="mb-4 text-4xl font-bold text-white">Ready to join your community?</h2>
				<p class="mb-10 text-xl text-primary-100 max-w-xl mx-auto">
					Sign up in seconds and start connecting with helpful neighbours today.
				</p>
				<button
					onclick={handleLogin}
					class="inline-flex items-center gap-2 rounded-2xl bg-white px-8 py-4 text-lg font-bold text-primary-600 shadow-soft-lg hover:shadow-xl hover:-translate-y-0.5 transition-all"
				>
					Create Free Account
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
					</svg>
				</button>
			</div>
		</div>
	</div>
{/if}
