<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';

	// Voice Agent State
	let isConnected = false;
	let currentStep = 'greeting';
	let conversationActive = false;

	// Conversation Data
	let transcript: Array<{
		id: string;
		timestamp: string;
		speaker: 'user' | 'agent' | 'system';
		message: string;
	}> = [];
	
	// Lead Qualification Data
	let leadData = {
		name: '',
		email: '',
		company: '',
		industry: '',
		employeeCount: '',
		currentChallenges: '',
		timeline: '',
		budget: '',
		phone: '',
		preferredMeetingTime: ''
	};

	// ElevenLabs Settings (placeholder - user will provide credentials later)
	let elevenLabsSettings = {
		apiKey: '', // Will be provided by user
		voiceId: 'EXAVITQu4vr4xnSDxMaL', // Bella voice
		model: 'eleven_turbo_v2'
	};

	// Demo Configuration
	let demoConfig = {
		companyName: 'LMA Automation',
		agentName: 'Sarah',
		services: [
			'Lead enrichment automation',
			'Google Maps lead generation', 
			'Email sequence automation',
			'Social media monitoring',
			'CRM data cleanup'
		],
		pricingTiers: [
			{ name: 'Starter', price: '$299/month', leads: '500 leads/month' },
			{ name: 'Growth', price: '$599/month', leads: '2,000 leads/month' },
			{ name: 'Enterprise', price: 'Custom', leads: 'Unlimited leads' }
		]
	};

	// Text Input for Demo
	let textInput = '';

	// Calendar Integration
	let availableSlots = [
		{ date: '2024-12-20', time: '10:00 AM', available: true },
		{ date: '2024-12-20', time: '2:00 PM', available: true },
		{ date: '2024-12-21', time: '11:00 AM', available: true },
		{ date: '2024-12-21', time: '3:00 PM', available: false },
		{ date: '2024-12-23', time: '9:00 AM', available: true },
		{ date: '2024-12-23', time: '1:00 PM', available: true }
	];

	onMount(() => {
		// Start with a greeting
		setTimeout(() => {
			startConversation();
		}, 1000);
	});

	function startConversation() {
		conversationActive = true;
		isConnected = true;
		const greeting = `Hello! I'm ${demoConfig.agentName}, your AI sales assistant for ${demoConfig.companyName}. I'm here to help you learn about our automation solutions and answer any questions you might have. How can I assist you today?`;
		
		addTranscriptEntry('agent', greeting);
		currentStep = 'greeting';
	}

	function handleUserInput(text: string) {
		addTranscriptEntry('user', text);
		
		// Process the input and generate response
		setTimeout(() => {
			processUserInput(text.toLowerCase());
		}, 500);
	}

	function processUserInput(input: string) {
		let response = '';
		
		// FAQ Detection
		if (input.includes('price') || input.includes('cost') || input.includes('pricing')) {
			response = generatePricingResponse();
			currentStep = 'faq';
		} else if (input.includes('demo') || input.includes('meeting') || input.includes('call')) {
			response = generateBookingResponse();
			currentStep = 'booking';
		} else if (input.includes('service') || input.includes('what do you do') || input.includes('offer')) {
			response = generateServicesResponse();
			currentStep = 'faq';
		} else if (input.includes('how long') || input.includes('implementation') || input.includes('setup')) {
			response = generateTimelineResponse();
			currentStep = 'faq';
		} else if (input.includes('help') || input.includes('support')) {
			response = generateSupportResponse();
			currentStep = 'faq';
		} else if (currentStep === 'greeting' || currentStep === 'faq') {
			response = generateQualificationResponse();
			currentStep = 'qualifying';
		} else if (currentStep === 'qualifying') {
			response = extractLeadInfo(input);
		} else if (currentStep === 'booking') {
			response = handleBookingProcess(input);
		} else {
			response = generateFallbackResponse();
		}

		addTranscriptEntry('agent', response);
	}

	function generatePricingResponse(): string {
		return `Great question! We offer three pricing tiers to fit different business needs. Our Starter plan is $299 per month for up to 500 leads, our Growth plan is $599 per month for up to 2,000 leads, and we also have custom Enterprise solutions. Each plan includes our full automation suite. Would you like me to tell you more about what's included, or would you prefer to schedule a demo to see the platform in action?`;
	}

	function generateServicesResponse(): string {
		return `${demoConfig.companyName} specializes in sales and marketing automation. Our main services include automated lead enrichment from your CRM, Google Maps lead generation for local businesses, intelligent email sequence automation, social media monitoring and engagement, and CRM data cleanup and standardization. We use AI to make these processes incredibly efficient. Which of these areas interests you most for your business?`;
	}

	function generateTimelineResponse(): string {
		return `That's a great question! Our typical implementation timeline is quite fast. For most clients, we can have basic lead enrichment running within 24-48 hours, and our complete automation suite deployed within 1-2 weeks. This includes data integration, workflow configuration, and team training. The exact timeline depends on your current systems and data complexity. What's your ideal timeline for getting started?`;
	}

	function generateSupportResponse(): string {
		return `We provide comprehensive support including 24/7 technical assistance, dedicated account management, training sessions for your team, and ongoing optimization recommendations. We also have extensive documentation and video tutorials. Is there a specific area you'd like support with, or would you like me to connect you with our technical team?`;
	}

	function generateBookingResponse(): string {
		return `I'd love to schedule a personalized demo for you! Our demos typically last 30 minutes and include a live walkthrough of our automation platform, discussion of your specific needs, and a custom strategy session. I have several slots available this week. Would you prefer morning or afternoon, and what days work best for you?`;
	}

	function generateQualificationResponse(): string {
		return `Perfect! To help me provide the most relevant information, could you tell me a bit about your business? Specifically, what industry are you in, and what are your biggest challenges with lead generation or sales processes right now?`;
	}

	function extractLeadInfo(input: string): string {
		// Extract information from user input
		if (input.includes('@')) {
			const emailMatch = input.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
			if (emailMatch) {
				leadData.email = emailMatch[0];
			}
		}
		
		// Industry detection
		const industries = ['technology', 'healthcare', 'finance', 'retail', 'manufacturing', 'real estate', 'education', 'consulting'];
		for (const industry of industries) {
			if (input.includes(industry)) {
				leadData.industry = industry;
				break;
			}
		}

		// Company size detection
		if (input.includes('employee') || input.includes('people') || input.includes('team')) {
			const numberMatch = input.match(/(\d+)/);
			if (numberMatch) {
				leadData.employeeCount = numberMatch[0];
			}
		}

		return `Thanks for sharing that information! Based on what you've told me about your ${leadData.industry || 'business'}, I think our automation platform could really help streamline your processes. Would you like to see a quick demo of how we've helped similar companies, or do you have specific questions about integration with your current systems?`;
	}

	function handleBookingProcess(input: string): string {
		if (input.includes('morning')) {
			return `Perfect! I have morning slots available on December 20th at 10 AM and December 23rd at 9 AM. Which would work better for you? I'll also need your email address to send the calendar invitation.`;
		} else if (input.includes('afternoon')) {
			return `Great! I have afternoon slots on December 20th at 2 PM and December 23rd at 1 PM. Which time works best? And could you provide your email so I can send the meeting details?`;
		} else if (input.includes('@')) {
			const emailMatch = input.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
			if (emailMatch) {
				leadData.email = emailMatch[0];
				return `Perfect! I've captured your email as ${emailMatch[0]}. I'll send you a calendar invitation shortly. Is there anything specific you'd like me to prepare for our demo, or any particular workflows you're most interested in seeing?`;
			}
		}
		return `I'd be happy to help you schedule that demo. What time of day works best for you, and could you share your email address so I can send the meeting invitation?`;
	}

	function generateFallbackResponse(): string {
		return `I understand your question, but I think it might be best handled by one of our human specialists who can give you a more detailed answer. Would you like me to transfer you to a member of our sales team, or would you prefer to leave a message and have someone call you back within the next few hours?`;
	}

	function addTranscriptEntry(speaker: 'user' | 'agent' | 'system', message: string) {
		const entry = {
			id: Date.now().toString(),
			timestamp: new Date().toLocaleTimeString(),
			speaker,
			message
		};
		transcript = [...transcript, entry];
		
		// Scroll to bottom of transcript
		setTimeout(() => {
			const transcriptElement = document.getElementById('transcript-container');
			if (transcriptElement) {
				transcriptElement.scrollTop = transcriptElement.scrollHeight;
			}
		}, 100);
	}

	function handleTextSubmit() {
		if (textInput.trim()) {
			handleUserInput(textInput.trim());
			textInput = '';
		}
	}

	function clearTranscript() {
		transcript = [];
	}

	function restartConversation() {
		clearTranscript();
		leadData = {
			name: '',
			email: '',
			company: '',
			industry: '',
			employeeCount: '',
			currentChallenges: '',
			timeline: '',
			budget: '',
			phone: '',
			preferredMeetingTime: ''
		};
		currentStep = 'greeting';
		conversationActive = false;
		isConnected = false;
		
		setTimeout(() => {
			startConversation();
		}, 1000);
	}

	function exportTranscript() {
		const transcriptText = transcript
			.map(entry => `[${entry.timestamp}] ${entry.speaker.toUpperCase()}: ${entry.message}`)
			.join('\n');
		
		const blob = new Blob([transcriptText], { type: 'text/plain' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `voice-agent-transcript-${new Date().toISOString().slice(0, 10)}.txt`;
		a.click();
		URL.revokeObjectURL(url);
	}

	// Reactive updates for lead data visualization
	$: leadProgress = Object.values(leadData).filter(value => value && value.trim()).length;
	$: totalLeadFields = Object.keys(leadData).length;
	$: qualificationPercentage = Math.round((leadProgress / totalLeadFields) * 100);
</script>

<svelte:head>
	<title>AI Voice Sales Agent Demo - LMA</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 py-8">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8">
			<div class="flex items-center justify-between">
				<div>
					<div class="flex items-center space-x-3 mb-2">
						<div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
							🎤
						</div>
						<div>
							<h1 class="text-3xl font-bold text-gray-900">AI Voice Sales Agent</h1>
							<p class="text-gray-600">Interactive demo of customizable voice AI for sales calls</p>
						</div>
					</div>
				</div>
				<div class="flex items-center space-x-4">
					<div class="flex items-center space-x-2">
						<div class="w-3 h-3 rounded-full {isConnected ? 'bg-green-500' : 'bg-red-500'}"></div>
						<span class="text-sm text-gray-600">{isConnected ? 'Connected' : 'Disconnected'}</span>
					</div>
					<button 
						on:click={restartConversation}
						class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
						Restart Demo
					</button>
				</div>
			</div>
		</div>

		<!-- Demo Introduction -->
		<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
			<h2 class="text-xl font-semibold text-gray-900 mb-4">🚀 Voice Agent Capabilities Demo</h2>
			<div class="grid md:grid-cols-2 gap-6">
				<div>
					<h3 class="font-medium text-gray-900 mb-2">What This Agent Can Do:</h3>
					<ul class="text-sm text-gray-600 space-y-1">
						<li class="flex items-center"><span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>Answer sales FAQs about services & pricing</li>
						<li class="flex items-center"><span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>Qualify leads by asking relevant questions</li>
						<li class="flex items-center"><span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>Schedule demo calls & collect contact info</li>
						<li class="flex items-center"><span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>Handle objections & provide solutions</li>
						<li class="flex items-center"><span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>Transfer to humans for complex questions</li>
					</ul>
				</div>
				<div>
					<h3 class="font-medium text-gray-900 mb-2">Customization Options:</h3>
					<ul class="text-sm text-gray-600 space-y-1">
						<li class="flex items-center"><span class="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>Voice personality & tone adjustment</li>
						<li class="flex items-center"><span class="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>Industry-specific knowledge base</li>
						<li class="flex items-center"><span class="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>Custom qualification questions</li>
						<li class="flex items-center"><span class="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>CRM & calendar integration</li>
						<li class="flex items-center"><span class="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>Multi-language support</li>
					</ul>
				</div>
			</div>
		</div>

		<!-- Main Demo Interface -->
		<div class="grid lg:grid-cols-3 gap-8">
			<!-- Voice Interface Panel -->
			<div class="lg:col-span-2">
				<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<div class="flex items-center justify-between mb-6">
						<h2 class="text-xl font-semibold text-gray-900">Voice Conversation</h2>
						<div class="flex items-center space-x-2">
							<span class="px-3 py-1.5 text-sm bg-blue-50 border border-blue-300 text-blue-700 rounded-md">
								🎤 ElevenLabs Integration Ready
							</span>
						</div>
					</div>

					<!-- ElevenLabs Widget Placeholder -->
					<div class="mb-6 p-6 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
						<div class="text-center">
							<div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
								<span class="text-blue-600 text-2xl">🎤</span>
							</div>
							<h3 class="text-lg font-medium text-gray-900 mb-2">ElevenLabs Voice Widget</h3>
							<p class="text-gray-600 mb-4">
								This is where the ElevenLabs voice widget will be integrated. 
								The widget will handle real-time voice conversations with the AI agent.
							</p>
							<div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
								<p class="text-sm text-blue-800">
									<strong>Integration Notes:</strong> Add your ElevenLabs widget code here. 
									The conversation logic below will handle the AI responses and lead qualification.
								</p>
							</div>
						</div>
					</div>

					<!-- Text Input for Testing -->
					<div class="mb-6 p-4 bg-gray-50 rounded-lg">
						<h4 class="font-medium text-gray-900 mb-3">Test Conversation (Text Mode)</h4>
						<div class="flex space-x-3">
							<input
								bind:value={textInput}
								on:keydown={(e) => e.key === 'Enter' && handleTextSubmit()}
								placeholder="Type your message here to test the conversation logic..."
								class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							/>
							<button
								on:click={handleTextSubmit}
								disabled={!textInput.trim() || !conversationActive}
								class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed">
								Send
							</button>
						</div>
					</div>

					<!-- Conversation Transcript -->
					<div class="border border-gray-200 rounded-lg">
						<div class="flex items-center justify-between p-3 bg-gray-50 border-b border-gray-200">
							<h3 class="font-medium text-gray-900">Live Transcript</h3>
							<div class="flex space-x-2">
								<button
									on:click={exportTranscript}
									disabled={transcript.length === 0}
									class="text-sm text-gray-600 hover:text-gray-900 disabled:text-gray-400">
									📄 Export
								</button>
								<button
									on:click={clearTranscript}
									disabled={transcript.length === 0}
									class="text-sm text-gray-600 hover:text-gray-900 disabled:text-gray-400">
									🗑️ Clear
								</button>
							</div>
						</div>
						<div 
							id="transcript-container"
							class="h-96 overflow-y-auto p-4 space-y-3">
							{#each transcript as entry}
								<div class="flex {entry.speaker === 'user' ? 'justify-end' : 'justify-start'}">
									<div class="max-w-[80%] {
										entry.speaker === 'user' 
											? 'bg-blue-500 text-white' 
											: entry.speaker === 'agent'
											? 'bg-gray-100 text-gray-900'
											: 'bg-yellow-50 text-yellow-800'
									} rounded-lg px-4 py-2">
										<div class="flex items-center justify-between mb-1">
											<span class="text-xs font-medium opacity-75">
												{entry.speaker === 'user' ? 'You' : entry.speaker === 'agent' ? demoConfig.agentName : 'System'}
											</span>
											<span class="text-xs opacity-50">{entry.timestamp}</span>
										</div>
										<p class="text-sm">{entry.message}</p>
									</div>
								</div>
							{/each}
							{#if transcript.length === 0}
								<div class="text-center text-gray-500 py-8">
									<p>Start a conversation to see the transcript here</p>
								</div>
							{/if}
						</div>
					</div>
				</div>
			</div>

			<!-- Lead Data & Stats Panel -->
			<div class="space-y-6">
				<!-- Lead Qualification Progress -->
				<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<h3 class="font-semibold text-gray-900 mb-4">Lead Qualification Progress</h3>
					<div class="mb-4">
						<div class="flex justify-between text-sm mb-1">
							<span>Progress</span>
							<span>{qualificationPercentage}%</span>
						</div>
						<div class="w-full bg-gray-200 rounded-full h-2">
							<div class="bg-blue-600 h-2 rounded-full transition-all duration-500" 
								 style="width: {qualificationPercentage}%"></div>
						</div>
					</div>
					<div class="space-y-3 text-sm">
						<div class="flex justify-between">
							<span class="text-gray-600">Name:</span>
							<span class="font-medium {leadData.name ? 'text-green-600' : 'text-gray-400'}">
								{leadData.name || 'Not captured'}
							</span>
						</div>
						<div class="flex justify-between">
							<span class="text-gray-600">Email:</span>
							<span class="font-medium {leadData.email ? 'text-green-600' : 'text-gray-400'}">
								{leadData.email || 'Not captured'}
							</span>
						</div>
						<div class="flex justify-between">
							<span class="text-gray-600">Company:</span>
							<span class="font-medium {leadData.company ? 'text-green-600' : 'text-gray-400'}">
								{leadData.company || 'Not captured'}
							</span>
						</div>
						<div class="flex justify-between">
							<span class="text-gray-600">Industry:</span>
							<span class="font-medium {leadData.industry ? 'text-green-600' : 'text-gray-400'}">
								{leadData.industry || 'Not captured'}
							</span>
						</div>
					</div>
				</div>

				<!-- Conversation Stats -->
				<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<h3 class="font-semibold text-gray-900 mb-4">Conversation Stats</h3>
					<div class="space-y-3 text-sm">
						<div class="flex justify-between">
							<span class="text-gray-600">Current Step:</span>
							<span class="font-medium capitalize text-blue-600">{currentStep.replace('_', ' ')}</span>
						</div>
						<div class="flex justify-between">
							<span class="text-gray-600">Messages:</span>
							<span class="font-medium">{transcript.length}</span>
						</div>
						<div class="flex justify-between">
							<span class="text-gray-600">User Messages:</span>
							<span class="font-medium">{transcript.filter(t => t.speaker === 'user').length}</span>
						</div>
						<div class="flex justify-between">
							<span class="text-gray-600">Agent Responses:</span>
							<span class="font-medium">{transcript.filter(t => t.speaker === 'agent').length}</span>
						</div>
					</div>
				</div>

				<!-- Available Calendar Slots -->
				<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<h3 class="font-semibold text-gray-900 mb-4">Available Demo Slots</h3>
					<div class="space-y-2">
						{#each availableSlots.filter(slot => slot.available) as slot}
							<div class="flex justify-between items-center p-2 bg-gray-50 rounded text-sm">
								<span>{slot.date} at {slot.time}</span>
								<span class="text-green-600 text-xs">Available</span>
							</div>
						{/each}
					</div>
				</div>

				<!-- ElevenLabs Settings -->
				<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
					<h3 class="font-semibold text-gray-900 mb-4">ElevenLabs Configuration</h3>
					<div class="space-y-4">
						<div>
							<label for="voice-id" class="block text-sm font-medium text-gray-700 mb-1">Voice ID</label>
							<input 
								id="voice-id"
								type="text" 
								bind:value={elevenLabsSettings.voiceId}
								placeholder="EXAVITQu4vr4xnSDxMaL"
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
						</div>
						<div>
							<label for="model" class="block text-sm font-medium text-gray-700 mb-1">Model</label>
							<select 
								id="model"
								bind:value={elevenLabsSettings.model}
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
								<option value="eleven_turbo_v2">Eleven Turbo v2</option>
								<option value="eleven_multilingual_v2">Eleven Multilingual v2</option>
								<option value="eleven_monolingual_v1">Eleven Monolingual v1</option>
							</select>
						</div>
						<div class="text-xs text-gray-500">
							Configure these settings when integrating the ElevenLabs widget
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Implementation Guide -->
		<div class="mt-12 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
			<h2 class="text-xl font-semibold text-gray-900 mb-4">🛠️ Implementation & Customization Guide</h2>
			<div class="grid md:grid-cols-2 gap-8">
				<div>
					<h3 class="font-medium text-gray-900 mb-3">For Client Implementation:</h3>
					<ul class="text-sm text-gray-600 space-y-2">
						<li><strong>Voice Customization:</strong> Replace demo agent name, company info, and services in the demoConfig object</li>
						<li><strong>Knowledge Base:</strong> Update the FAQ responses and qualification questions for the client's industry</li>
						<li><strong>Lead Qualification:</strong> Modify leadData fields to match client's specific qualification criteria</li>
						<li><strong>Calendar Integration:</strong> Connect to client's calendar API (Google Calendar, Outlook, Calendly)</li>
						<li><strong>CRM Integration:</strong> Add API calls to sync captured lead data with client's CRM system</li>
					</ul>
				</div>
				<div>
					<h3 class="font-medium text-gray-900 mb-3">ElevenLabs Integration Steps:</h3>
					<ul class="text-sm text-gray-600 space-y-2">
						<li><strong>Widget Integration:</strong> Add ElevenLabs conversational AI widget in the placeholder area</li>
						<li><strong>Voice Configuration:</strong> Set up voice ID, model, and speech settings</li>
						<li><strong>Conversation Hooks:</strong> Connect widget events to the existing conversation logic functions</li>
						<li><strong>Real-time Updates:</strong> Sync voice interactions with transcript and lead qualification</li>
						<li><strong>Error Handling:</strong> Implement fallback to text mode if voice fails</li>
					</ul>
				</div>
			</div>
			
			<div class="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
				<h4 class="font-medium text-blue-900 mb-2">💡 Ready for ElevenLabs Integration:</h4>
				<p class="text-sm text-blue-800">
					This demo is now prepared for ElevenLabs integration. The conversation logic, lead qualification, 
					and transcript management are all ready. Simply add the ElevenLabs widget in the designated area 
					and connect it to the existing handleUserInput() function to enable voice conversations.
				</p>
			</div>
		</div>
	</div>
</div> 