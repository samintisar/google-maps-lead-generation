<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { activeTab } from '$lib/stores/app';
	import type { TabType } from '$lib/types';

	const dispatch = createEventDispatcher<{
		tabChange: TabType;
	}>();

	function handleTabClick(tab: TabType) {
		activeTab.set(tab);
		dispatch('tabChange', tab);
	}

	$: tabClasses = (tab: TabType) =>
		`flex-1 py-3 px-4 text-center font-medium border-2 border-foreground transition-colors ${
			$activeTab === tab
				? 'bg-primary text-primary-foreground'
				: 'bg-background text-foreground hover:bg-muted'
		}`;
</script>

<div class="flex bg-background border-t-2 border-foreground md:hidden">
	<button
		class={tabClasses('results')}
		on:click={() => handleTabClick('results')}
	>
		Results
	</button>
	<button
		class={tabClasses('leads')}
		on:click={() => handleTabClick('leads')}
	>
		My Leads
	</button>
</div>