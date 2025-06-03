<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { Button, Input, Card } from '$lib/components';
	import { auth } from '$lib/stores';
	import { api } from '$lib/api';
	import toast from 'svelte-french-toast';
	
	let email = '';
	let password = '';
	let confirmPassword = '';
	let firstName = '';
	let lastName = '';
	let organizationName = '';
	let isLoading = false;
	let errors: { 
		email?: string; 
		password?: string; 
		confirmPassword?: string;
		firstName?: string;
		lastName?: string;
	} = {};
	
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
		
		if (!firstName) {
			errors.firstName = 'First name is required';
		}
		
		if (!lastName) {
			errors.lastName = 'Last name is required';
		}
		
		if (!email) {
			errors.email = 'Email is required';
		} else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
			errors.email = 'Please enter a valid email address';
		}
		
		if (!password) {
			errors.password = 'Password is required';
		} else if (password.length < 8) {
			errors.password = 'Password must be at least 8 characters';
		} else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) {
			errors.password = 'Password must contain at least one uppercase letter, one lowercase letter, and one number';
		}
		
		if (!confirmPassword) {
			errors.confirmPassword = 'Please confirm your password';
		} else if (password !== confirmPassword) {
			errors.confirmPassword = 'Passwords do not match';
		}
		
		return Object.keys(errors).length === 0;
	}
	
	async function handleSubmit() {
		if (!validateForm()) return;
		
		isLoading = true;
		auth.setLoading(true);
		
		try {
			const response = await api.auth.register({
				email,
				password,
				first_name: firstName,
				last_name: lastName,
				organization_name: organizationName || undefined
			});
			
			auth.login(response.user, response.access_token);
			toast.success('Account created successfully! Welcome to LMA Platform.');
			goto('/dashboard');
		} catch (error) {
			console.error('Registration failed:', error);
			toast.error(error instanceof Error ? error.message : 'Registration failed');
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
	<title>Register - LMA Platform</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-md w-full space-y-8">
		<div>
			<h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
				Create your account
			</h2>
			<p class="mt-2 text-center text-sm text-gray-600">
				Or
				<a href="/login" class="font-medium text-blue-600 hover:text-blue-500">
					sign in to your existing account
				</a>
			</p>
		</div>
		
		<Card padding="large">
			<form class="space-y-6" on:submit|preventDefault={handleSubmit}>
				<div class="grid grid-cols-2 gap-4">
					<Input
						type="text"
						label="First name"
						id="firstName"
						name="firstName"
						required
						bind:value={firstName}
						error={errors.firstName}
						placeholder="John"
						on:keydown={handleKeydown}
					/>
					
					<Input
						type="text"
						label="Last name"
						id="lastName"
						name="lastName"
						required
						bind:value={lastName}
						error={errors.lastName}
						placeholder="Doe"
						on:keydown={handleKeydown}
					/>
				</div>
				
				<Input
					type="email"
					label="Email address"
					id="email"
					name="email"
					required
					bind:value={email}
					error={errors.email}
					placeholder="john@company.com"
					on:keydown={handleKeydown}
				/>
				
				<Input
					type="text"
					label="Organization name (optional)"
					id="organizationName"
					name="organizationName"
					bind:value={organizationName}
					placeholder="Your Company"
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
					placeholder="Create a strong password"
					on:keydown={handleKeydown}
				/>
				
				<Input
					type="password"
					label="Confirm password"
					id="confirmPassword"
					name="confirmPassword"
					required
					bind:value={confirmPassword}
					error={errors.confirmPassword}
					placeholder="Confirm your password"
					on:keydown={handleKeydown}
				/>
				
				<div class="flex items-center">
					<input
						id="terms"
						name="terms"
						type="checkbox"
						required
						class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
					/>
					<label for="terms" class="ml-2 block text-sm text-gray-900">
						I agree to the
						<a href="/terms" class="text-blue-600 hover:text-blue-500">Terms of Service</a>
						and
						<a href="/privacy" class="text-blue-600 hover:text-blue-500">Privacy Policy</a>
					</label>
				</div>
				
				<Button
					type="submit"
					variant="primary"
					size="large"
					disabled={isLoading}
					loading={isLoading}
					class="w-full"
				>
					Create account
				</Button>
			</form>
		</Card>
		
		<div class="text-center">
			<p class="text-sm text-gray-600">
				Already have an account?
				<a href="/login" class="font-medium text-blue-600 hover:text-blue-500">
					Sign in here
				</a>
			</p>
		</div>
	</div>
</div> 