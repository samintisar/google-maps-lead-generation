<script>
	import SignIn from 'clerk-sveltekit/client/SignIn.svelte';
</script>

<svelte:head>
	<title>Sign In - Lead Management Platform</title>
	<meta name="description" content="Sign in to your Lead Management Platform account" />
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-md w-full space-y-8">
		<div>
			<h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
				Sign in to your account
			</h2>
			<p class="mt-2 text-center text-sm text-gray-600">
				Or
				<a href="/sign-up" class="font-medium text-indigo-600 hover:text-indigo-500">
					create a new account
				</a>
			</p>
		</div>
		
		<div class="mt-8">
			<SignIn redirectUrl="/dashboard" />
		</div>
	</div>
</div> 