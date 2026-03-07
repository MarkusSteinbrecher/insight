<script lang="ts">
	import { app } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let expandedFinding = $state<string | null>(null);
	let expandedClaim = $state<string | null>(null);
	let categoryFilter = $state('all');

	let categories = $derived.by(() => {
		if (!app.findings) return [];
		const cats = new Set(app.findings.findings.map((f: any) => f.category));
		return [...cats].sort();
	});

	let filtered = $derived.by(() => {
		if (!app.findings) return [];
		let list = app.findings.findings;
		if (categoryFilter !== 'all') list = list.filter((f: any) => f.category === categoryFilter);
		if (app.searchQuery) {
			const q = app.searchQuery.toLowerCase();
			list = list.filter((f: any) => f.title.toLowerCase().includes(q) || f.description.toLowerCase().includes(q));
		}
		return list;
	});

	function toggleFinding(id: string) {
		expandedFinding = expandedFinding === id ? null : id;
		expandedClaim = null;
	}

	function toggleClaim(id: string) {
		expandedClaim = expandedClaim === id ? null : id;
	}
</script>

{#if app.findings}
	<div class="toolbar">
		<Icon name="filter" size={15} />
		<select bind:value={categoryFilter}>
			<option value="all">All categories ({app.findings.total_findings})</option>
			{#each categories as cat}
				<option value={cat}>{cat}</option>
			{/each}
		</select>
	</div>

	<div class="findings-list">
		{#each filtered as finding}
			<div class="finding-card" class:expanded={expandedFinding === finding.id}>
				<button class="finding-header" onclick={() => toggleFinding(finding.id)}>
					<div class="finding-icon">
						<Icon name={expandedFinding === finding.id ? 'chevron-down' : 'chevron-right'} size={16} />
					</div>
					<div class="finding-info">
						<div class="finding-meta">
							<span class="badge badge-finding">{finding.category}</span>
							<span class="claim-count">{finding.claim_count} claims</span>
						</div>
						<h3 class="finding-title">{finding.title}</h3>
						<p class="finding-desc">{finding.description}</p>
					</div>
				</button>

				{#if expandedFinding === finding.id}
					<div class="claims">
						{#each finding.claims as claim}
							<div class="claim" class:expanded={expandedClaim === claim.id}>
								<button class="claim-header" onclick={() => toggleClaim(claim.id)}>
									<Icon name={expandedClaim === claim.id ? 'chevron-down' : 'chevron-right'} size={14} />
									<span class="claim-id">{claim.id}</span>
									<span class="claim-text">{claim.statement}</span>
									<span class="claim-sources">{claim.source_count} sources</span>
								</button>
								{#if expandedClaim === claim.id}
									<div class="claim-detail">
										{#if claim.bottom_line}
											<p class="bottom-line">{claim.bottom_line}</p>
										{/if}
										{#if claim.baseline_category}
											<span class="badge badge-{claim.baseline_category === 'novel' ? 'success' : claim.baseline_category === 'common-knowledge' ? 'warning' : 'info'}">{claim.baseline_category}</span>
										{/if}
										{#if claim.sources?.length}
											<div class="source-list">
												{#each claim.sources as src}
													<div class="source-ref">
														<a href={src.url} target="_blank" rel="noopener">{src.title}</a>
														<span class="dim"> — {src.author}</span>
														{#each src.quotes as q}
															<blockquote>{q}</blockquote>
														{/each}
													</div>
												{/each}
											</div>
										{/if}
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	</div>
{:else}
	<div class="empty-state"><p>No findings available.</p></div>
{/if}

<style>
	.findings-list { display: flex; flex-direction: column; gap: var(--space-3); }
	.finding-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		overflow: hidden;
		transition: box-shadow 0.15s;
	}
	.finding-card:hover { box-shadow: var(--shadow-md); }
	.finding-card.expanded { box-shadow: var(--shadow-md); border-color: var(--color-border); }
	.finding-header {
		display: flex;
		align-items: flex-start;
		gap: var(--space-3);
		width: 100%;
		padding: var(--space-4) var(--space-5);
		background: none;
		border: none;
		cursor: pointer;
		text-align: left;
		font-family: var(--font-family);
	}
	.finding-header:hover { background: var(--color-surface-hover); }
	.finding-icon { color: var(--color-text-tertiary); margin-top: 2px; }
	.finding-info { flex: 1; min-width: 0; }
	.finding-meta { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-2); }
	.claim-count { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
	.finding-title { font-size: var(--font-size-base); font-weight: var(--font-weight-semibold); line-height: var(--line-height-tight); }
	.finding-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: var(--space-1); line-height: var(--line-height-normal); }

	.claims { border-top: 1px solid var(--color-border-light); }
	.claim { border-bottom: 1px solid var(--color-border-light); }
	.claim:last-child { border-bottom: none; }
	.claim-header {
		display: flex;
		align-items: baseline;
		gap: var(--space-2);
		width: 100%;
		padding: var(--space-3) var(--space-5);
		background: none;
		border: none;
		cursor: pointer;
		text-align: left;
		font-family: var(--font-family);
		font-size: var(--font-size-sm);
		color: var(--color-text);
	}
	.claim-header :global(.icon) { flex-shrink: 0; margin-top: 2px; color: var(--color-text-tertiary); }
	.claim-header:hover { background: var(--color-surface-hover); }
	.claim-id { font-size: var(--font-size-xs); color: var(--color-claim); font-weight: var(--font-weight-medium); flex-shrink: 0; font-family: monospace; }
	.claim-text { flex: 1; }
	.claim-sources { font-size: var(--font-size-xs); color: var(--color-text-tertiary); flex-shrink: 0; }
	.claim-detail { padding: var(--space-3) var(--space-5) var(--space-5) calc(var(--space-5) + 3rem); }
	.bottom-line { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-3); font-style: italic; }
	.source-list { margin-top: var(--space-3); }
	.source-ref { margin-bottom: var(--space-3); font-size: var(--font-size-sm); }
	.dim { color: var(--color-text-secondary); }
	blockquote { margin: var(--space-2) 0; padding-left: var(--space-4); border-left: 2px solid var(--color-primary-light); font-size: var(--font-size-sm); color: var(--color-text-secondary); }
</style>
