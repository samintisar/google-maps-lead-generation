<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { Button, Input, Card } from '$lib/components';
	import { auth } from '$lib/stores';
	import { api } from '$lib/api';
	import toast from 'svelte-french-toast';
	
	let email = '';
	let password = '';
	let isLoading = false;
	let errors: { email?: string; password?: string } = {};
	
	// Redirect if already authenticated
	onMount(() => {
		auth.init();
		const unsubscribe = auth.subscribe(($auth) => {
			if ($auth.isAuthenticated) {
				goto('/dashboard');
			}
		});
		return unsubscribe;
	});
	
	function validateForm() {
		errors = {};
		
		if (!email) {
			errors.email = 'Email is required';
		} else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
			errors.email = 'Please enter a valid email address';
		}
		
		if (!password) {
			errors.password = 'Password is required';
		} else if (password.length < 6) {
			errors.password = 'Password must be at least 6 characters';
		}
		
		return Object.keys(errors).length === 0;
	}
	
	async function handleSubmit() {
		if (!validateForm()) return;
		
		isLoading = true;
		auth.setLoading(true);
		
		try {
			const response = await api.auth.login({ email, password });
			auth.login(response.user, response.access_token);
			toast.success('Welcome back!');
			goto('/dashboard');
		} catch (error) {
			console.error('Login failed:', error);
			toast.error(error instanceof Error ? error.message : 'Login failed');
		} finally {
			isLoading = false;
			auth.setLoading(false);
		}
	}
	
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			handleSubmit();
		}
	}
</script>

<svelte:head>
	<title>Login - LMA Platform</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-md w-full space-y-8">
		<div>
			<h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
				Sign in to your account
			</h2>
			<p class="mt-2 text-center text-sm text-gray-600">
				Or
				<a href="/register" class="font-medium text-blue-600 hover:text-blue-500">
					create a new account
				</a>
			</p>
		</div>
		
		<Card padding="large">
			<form class="space-y-6" on:submit|preventDefault={handleSubmit}>
				<Input
					type="email"
					label="Email address"
					id="email"
					name="email"
					required
					bind:value={email}
					error={errors.email}
					placeholder="Enter your email"
					on:keydown={handleKeydown}
				/>
				
				<Input
					type="password"
					label="Password"
					id="password"
					name="password"
					required
					bind:value={password}
					error={errors.password}
					placeholder="Enter your password"
					on:keydown={handleKeydown}
				/>
				
				<div class="flex items-center justify-between">
					<div class="flex items-center">
						<input
							id="remember-me"
							name="remember-me"
							type="checkbox"
							class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
						/>
						<label for="remember-me" class="ml-2 block text-sm text-gray-900">
							Remember me
						</label>
					</div>
					
					<div class="text-sm">
						<a href="/forgot-password" class="font-medium text-blue-600 hover:text-blue-500">
							Forgot your password?
						</a>
					</div>
				</div>
				
				<Button
					type="submit"
					variant="primary"
					size="large"
					disabled={isLoading}
					loading={isLoading}
					class="w-full"
				>
					Sign in
				</Button>
			</form>
		</Card>
		
		<div class="text-center">
			<p class="text-sm text-gray-600">
				Don't have an account?
				<a href="/register" class="font-medium text-blue-600 hover:text-blue-500">
					Sign up here
				</a>
			</p>
		</div>
	</div>
</div> 