<script>
    import Chat from './Chat.svelte';
    
    let { orderId = null, hasHelper = true } = $props();
    
    let isOpen = $state(false);
    let hasUnread = $state(false);
    
    function toggleChat() {
        isOpen = !isOpen;
        if (isOpen) {
            hasUnread = false;
        }
    }
</script>

<!-- Floating Chat Container -->
<div class="fixed bottom-20 right-6 z-[100]">
    <!-- Chat Panel -->
    {#if isOpen && orderId}
        <div class="mb-4 w-80 h-96 animate-slide-up">
            {#if hasHelper}
                <Chat {orderId} onClose={() => isOpen = false} />
            {:else}
                <div class="flex flex-col h-full bg-white rounded-t-2xl shadow-soft-lg overflow-hidden">
                    <div class="bg-primary-600 text-white px-4 py-3 flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                </svg>
                            </div>
                            <p class="font-semibold text-sm">Chat</p>
                        </div>
                        <button onclick={() => isOpen = false} class="p-1 hover:bg-white/20 rounded-full transition-colors" aria-label="Close chat">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    <div class="flex-1 flex flex-col items-center justify-center p-6 text-center bg-warm-50">
                        <div class="w-16 h-16 bg-warm-200 rounded-full flex items-center justify-center mb-4">
                            <svg class="w-8 h-8 text-warm-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <p class="font-semibold text-warm-700">Waiting for a helper</p>
                        <p class="text-sm text-warm-500 mt-2">Once someone commits to help with your request, you'll be able to chat with them here.</p>
                    </div>
                </div>
            {/if}
        </div>
    {/if}
    
    <!-- Chat Button -->
    <button
        onclick={toggleChat}
        aria-label="Open chat"
        class="w-14 h-14 bg-primary-600 hover:bg-primary-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center group relative"
        class:ring-4={!isOpen}
        class:ring-primary-200={!isOpen}
    >
        {#if isOpen}
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        {:else}
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
        {/if}
        
        <!-- Tooltip -->
        {#if !isOpen && orderId}
            <span class="absolute right-full mr-3 px-3 py-1 bg-warm-800 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                {hasHelper ? 'Chat with your helper' : 'Chat (waiting for helper)'}
            </span>
        {/if}
        
        <!-- Unread indicator -->
        {#if hasUnread && !isOpen}
            <span class="absolute -top-1 -right-1 w-4 h-4 bg-accent-500 rounded-full animate-pulse"></span>
        {/if}
    </button>
</div>

<style>
    @keyframes slide-up {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .animate-slide-up {
        animation: slide-up 0.2s ease-out;
    }
</style>
