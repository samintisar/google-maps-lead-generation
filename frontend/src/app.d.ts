/// <reference types="svelte-clerk/env" />

declare global {
	namespace App {
		// interface Error {}
		interface Locals {
			auth: () => {
				userId?: string;
				user?: any;
				sessionId?: string;
			};
		}
		// interface PageData {}
		// interface Platform {}
	}
}

export {}; 