import type { HandleClientError } from '@sveltejs/kit';
import { initializeClerkClient } from 'clerk-sveltekit/client';
import { env } from '$env/dynamic/public';

const clerkPublishableKey = env.PUBLIC_CLERK_PUBLISHABLE_KEY;

if (clerkPublishableKey) {
	initializeClerkClient(clerkPublishableKey, {
		afterSignInUrl: '/dashboard',
		afterSignUpUrl: '/dashboard',
		signInUrl: '/sign-in',
		signUpUrl: '/sign-up',
	});
}

export const handleError: HandleClientError = async ({ error, event }) => {
	console.error(error, event);
}; 