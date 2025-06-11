<script lang="ts">
	import { auth, authStore } from '$lib/stores/auth';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import ErrorAlert from '$lib/components/ErrorAlert.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	let username = $state('');
	let password = $state('');
	let localError = $state<string | null>(null);

	// Reactive state from auth store
	let authState = $state($authStore);

	// Subscribe to auth store changes
	onMount(() => {
		const unsubscribe = authStore.subscribe(state => {
			authState = state;
		});

		// If already authenticated, redirect to dashboard
		if (authState.isAuthenticated) {
			goto('/dashboard');
		}

		return unsubscribe;
	});

	async function handleSubmit(event: Event) {
		event.preventDefault();
		localError = null;
		auth.clearError(); // Clear any previous auth store errors

		if (!username || !password) {
			localError = 'Please fill in all fields';
			return;
		}

		try {
			await auth.login(username, password);
			// Redirect happens in auth.login()
		} catch (err) {
			localError = (err as Error).message;
		}
	}

	function dismissError() {
		localError = null;
		auth.clearError();
	}

	// Get the error to display (local error takes precedence)
	let displayError = $derived(localError || authState.error);
</script>

<svelte:head>
	<title>Login - LMA Platform</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-md w-full space-y-8">
		<div>
			<div class="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-indigo-100">
				<svg class="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
				</svg>
			</div>
			<h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
				Sign in to your account
			</h2>
			<p class="mt-2 text-center text-sm text-gray-600">
				Or
				<a href="/register" class="font-medium text-indigo-600 hover:text-indigo-500">
					create a new account
				</a>
			</p>
		</div>

		<form class="mt-8 space-y-6" onsubmit={handleSubmit} autocomplete="on">
			<!-- Error Alert -->
			{#if displayError}
				<ErrorAlert error={displayError} onDismiss={dismissError} />
			{/if}

			<div class="rounded-md shadow-sm -space-y-px">
				<div>
					<label for="username" class="sr-only">Username or email address</label>
					<input
						id="username"
						name="username"
						type="text"
						autocomplete="username"
						required
						bind:value={username}
						disabled={authState.isLoading}
						data-testid="username-input"
						class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
						placeholder="Username or email address"
					/>
				</div>
				<div>
					<label for="password" class="sr-only">Password</label>
					<input
						id="password"
						name="password"
						type="password"
						autocomplete="current-password"
						required
						bind:value={password}
						disabled={authState.isLoading}
						data-testid="password-input"
						class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
						placeholder="Password"
					/>
				</div>
			</div>

			<div class="flex items-center justify-between">
				<div class="flex items-center">
					<input
						id="remember-me"
						name="remember-me"
						type="checkbox"
						disabled={authState.isLoading}
						class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded disabled:cursor-not-allowed"
					/>
					<label for="remember-me" class="ml-2 block text-sm text-gray-900">
						Remember me
					</label>
				</div>

				<div class="text-sm">
					<a href="/forgot-password" class="font-medium text-indigo-600 hover:text-indigo-500">
						Forgot your password?
					</a>
				</div>
			</div>

			<div>
				<button
					type="submit"
					disabled={authState.isLoading}
					class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{#if authState.isLoading}
						<LoadingSpinner size="sm" message="Signing in..." />
					{:else}
						Sign in
					{/if}
				</button>
			</div>
		</form>

		<div class="text-center">
			<a href="/" class="font-medium text-indigo-600 hover:text-indigo-500">
				← Back to homepage
			</a>
		</div>
	</div>
</div> 