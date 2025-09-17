<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import CardHeader from '$lib/components/ui/CardHeader.svelte';
	import CardTitle from '$lib/components/ui/CardTitle.svelte';
	import CardContent from '$lib/components/ui/CardContent.svelte';
	import { leadsStore } from '$lib/stores/leads';
	import { convertLeadsToCSV, downloadCSV } from '$lib/utils/csv';
	import { Trash, Phone, Star, MapPin, Globe } from 'lucide-svelte';

	const dispatch = createEventDispatcher();

	function handleDelete(id: string) {
		leadsStore.remove(id);
	}

	function handleExportCSV() {
		if ($leadsStore.length === 0) {
			alert('No leads to export');
			return;
		}

		const csvContent = convertLeadsToCSV($leadsStore);
		const timestamp = new Date().toISOString().split('T')[0];
		downloadCSV(csvContent, `leads-${timestamp}.csv`);
	}

	function formatDate(dateString: string) {
		return new Date(dateString).toLocaleDateString();
	}

	function formatPhone(phone?: string) {
		if (!phone) return '-';
		// Simple phone formatting for international numbers
		if (phone.startsWith('+1')) {
			return phone.replace(/^\+1/, '').replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
		}
		return phone; // Return as-is for non-US numbers
	}
</script>

<div class="h-full overflow-y-auto bg-background">
	<div class="p-4">
		<div class="flex justify-between items-center mb-4 pb-2 border-b-2 border-foreground">
			<h2 class="text-xl font-semibold">
				My Leads ({$leadsStore.length})
			</h2>
			{#if $leadsStore.length > 0}
				<Button variant="outline" class="border-2 border-foreground bg-background text-foreground hover:bg-primary hover:text-primary-foreground shadow-[4px_4px_0_0_#000] hover:shadow-none hover:translate-x-1 hover:translate-y-1 transition-all duration-200" on:click={handleExportCSV}>
					Export CSV
				</Button>
			{/if}
		</div>

		{#if $leadsStore.length === 0}
			<div class="text-center py-8">
				<p class="text-muted-foreground">
					No saved leads yet. Start searching and save leads you're interested in.
				</p>
			</div>
		{:else}
			<!-- Mobile/Tablet Card View -->
			<div class="block md:hidden space-y-4 p-2">
				{#each $leadsStore as lead (lead.id)}
					<Card>
						<CardHeader>
							<div class="flex justify-between items-start">
								<CardTitle class="text-lg">{lead.displayName}</CardTitle>
								<Button variant="destructive" class="bg-destructive text-destructive-foreground hover:bg-destructive/90 border-2 border-black min-w-[44px] min-h-[44px] gap-2 shadow-[4px_4px_0_0_#000] hover:shadow-none hover:translate-x-1 hover:translate-y-1 px-3 py-2" on:click={() => handleDelete(lead.id)}>
									<Trash class="w-4 h-4" />
									Delete
								</Button>
							</div>
							{#if lead.primaryTypeDisplayName}
								<Badge variant="default" size="sm">
									{lead.primaryTypeDisplayName}
								</Badge>
							{/if}
						</CardHeader>
						<CardContent>
							<div class="space-y-2 text-sm">
								{#if formatPhone(lead.internationalPhoneNumber) !== '-'}
									<div class="flex items-center gap-2">
										<Phone class="w-4 h-4" />
							<strong>Phone:</strong>
										<a href="tel:{lead.internationalPhoneNumber}" class="text-primary hover:underline font-medium">
											{formatPhone(lead.internationalPhoneNumber)}
										</a>
									</div>
								{/if}
								{#if lead.rating}
									<div class="flex items-center gap-2">
								<Star class="w-4 h-4 fill-current text-yellow-500" />
								<strong>Rating:</strong> {lead.rating} ({lead.userRatingCount || 0} reviews)
							</div>
								{/if}
								<div class="flex items-start gap-2">
							<MapPin class="w-4 h-4 mt-0.5 flex-shrink-0" />
							<div><strong>Address:</strong> {lead.formattedAddress}</div>
						</div>
								{#if lead.websiteUri}
									<div class="flex items-center gap-2">
										<Globe class="w-4 h-4" />
								<strong>Website:</strong>
										<a href={lead.websiteUri} target="_blank" rel="noopener noreferrer" class="text-primary hover:underline">
											{new URL(lead.websiteUri).hostname}
										</a>
									</div>
								{/if}
								<div class="text-xs text-muted-foreground"><strong>Saved:</strong> {formatDate(lead.savedAt)}</div>
							</div>
						</CardContent>
					</Card>
				{/each}
			</div>

			<!-- Desktop Table View -->
			<div class="hidden md:block overflow-x-auto">
				<table class="w-full border-2 border-foreground">
					<thead>
						<tr class="bg-muted border-b-2 border-foreground">
							<th class="text-left p-3 font-semibold">Name</th>
							<th class="text-left p-3 font-semibold">Category</th>
							<th class="text-left p-3 font-semibold">Address</th>
							<th class="text-left p-3 font-semibold">Phone</th>
							<th class="text-left p-3 font-semibold">Rating</th>
							<th class="text-left p-3 font-semibold">Saved</th>
							<th class="text-left p-3 font-semibold">Actions</th>
						</tr>
					</thead>
					<tbody>
						{#each $leadsStore as lead, index (lead.id)}
							<tr class="border-b border-border hover:bg-muted/50">
								<td class="p-3">
									<div class="font-medium">{lead.displayName}</div>
									{#if lead.websiteUri}
										<a href={lead.websiteUri} target="_blank" rel="noopener noreferrer"
											class="text-sm text-primary hover:underline">
											Website
										</a>
									{/if}
								</td>
								<td class="p-3">
									{#if lead.primaryTypeDisplayName}
										<Badge variant="default" size="sm">
											{lead.primaryTypeDisplayName}
										</Badge>
									{:else}
										-
									{/if}
								</td>
								<td class="p-3 text-sm max-w-xs truncate" title={lead.formattedAddress}>
									{lead.formattedAddress}
								</td>
								<td class="p-3 text-sm">
									{formatPhone(lead.internationalPhoneNumber)}
								</td>
								<td class="p-3 text-sm">
									{#if lead.rating}
										<div class="flex items-center gap-1">
											<Star class="w-4 h-4 fill-current text-yellow-500" />
											{lead.rating} ({lead.userRatingCount || 0})
										</div>
									{:else}
										-
									{/if}
								</td>
								<td class="p-3 text-sm">
									{formatDate(lead.savedAt)}
								</td>
								<td class="p-3">
									<Button variant="destructive" class="bg-destructive text-destructive-foreground hover:bg-destructive/90 border-2 border-black min-w-[110px] gap-2 shadow-[4px_4px_0_0_#000] hover:shadow-none hover:translate-x-1 hover:translate-y-1" on:click={() => handleDelete(lead.id)}>
										<Trash class="w-4 h-4" />
										Delete
									</Button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>