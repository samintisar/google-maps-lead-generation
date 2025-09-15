import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		port: 5173,
		host: '127.0.0.1'
	},
	ssr: {
		noExternal: []
	},
	optimizeDeps: {
		exclude: ['@googlemaps/js-api-loader']
	}
});
