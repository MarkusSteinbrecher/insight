<script lang="ts">
	import { app } from '$lib/data.svelte';

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
		if (categoryFilter === 'all') return app.findings.findings;
		return app.findings.findings.filter((f: any) => f.category === categoryFilter);
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
	<div class="controls">
		<select bind:value={categoryFilter}>
			<option value="all">All categories ({app.findings.total_findings})</option>
			{#each categories as cat}
				<option value={cat}>{cat}</option>
			{/each}
		</select>
	</div>

	{#each filtered as finding}
		<div class="finding-card">
			<button class="finding-header" onclick={() => toggleFinding(finding.id)}>
				<div>
					<span class="badge badge-primary">{finding.category}</span>
					<h3 class="finding-title">{finding.title}</h3>
					<p class="finding-desc">{finding.description}</p>
				</div>
				<span class="count">{finding.claim_count} claims</span>
			</button>

			{#if expandedFinding === finding.id}
				<div class="claims">
					{#each finding.claims as claim}
						<div class="claim">
							<button class="claim-header" onclick={() => toggleClaim(claim.id)}>
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
										<span class="badge badge-{claim.baseline_category === 'novel' ? 'success' : claim.baseline_category === 'common-knowledge' ? 'warning' : 'primary'}">{claim.baseline_category}</span>
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
{:else}
	<div class="empty-state"><p>No findings available.</p></div>
{/if}

<style>
	.controls { margin-bottom: var(--space-6); }
	.controls select { font-family: var(--font-family); font-size: var(--font-size-sm); padding: var(--space-2) var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-sm); }
	.finding-card { border: 1px solid var(--color-border); border-radius: var(--radius-md); margin-bottom: var(--space-4); overflow: hidden; }
	.finding-header { display: flex; justify-content: space-between; align-items: flex-start; width: 100%; padding: var(--space-5); background: none; border: none; cursor: pointer; text-align: left; font-family: var(--font-family); }
	.finding-header:hover { background: var(--color-surface); }
	.finding-title { font-size: var(--font-size-base); font-weight: var(--font-weight-semibold); margin-top: var(--space-2); }
	.finding-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: var(--space-1); }
	.count { font-size: var(--font-size-xs); color: var(--color-text-tertiary); white-space: nowrap; margin-left: var(--space-4); }
	.claims { border-top: 1px solid var(--color-border); }
	.claim { border-bottom: 1px solid var(--color-border-light); }
	.claim:last-child { border-bottom: none; }
	.claim-header { display: flex; align-items: baseline; gap: var(--space-3); width: 100%; padding: var(--space-3) var(--space-5); background: none; border: none; cursor: pointer; text-align: left; font-family: var(--font-family); font-size: var(--font-size-sm); }
	.claim-header:hover { background: var(--color-surface); }
	.claim-id { font-size: var(--font-size-xs); color: var(--color-text-tertiary); font-weight: var(--font-weight-medium); flex-shrink: 0; }
	.claim-text { flex: 1; }
	.claim-sources { font-size: var(--font-size-xs); color: var(--color-text-tertiary); flex-shrink: 0; }
	.claim-detail { padding: var(--space-3) var(--space-5) var(--space-5) calc(var(--space-5) + 4rem); }
	.bottom-line { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-3); font-style: italic; }
	.source-list { margin-top: var(--space-3); }
	.source-ref { margin-bottom: var(--space-3); font-size: var(--font-size-sm); }
	.dim { color: var(--color-text-secondary); }
	blockquote { margin: var(--space-2) 0; padding-left: var(--space-4); border-left: 2px solid var(--color-border); font-size: var(--font-size-sm); color: var(--color-text-secondary); }
</style>
