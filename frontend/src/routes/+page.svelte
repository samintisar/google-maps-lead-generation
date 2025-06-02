<script>
	import { onMount } from 'svelte';
	import { api, API_BASE_URL } from '$lib/api.js';
	
	let healthStatus = 'Checking...';
	let models = [];
	let chatMessage = '';
	let chatResponse = '';
	let isLoading = false;
	
	// Test backend health on component mount
	onMount(async () => {
		try {
			const health = await api.health();
			healthStatus = `✅ ${health.message || 'Backend is healthy'}`;
			
			// Load available models
			const modelData = await api.models();
			models = modelData.models || [];
		} catch (error) {
			healthStatus = `❌ Backend unavailable: ${error.message}`;
		}
	});
	
	// Send chat message
	async function sendChatMessage() {
		if (!chatMessage.trim()) return;
		
		isLoading = true;
		chatResponse = '';
		
		try {
			const response = await api.chat(chatMessage);
			chatResponse = response.response || 'No response received';
		} catch (error) {
			chatResponse = `Error: ${error.message}`;
		} finally {
			isLoading = false;
		}
	}
</script>

<h1>Lead Management Automation Platform</h1>

<div class="card">
	<h2>🚀 LMA System Status</h2>
	<p>
		Node.js/Express backend with SvelteKit frontend - Testing end-to-end communication
	</p>
	
	<div class="status-section">
		<h3>Backend Health</h3>
		<p class="status">{healthStatus}</p>
		<p class="api-url">API URL: {API_BASE_URL}</p>
	</div>
	
	<div class="grid">
		<div class="service">
			<h3>🤖 Available Models</h3>
			{#if models.length > 0}
				<ul>
					{#each models as model}
						<li>{model}</li>
					{/each}
				</ul>
			{:else}
				<p>Loading models...</p>
			{/if}
		</div>
		
		<div class="service">
			<h3>💬 Chat Test</h3>
			<div class="chat-test">
				<input 
					bind:value={chatMessage} 
					placeholder="Enter a message to test chat..."
					on:keypress={(e) => e.key === 'Enter' && sendChatMessage()}
				/>
				<button on:click={sendChatMessage} disabled={isLoading}>
					{isLoading ? 'Sending...' : 'Send'}
				</button>
				{#if chatResponse}
					<div class="response">
						<strong>Response:</strong> {chatResponse}
					</div>
				{/if}
			</div>
		</div>
		
		<div class="service">
			<h3>🔗 Quick Links</h3>
			<div class="links">
				<a href="{API_BASE_URL}/api/health" target="_blank" rel="noopener">Health Check</a>
				<a href="{API_BASE_URL}/api/models" target="_blank" rel="noopener">Models API</a>
			</div>
		</div>
	</div>
</div>

<style>
	h1 {
		color: #ff3e00;
		text-align: center;
		margin-bottom: 2rem;
	}
	
	.card {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem;
		background: white;
		border-radius: 8px;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
	}
	
	.status-section {
		margin-bottom: 2rem;
		padding: 1rem;
		background: #f7fafc;
		border-radius: 6px;
		border-left: 4px solid #ff3e00;
	}
	
	.status {
		font-weight: bold;
		font-size: 1.1rem;
	}
	
	.api-url {
		color: #666;
		font-size: 0.9rem;
		margin-top: 0.5rem;
	}
	
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1.5rem;
		margin-top: 2rem;
	}
	
	.service {
		padding: 1.5rem;
		border: 1px solid #e2e8f0;
		border-radius: 6px;
	}
	
	.service h3 {
		margin-top: 0;
		color: #2d3748;
		margin-bottom: 1rem;
	}
	
	.service ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	
	.service li {
		padding: 0.5rem;
		background: #f1f5f9;
		margin-bottom: 0.5rem;
		border-radius: 4px;
	}
	
	.chat-test {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chat-test input {
		padding: 0.75rem;
		border: 1px solid #d1d5db;
		border-radius: 4px;
		font-size: 1rem;
	}
	
	.chat-test button {
		padding: 0.75rem 1.5rem;
		background: #ff3e00;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		transition: background 0.2s;
		font-size: 1rem;
	}
	
	.chat-test button:hover:not(:disabled) {
		background: #d42c00;
	}
	
	.chat-test button:disabled {
		background: #9ca3af;
		cursor: not-allowed;
	}
	
	.response {
		padding: 1rem;
		background: #ecfdf5;
		border: 1px solid #a7f3d0;
		border-radius: 4px;
		margin-top: 1rem;
	}
	
	.links {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.links a {
		display: inline-block;
		padding: 0.5rem 1rem;
		background: #ff3e00;
		color: white;
		text-decoration: none;
		border-radius: 4px;
		transition: background 0.2s;
		text-align: center;
	}
	
	.links a:hover {
		background: #d42c00;
	}
</style>
