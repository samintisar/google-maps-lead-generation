<script lang="ts">
	import { goto } from '$app/navigation';
	import { leadsStore, leadsLoading, leadsError } from '$lib/stores/leads';
	import { LeadStatus, LeadSource } from '$lib/types';
	import type { LeadCreate } from '$lib/types';

	// Form data
	let formData: LeadCreate = {
		first_name: '',
		last_name: '',
		email: '',
		phone: '',
		company: '',
		job_title: '',
		industry: '',
		website: '',
		source: LeadSource.WEBSITE,
		status: LeadStatus.NEW,
		notes: '',
		interest_level: 5,
		budget: undefined,
		timeline: '',
		organization_id: 1 // TODO: Get from user session/context
	};

	// Form validation
	let errors: Record<string, string> = {};

	function validateForm() {
		errors = {};

		if (!formData.first_name.trim()) {
			errors.first_name = 'First name is required';
		}

		if (!formData.last_name.trim()) {
			errors.last_name = 'Last name is required';
		}

		if (!formData.email.trim()) {
			errors.email = 'Email is required';
		} else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
			errors.email = 'Please enter a valid email address';
		}

		if ((formData.interest_level ?? 5) < 1 || (formData.interest_level ?? 5) > 10) {
			errors.interest_level = 'Interest level must be between 1 and 10';
		}

		if (formData.budget && formData.budget < 0) {
			errors.budget = 'Budget must be a positive number';
		}

		return Object.keys(errors).length === 0;
	}

	// Submit form
	async function handleSubmit(event: Event) {
		event.preventDefault();
		if (!validateForm()) {
			return;
		}

		// Clean up form data - remove empty strings
		const cleanedData = Object.fromEntries(
			Object.entries(formData).filter(([key, value]) => {
				if (typeof value === 'string') {
					return value.trim() !== '';
				}
				return value !== undefined && value !== null;
			})
		) as LeadCreate;

		const result = await leadsStore.createLead(cleanedData);
		if (result?.data) {
			// Navigate to the new lead's detail page
			goto(`/dashboard/leads/${result.data.id}`);
		}
	}

	// Cancel and go back
	function handleCancel() {
		goto('/dashboard/leads');
	}
</script>

<svelte:head>
	<title>Add New Lead - LMA Platform</title>
</svelte:head>

<div class="py-6">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
		<!-- Page header -->
		<div class="md:flex md:items-center md:justify-between mb-6">
			<div class="flex-1 min-w-0">
				<h1 class="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
					Add New Lead
				</h1>
				<p class="mt-1 text-sm text-gray-500">
					Create a new lead record in your pipeline
				</p>
			</div>
		</div>

		<!-- Error message -->
		{#if $leadsError}
			<div class="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative">
				<strong class="font-bold">Error:</strong>
				<span class="block sm:inline">{$leadsError}</span>
			</div>
		{/if}

		<!-- Form -->
		<form onsubmit={handleSubmit} class="space-y-6">
			<div class="bg-white shadow rounded-lg">
				<div class="px-4 py-5 sm:p-6">
					<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Contact Information</h3>
					
					<div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
						<div>
							<label for="first_name" class="block text-sm font-medium text-gray-700">
								First Name <span class="text-red-500">*</span>
							</label>
							<input
								type="text"
								id="first_name"
								bind:value={formData.first_name}
								class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md {errors.first_name ? 'border-red-300' : ''}"
								required
							/>
							{#if errors.first_name}
								<p class="mt-1 text-sm text-red-600">{errors.first_name}</p>
							{/if}
						</div>

						<div>
							<label for="last_name" class="block text-sm font-medium text-gray-700">
								Last Name <span class="text-red-500">*</span>
							</label>
							<input
								type="text"
								id="last_name"
								bind:value={formData.last_name}
								class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md {errors.last_name ? 'border-red-300' : ''}"
								required
							/>
							{#if errors.last_name}
								<p class="mt-1 text-sm text-red-600">{errors.last_name}</p>
							{/if}
						</div>

						<div>
							<label for="email" class="block text-sm font-medium text-gray-700">
								Email Address <span class="text-red-500">*</span>
							</label>
							<input
								type="email"
								id="email"
								bind:value={formData.email}
								class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md {errors.email ? 'border-red-300' : ''}"
								required
							/>
							{#if errors.email}
								<p class="mt-1 text-sm text-red-600">{errors.email}</p>
							{/if}
						</div>

						<div>
							<label for="phone" class="block text-sm font-medium text-gray-700">Phone Number</label>
							<input
								type="tel"
								id="phone"
								bind:value={formData.phone}
								class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
								placeholder="+1 (555) 123-4567"
							/>
						</div>
					</div>
				</div>
			</div>

			<div class="bg-white shadow rounded-lg">
				<div class="px-4 py-5 sm:p-6">
					<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Company Information</h3>
					
					<div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
						<div>
							<label for="company" class="block text-sm font-medium text-gray-700">Company</label>
							<input
								type="text"
								id="company"
								bind:value={formData.company}
								class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
								placeholder="Acme Corp"
							/>
						</div>

						<div>
							<label for="job_title" class="block text-sm font-medium text-gray-700">Job Title</label>
							<input
								type="text"
								id="job_title"
								bind:value={formData.job_title}
								class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
								placeholder="Marketing Director"
							/>
						</div>

						<div>
							<label for="industry" class="block text-sm font-medium text-gray-700">Industry</label>
							<input
								type="text"
								id="industry"
								bind:value={formData.industry}
								class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
								placeholder="Technology"
							/>
						</div>

						<div>
							<label for="website" class="block text-sm font-medium text-gray-700">Website</label>
							<input
								type="url"
								id="website"
								bind:value={formData.website}
								class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
								placeholder="https://example.com"
							/>
						</div>
					</div>
				</div>
			</div>

			<div class="bg-white shadow rounded-lg">
				<div class="px-4 py-5 sm:p-6">
					<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Lead Details</h3>
					
					<div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
						<div>
							<label for="source" class="block text-sm font-medium text-gray-700">Lead Source</label>
							<select
								id="source"
								bind:value={formData.source}
								class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
							>
								{#each Object.values(LeadSource) as source}
									<option value={source}>{source.replace('_', ' ').toUpperCase()}</option>
								{/each}
							</select>
						</div>

						<div>
							<label for="status" class="block text-sm font-medium text-gray-700">Initial Status</label>
							<select
								id="status"
								bind:value={formData.status}
								class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
							>
								{#each Object.values(LeadStatus) as status}
									<option value={status}>{status.replace('_', ' ').toUpperCase()}</option>
								{/each}
							</select>
						</div>

						<div>
							<label for="interest_level" class="block text-sm font-medium text-gray-700">
								Interest Level (1-10)
							</label>
							<input
								type="number"
								id="interest_level"
								bind:value={formData.interest_level}
								min="1"
								max="10"
								class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md {errors.interest_level ? 'border-red-300' : ''}"
							/>
							{#if errors.interest_level}
								<p class="mt-1 text-sm text-red-600">{errors.interest_level}</p>
							{/if}
						</div>

						<div>
							<label for="budget" class="block text-sm font-medium text-gray-700">Estimated Budget ($)</label>
							<input
								type="number"
								id="budget"
								bind:value={formData.budget}
								min="0"
								step="100"
								class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md {errors.budget ? 'border-red-300' : ''}"
								placeholder="10000"
							/>
							{#if errors.budget}
								<p class="mt-1 text-sm text-red-600">{errors.budget}</p>
							{/if}
						</div>

						<div class="sm:col-span-2">
							<label for="timeline" class="block text-sm font-medium text-gray-700">Decision Timeline</label>
							<input
								type="text"
								id="timeline"
								bind:value={formData.timeline}
								class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
								placeholder="Q2 2024"
							/>
						</div>
					</div>
				</div>
			</div>

			<div class="bg-white shadow rounded-lg">
				<div class="px-4 py-5 sm:p-6">
					<h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Notes</h3>
					
					<div>
						<label for="notes" class="block text-sm font-medium text-gray-700">Initial Notes</label>
						<textarea
							id="notes"
							bind:value={formData.notes}
							rows="4"
							class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 mt-1 block w-full sm:text-sm border-gray-300 rounded-md"
							placeholder="Add any initial notes about this lead..."
						></textarea>
					</div>
				</div>
			</div>

			<!-- Form actions -->
			<div class="flex justify-end space-x-3">
				<button
					type="button"
					onclick={handleCancel}
					class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
				>
					Cancel
				</button>
				<button
					type="submit"
					disabled={$leadsLoading.create}
					class="bg-indigo-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{#if $leadsLoading.create}
						<svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						Creating...
					{:else}
						Create Lead
					{/if}
				</button>
			</div>
		</form>
	</div>
</div> 