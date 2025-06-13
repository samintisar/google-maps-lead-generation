<!-- Settings Page -->
<script lang="ts">
	import { onMount } from 'svelte';
	// Auth store removed
	
	// Settings state - auth removed
	let userSettings = $state({
		username: 'demo_user',
		email: 'demo@example.com',
		notifications: {
			email: true,
			browser: true,
			leadUpdates: true,
			weeklyReport: true
		},
		privacy: {
			profileVisible: false,
			dataExport: false
		},
		preferences: {
			theme: 'light',
			timezone: 'UTC',
			dateFormat: 'MM/dd/yyyy',
			currency: 'USD'
		}
	});
	
	let saving = $state(false);
	let message = $state('');
	
	const saveSettings = async (event: Event) => {
		event.preventDefault();
		saving = true;
		message = '';
		
		try {
			// Simulate API call - replace with actual settings update
			await new Promise(resolve => setTimeout(resolve, 1000));
			message = 'Settings saved successfully!';
		} catch (error) {
			message = 'Failed to save settings. Please try again.';
			console.error('Error saving settings:', error);
		} finally {
			saving = false;
			setTimeout(() => message = '', 3000);
		}
	};
</script>

<svelte:head>
	<title>Settings - LMA Platform</title>
</svelte:head>

<div class="p-6">
	<div class="mb-6">
		<h1 class="text-3xl font-semibold text-gray-900">Account Settings</h1>
		<p class="text-gray-600 mt-2">Manage your account preferences and notification settings.</p>
	</div>

	{#if message}
		<div class="mb-6 p-4 rounded-md {message.includes('success') ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}">
			<p class="text-sm {message.includes('success') ? 'text-green-800' : 'text-red-800'}">{message}</p>
		</div>
	{/if}

	<div class="max-w-4xl">
		<form onsubmit={saveSettings}>
			<!-- Profile Section -->
			<div class="bg-white shadow-sm rounded-lg mb-6">
				<div class="px-6 py-4 border-b border-gray-200">
					<h3 class="text-lg font-medium text-gray-900">Profile Information</h3>
				</div>
				<div class="px-6 py-4 space-y-4">
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label for="username" class="block text-sm font-medium text-gray-700 mb-1">Username</label>
							<input
								type="text"
								id="username"
								bind:value={userSettings.username}
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
								placeholder="Enter username"
							/>
						</div>
						<div>
							<label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email</label>
							<input
								type="email"
								id="email"
								bind:value={userSettings.email}
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
								placeholder="Enter email"
							/>
						</div>
					</div>
				</div>
			</div>

			<!-- Notifications Section -->
			<div class="bg-white shadow-sm rounded-lg mb-6">
				<div class="px-6 py-4 border-b border-gray-200">
					<h3 class="text-lg font-medium text-gray-900">Notification Preferences</h3>
				</div>
				<div class="px-6 py-4 space-y-4">
					<div class="space-y-3">
						<label class="flex items-center">
							<input
								type="checkbox"
								bind:checked={userSettings.notifications.email}
								class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
							/>
							<span class="ml-2 text-sm text-gray-700">Email notifications</span>
						</label>
						<label class="flex items-center">
							<input
								type="checkbox"
								bind:checked={userSettings.notifications.browser}
								class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
							/>
							<span class="ml-2 text-sm text-gray-700">Browser notifications</span>
						</label>
						<label class="flex items-center">
							<input
								type="checkbox"
								bind:checked={userSettings.notifications.leadUpdates}
								class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
							/>
							<span class="ml-2 text-sm text-gray-700">Lead status updates</span>
						</label>
						<label class="flex items-center">
							<input
								type="checkbox"
								bind:checked={userSettings.notifications.weeklyReport}
								class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
							/>
							<span class="ml-2 text-sm text-gray-700">Weekly performance reports</span>
						</label>
					</div>
				</div>
			</div>

			<!-- Preferences Section -->
			<div class="bg-white shadow-sm rounded-lg mb-6">
				<div class="px-6 py-4 border-b border-gray-200">
					<h3 class="text-lg font-medium text-gray-900">Display Preferences</h3>
				</div>
				<div class="px-6 py-4 space-y-4">
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label for="theme" class="block text-sm font-medium text-gray-700 mb-1">Theme</label>
							<select
								id="theme"
								bind:value={userSettings.preferences.theme}
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
							>
								<option value="light">Light</option>
								<option value="dark">Dark</option>
								<option value="system">System</option>
							</select>
						</div>
						<div>
							<label for="timezone" class="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
							<select
								id="timezone"
								bind:value={userSettings.preferences.timezone}
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
							>
								<option value="UTC">UTC</option>
								<option value="America/New_York">Eastern Time</option>
								<option value="America/Chicago">Central Time</option>
								<option value="America/Denver">Mountain Time</option>
								<option value="America/Los_Angeles">Pacific Time</option>
							</select>
						</div>
						<div>
							<label for="dateFormat" class="block text-sm font-medium text-gray-700 mb-1">Date Format</label>
							<select
								id="dateFormat"
								bind:value={userSettings.preferences.dateFormat}
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
							>
								<option value="MM/dd/yyyy">MM/dd/yyyy</option>
								<option value="dd/MM/yyyy">dd/MM/yyyy</option>
								<option value="yyyy-MM-dd">yyyy-MM-dd</option>
							</select>
						</div>
						<div>
							<label for="currency" class="block text-sm font-medium text-gray-700 mb-1">Currency</label>
							<select
								id="currency"
								bind:value={userSettings.preferences.currency}
								class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
							>
								<option value="USD">USD ($)</option>
								<option value="EUR">EUR (€)</option>
								<option value="GBP">GBP (£)</option>
								<option value="CAD">CAD (C$)</option>
							</select>
						</div>
					</div>
				</div>
			</div>

			<!-- Privacy Section -->
			<div class="bg-white shadow-sm rounded-lg mb-6">
				<div class="px-6 py-4 border-b border-gray-200">
					<h3 class="text-lg font-medium text-gray-900">Privacy & Data</h3>
				</div>
				<div class="px-6 py-4 space-y-4">
					<div class="space-y-3">
						<label class="flex items-center">
							<input
								type="checkbox"
								bind:checked={userSettings.privacy.profileVisible}
								class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
							/>
							<span class="ml-2 text-sm text-gray-700">Make profile visible to team members</span>
						</label>
						<label class="flex items-center">
							<input
								type="checkbox"
								bind:checked={userSettings.privacy.dataExport}
								class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
							/>
							<span class="ml-2 text-sm text-gray-700">Allow data export for analytics</span>
						</label>
					</div>
				</div>
			</div>

			<!-- Save Button -->
			<div class="flex justify-end">
				<button
					type="submit"
					disabled={saving}
					class="px-6 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{#if saving}
						<div class="flex items-center">
							<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
							Saving...
						</div>
					{:else}
						Save Settings
					{/if}
				</button>
			</div>
		</form>
	</div>
</div> 