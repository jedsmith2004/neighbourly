<script>
    import { API_URL } from '$lib/config';
    
    let { orderId = $bindable(null), onClose = () => {} } = $props();
    
    let messages = $state([]);
    let newMessage = $state('');
    let otherUser = $state(null);
    let isLoading = $state(true);
    let error = $state(null);
    let messagesContainer = $state(null);
    let pollInterval = $state(null);
    
    async function fetchMessages() {
        if (!orderId) return;
        
        try {
            const response = await fetch(`${API_URL}/messages/${orderId}`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                messages = data.messages || [];
                otherUser = data.other_user;
                error = null;
                
                // Scroll to bottom after messages load
                setTimeout(() => {
                    if (messagesContainer) {
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    }
                }, 50);
            } else {
                const data = await response.json();
                error = data.error || 'Failed to load messages';
            }
        } catch (err) {
            error = 'Failed to connect to server';
        } finally {
            isLoading = false;
        }
    }
    
    async function sendMessage() {
        if (!newMessage.trim() || !orderId) return;
        
        try {
            const response = await fetch(`${API_URL}/send-message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    order_id: orderId,
                    content: newMessage.trim()
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                messages = [...messages, data.message];
                newMessage = '';
                
                // Scroll to bottom
                setTimeout(() => {
                    if (messagesContainer) {
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    }
                }, 50);
            }
        } catch (err) {
            console.error('Failed to send message:', err);
        }
    }
    
    function handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }
    
    function formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    }
    
    // Fetch messages when orderId changes
    $effect(() => {
        if (orderId) {
            isLoading = true;
            fetchMessages();
            
            // Poll for new messages every 3 seconds
            pollInterval = setInterval(fetchMessages, 3000);
        }
        
        return () => {
            if (pollInterval) {
                clearInterval(pollInterval);
            }
        };
    });
</script>

<div class="flex flex-col h-full bg-white rounded-t-2xl shadow-soft-lg overflow-hidden">
    <!-- Header -->
    <div class="bg-primary-600 text-white px-4 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
            </div>
            <div>
                <p class="font-semibold text-sm">
                    {#if otherUser}
                        Chat with {otherUser.name}
                    {:else}
                        Chat
                    {/if}
                </p>
            </div>
        </div>
        <button 
            onclick={onClose}
            class="p-1 hover:bg-white/20 rounded-full transition-colors"
            aria-label="Close chat"
        >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        </button>
    </div>
    
    <!-- Messages Area -->
    <div 
        bind:this={messagesContainer}
        class="flex-1 overflow-y-auto p-4 space-y-3 bg-warm-50"
    >
        {#if isLoading}
            <div class="flex items-center justify-center h-full">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
        {:else if error}
            <div class="flex items-center justify-center h-full">
                <p class="text-warm-500 text-sm">{error}</p>
            </div>
        {:else if messages.length === 0}
            <div class="flex flex-col items-center justify-center h-full text-warm-400">
                <svg class="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <p class="text-sm">No messages yet</p>
                <p class="text-xs">Start the conversation!</p>
            </div>
        {:else}
            {#each messages as message}
                <div class="flex {message.is_mine ? 'justify-end' : 'justify-start'}">
                    <div class="max-w-[75%] {message.is_mine ? 'bg-primary-600 text-white' : 'bg-white text-warm-800'} rounded-2xl px-4 py-2 shadow-sm">
                        <p class="text-sm whitespace-pre-wrap">{message.content}</p>
                        <p class="text-xs {message.is_mine ? 'text-primary-200' : 'text-warm-400'} mt-1">
                            {formatTime(message.timestamp)}
                        </p>
                    </div>
                </div>
            {/each}
        {/if}
    </div>
    
    <!-- Input Area -->
    <div class="border-t border-warm-200 bg-white p-3">
        <div class="flex items-center gap-2">
            <input
                type="text"
                bind:value={newMessage}
                onkeypress={handleKeyPress}
                placeholder="Type a message..."
                class="flex-1 px-4 py-2 bg-warm-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 text-warm-800 placeholder-warm-400"
            />
            <button
                onclick={sendMessage}
                disabled={!newMessage.trim()}
                class="p-2 bg-primary-600 text-white rounded-full hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                aria-label="Send message"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
            </button>
        </div>
    </div>
</div>
