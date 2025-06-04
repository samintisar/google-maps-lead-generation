import type { Handle } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';
import { handleClerk } from 'clerk-sveltekit/server';
import { env } from '$env/dynamic/private';

const clerkSecretKey = env.CLERK_SECRET_KEY;

export const handle: Handle = sequence(
	clerkSecretKey ? handleClerk(clerkSecretKey, {
		debug: true,
		protectedPaths: ['/dashboard', '/leads', '/analytics'],
		signInUrl: '/sign-in',
	}) : (({ event, resolve }) => resolve(event))
); 