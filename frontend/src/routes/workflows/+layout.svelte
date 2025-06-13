<script lang="ts">
	let showMobileMenu = $state(false);
	let { children } = $props();

	function toggleMobileMenu() {
		showMobileMenu = !showMobileMenu;
	}
</script>

<div class="h-screen flex">
	<!-- Sidebar -->
	<div class="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 lg:bg-gray-900">
		<div class="flex-1 flex flex-col min-h-0">
			<div class="flex items-center h-16 flex-shrink-0 px-4 bg-gray-900">
				<h1 class="text-white text-xl font-semibold">LMA Platform</h1>
			</div>
			<nav class="flex-1 px-2 py-4 bg-gray-900 space-y-1">
				<a href="/dashboard" class="text-gray-300 hover:bg-gray-700 hover:text-white group flex items-center px-2 py-2 text-sm font-medium rounded-md">
					<svg class="text-gray-400 group-hover:text-gray-300 mr-3 flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2V7a2 2 0 012-2h14a2 2 0 012 2v2a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
					</svg>
					Dashboard
				</a>
				<a href="/dashboard/leads" class="text-gray-300 hover:bg-gray-700 hover:text-white group flex items-center px-2 py-2 text-sm font-medium rounded-md">
					<svg class="text-gray-400 group-hover:text-gray-300 mr-3 flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 01 5.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 01 9.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM9 9a2 2 0 11-4 0 2 2 0 014 0z" />
					</svg>
					Leads
				</a>
				<a href="/dashboard/analytics" class="text-gray-300 hover:bg-gray-700 hover:text-white group flex items-center px-2 py-2 text-sm font-medium rounded-md">
					<svg class="text-gray-400 group-hover:text-gray-300 mr-3 flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
					</svg>
					Analytics
				</a>
				<a href="/workflows" class="bg-gray-800 text-white group flex items-center px-2 py-2 text-sm font-medium rounded-md">
					<svg class="text-gray-300 mr-3 flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
					</svg>
					Workflows
				</a>
				<a href="/dashboard/settings" class="text-gray-300 hover:bg-gray-700 hover:text-white group flex items-center px-2 py-2 text-sm font-medium rounded-md">
					<svg class="text-gray-400 group-hover:text-gray-300 mr-3 flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
					</svg>
					Settings
				</a>
			</nav>
		</div>
	</div>

	<!-- Mobile menu overlay -->
	{#if showMobileMenu}
		<div class="lg:hidden fixed inset-0 z-40 flex">
			<div 
				class="fixed inset-0 bg-gray-600 bg-opacity-75" 
				onclick={toggleMobileMenu}
				onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggleMobileMenu(); }}
				tabindex="0"
				role="button"
				aria-label="Close menu"
			></div>
			<div class="relative flex-1 flex flex-col max-w-xs w-full bg-gray-900">
				<div class="absolute top-0 right-0 -mr-12 pt-2">
					<button
						type="button"
						class="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
						onclick={toggleMobileMenu}
					>
						<span class="sr-only">Close sidebar</span>
						<svg class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
				<div class="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
					<div class="flex-shrink-0 flex items-center px-4">
						<h1 class="text-white text-xl font-semibold">LMA Platform</h1>
					</div>
					<nav class="mt-5 px-2 space-y-1">
						<a href="/dashboard" class="text-gray-300 hover:bg-gray-700 hover:text-white group flex items-center px-2 py-2 text-base font-medium rounded-md">
							Dashboard
						</a>
						<a href="/dashboard/leads" class="text-gray-300 hover:bg-gray-700 hover:text-white group flex items-center px-2 py-2 text-base font-medium rounded-md">
							Leads
						</a>
						<a href="/dashboard/analytics" class="text-gray-300 hover:bg-gray-700 hover:text-white group flex items-center px-2 py-2 text-base font-medium rounded-md">
							Analytics
						</a>
						<a href="/workflows" class="bg-gray-800 text-white group flex items-center px-2 py-2 text-base font-medium rounded-md">
							Workflows
						</a>
						<a href="/dashboard/settings" class="text-gray-300 hover:bg-gray-700 hover:text-white group flex items-center px-2 py-2 text-base font-medium rounded-md">
							Settings
						</a>
					</nav>
				</div>
			</div>
		</div>
	{/if}

	<!-- Main content -->
	<div class="lg:pl-64 flex flex-col flex-1">
		<!-- Top navigation -->
		<div class="sticky top-0 z-10 lg:hidden pl-1 pt-1 sm:pl-3 sm:pt-3 bg-gray-100">
			<button
				type="button"
				class="-ml-0.5 -mt-0.5 h-12 w-12 inline-flex items-center justify-center rounded-md text-gray-500 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
				onclick={toggleMobileMenu}
			>
				<span class="sr-only">Open sidebar</span>
				<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
				</svg>
			</button>
		</div>

		<!-- Header -->
		<header class="bg-white shadow-sm lg:static lg:overflow-y-visible">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="relative flex justify-between xl:grid xl:grid-cols-12 lg:gap-8">
					<div class="flex md:absolute md:left-0 md:inset-y-0 lg:static xl:col-span-2">
						<div class="flex-shrink-0 flex items-center">
							<!-- This space can be used for breadcrumbs or page title -->
						</div>
					</div>
					<div class="min-w-0 flex-1 md:px-8 lg:px-0 xl:col-span-6">
						<!-- Search can go here if needed -->
					</div>
					<div class="flex items-center md:absolute md:right-0 md:inset-y-0 lg:hidden xl:col-span-4">
						<!-- Mobile menu button is above -->
					</div>
					<div class="hidden lg:flex lg:items-center lg:justify-end xl:col-span-4">
						<!-- Authentication removed -->
					</div>
				</div>
			</div>
		</header>

		<!-- Main content area -->
		<main class="flex-1 bg-gray-50">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
				{@render children()}
			</div>
		</main>
	</div>
</div> 