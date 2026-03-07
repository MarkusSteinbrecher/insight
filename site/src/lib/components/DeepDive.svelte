<script lang="ts">
	import { app } from '$lib/data.svelte';
	import type { AuditSource, AuditExtract } from '$lib/data.svelte';

	let selectedIdx = $state(0);
	let extractTypeFilter = $state('all');
	let searchTerm = $state('');

	let sources = $derived.by(() => app.audit?.sources ?? []);
	let selected = $derived.by(() => sources[selectedIdx] ?? null);

	let extractTypes = $derived.by(() => {
		if (!selected) return [];
		return [...new Set(selected.extracts.map((e: AuditExtract) => e.extract_type))].sort();
	});

	let filteredExtracts = $derived.by(() => {
		if (!selected) return [];
		let list = selected.extracts;
		if (extractTypeFilter !== 'all') list = list.filter((e: AuditExtract) => e.extract_type === extractTypeFilter);
		if (searchTerm) {
			const q = searchTerm.toLowerCase();
			list = list.filter((e: AuditExtract) => e.text.toLowerCase().includes(q));
		}
		return list;
	});
</script>

{#if sources.length > 0}
	<div class="deep-dive">
		<div class="source-list">
			<div class="list-header">Sources ({sources.length})</div>
			{#each sources as src, i}
				<button class="source-item" class:active={selectedIdx === i} onclick={() => { selectedIdx = i; }}>
					<span class="source-num">{i + 1}</span>
					<span class="source-name">{src.title}</span>
					<span class="source-count">{src.extract_count}</span>
				</button>
			{/each}
		</div>

		<div class="source-detail">
			{#if selected}
				<h2 class="detail-title">{selected.title}</h2>
				<p class="detail-meta">
					{selected.author} &middot; {selected.type}
					{#if selected.url} &middot; <a href={selected.url} target="_blank" rel="noopener">source</a>{/if}
				</p>

				<div class="controls">
					<select bind:value={extractTypeFilter}>
						<option value="all">All types ({selected.extracts.length})</option>
						{#each extractTypes as t}
							<option value={t}>{t}</option>
						{/each}
					</select>
					<input type="text" placeholder="Search extracts..." bind:value={searchTerm} class="search-input" />
				</div>

				<div class="extracts">
					{#each filteredExtracts as ext}
						<div class="extract">
							<div class="extract-meta">
								<span class="badge badge-primary">{ext.extract_type}</span>
								<span class="dim">{ext.section}</span>
							</div>
							<p class="extract-text">{ext.text}</p>
							{#if ext.claims?.length}
								<div class="extract-claims">
									{#each ext.claims as c}
										<span class="claim-tag" title={c.summary}>
											{c.claim_id}
											{#if c.finding}
												<span class="finding-tag">{c.finding.finding_title}</span>
											{/if}
										</span>
									{/each}
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
{:else}
	<div class="empty-state"><p>No audit data available.</p></div>
{/if}

<style>
	.deep-dive { display: grid; grid-template-columns: 280px 1fr; gap: var(--space-4); min-height: 600px; }
	.source-list { border: 1px solid var(--color-border); border-radius: var(--radius-md); overflow-y: auto; max-height: 80vh; }
	.list-header { font-size: var(--font-size-xs); font-weight: var(--font-weight-semibold); text-transform: uppercase; padding: var(--space-3) var(--space-4); color: var(--color-text-secondary); background: var(--color-surface); border-bottom: 1px solid var(--color-border); }
	.source-item { display: flex; gap: var(--space-2); align-items: center; width: 100%; padding: var(--space-2) var(--space-4); background: none; border: none; border-bottom: 1px solid var(--color-border-light); cursor: pointer; font-family: var(--font-family); font-size: var(--font-size-xs); text-align: left; }
	.source-item:hover { background: var(--color-surface); }
	.source-item.active { background: var(--color-primary-light); }
	.source-num { color: var(--color-text-tertiary); width: 20px; flex-shrink: 0; }
	.source-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.source-count { color: var(--color-text-tertiary); flex-shrink: 0; }
	.source-detail { overflow-y: auto; }
	.detail-title { font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); }
	.detail-meta { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--space-4); }
	.controls { display: flex; gap: var(--space-3); margin-bottom: var(--space-4); }
	.controls select { font-family: var(--font-family); font-size: var(--font-size-sm); padding: var(--space-2) var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-sm); }
	.search-input { font-family: var(--font-family); font-size: var(--font-size-sm); padding: var(--space-2) var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-sm); flex: 1; max-width: 300px; }
	.extracts { display: flex; flex-direction: column; gap: var(--space-3); }
	.extract { border: 1px solid var(--color-border-light); border-radius: var(--radius-sm); padding: var(--space-3) var(--space-4); }
	.extract-meta { display: flex; gap: var(--space-2); align-items: center; margin-bottom: var(--space-2); }
	.extract-text { font-size: var(--font-size-sm); line-height: var(--line-height-normal); }
	.extract-claims { margin-top: var(--space-2); display: flex; flex-wrap: wrap; gap: var(--space-1); }
	.claim-tag { font-size: var(--font-size-xs); background: var(--color-surface); padding: 2px 6px; border-radius: var(--radius-sm); color: var(--color-text-secondary); }
	.finding-tag { margin-left: var(--space-1); color: var(--color-success); }
	.dim { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
</style>
