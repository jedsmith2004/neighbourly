<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { API_URL } from '$lib/config';
	
	let { children } = $props();
	let isAuthenticated = $state(false);
	let user = $state(null);
	let isLoading = $state(true);

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

	function handleLogout() {
		window.location.href = `${API_URL}/logout`;
	}
</script>

<div class="fixed inset-0 flex min-h-dvh flex-col bg-warm-50">
	<header class="z-50 bg-white/80 backdrop-blur-lg border-b border-warm-200">
		<div class="container mx-auto flex items-center justify-between px-4 py-3">
			<a class="flex items-center gap-2 text-2xl font-bold text-primary-600" href="/" data-sveltekit-reload>
				<span class="text-3xl">🏘️</span>
				<span>Neighbourly</span>
			</a>
			<nav class="flex items-center gap-2">
				{#if isAuthenticated}
					<a href="/makerequest" data-sveltekit-reload class="px-4 py-2 rounded-xl text-warm-600 hover:text-primary-600 hover:bg-primary-50 font-medium">
						New Request
					</a>
					<a href="/requests" data-sveltekit-reload class="px-4 py-2 rounded-xl text-warm-600 hover:text-primary-600 hover:bg-primary-50 font-medium">
						Browse
					</a>
					<a href="/account" data-sveltekit-reload class="px-4 py-2 rounded-xl text-warm-600 hover:text-primary-600 hover:bg-primary-50 font-medium">
						Account
					</a>
					<button 
						onclick={handleLogout}
						class="ml-2 btn btn-secondary"
					>
						Sign Out
					</button>
				{:else if !isLoading}
					<button 
						onclick={handleLogin}
						class="btn btn-primary"
					>
						Get Started
					</button>
				{/if}
			</nav>
		</div>
	</header>
	<main class="relative grow overflow-y-auto">
		{@render children()}
	</main>
	<footer class="z-50 bg-warm-800 py-6 text-warm-300">
		<div class="container mx-auto px-4">
			<div class="flex flex-col md:flex-row items-center justify-between gap-4">
				<div class="flex items-center gap-2">
					<span class="text-2xl">🏘️</span>
					<span class="font-semibold text-white">Neighbourly</span>
				</div>
				<p class="text-sm">Built with ❤️ by Ben, Jack, Jonathan & Nikkhil</p>
				<p class="text-sm text-warm-400">HackSheffield 9</p>
			</div>
		</div>
	</footer>
</div>
