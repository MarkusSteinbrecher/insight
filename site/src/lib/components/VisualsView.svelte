<script lang="ts">
	import { app } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let typeFilter = $state('all');
	let sourceFilter = $state('all');

	let visualTypes = $derived.by(() => {
		if (!app.visuals) return [];
		return [...new Set(app.visuals.visuals.map((v: any) => v.visual_type))].sort();
	});

	let sourcesMap = $derived.by(() => {
		if (!app.visuals) return new Map<string, string>();
		const m = new Map<string, string>();
		for (const v of app.visuals.visuals) m.set(v.source_id, v.source_title);
		return m;
	});

	let filtered = $derived.by(() => {
		if (!app.visuals) return [];
		let list = app.visuals.visuals;
		if (typeFilter !== 'all') list = list.filter((v: any) => v.visual_type === typeFilter);
		if (sourceFilter !== 'all') list = list.filter((v: any) => v.source_id === sourceFilter);
		if (app.searchQuery) {
			const q = app.searchQuery.toLowerCase();
			list = list.filter((v: any) => v.description.toLowerCase().includes(q) || v.source_title.toLowerCase().includes(q));
		}
		return list;
	});
</script>

{#if app.visuals && app.visuals.visuals.length > 0}
	<div class="toolbar">
		<Icon name="filter" size={15} />
		<select bind:value={typeFilter}>
			<option value="all">All types ({app.visuals.total_visuals})</option>
			{#each visualTypes as t}<option value={t}>{t}</option>{/each}
		</select>
		<select bind:value={sourceFilter}>
			<option value="all">All sources</option>
			{#each [...sourcesMap.entries()] as [id, title]}<option value={id}>{title}</option>{/each}
		</select>
	</div>

	<div class="grid">
		{#each filtered as vis}
			<div class="visual-card">
				{#if vis.image_path}
					<div class="visual-img">
						<img src="data/{app.currentSlug}/images/{vis.image_path}" alt={vis.description} loading="lazy" />
					</div>
				{/if}
				<div class="visual-body">
					<div class="visual-meta">
						<span class="badge badge-primary">{vis.visual_type}</span>
						<span class="source-name">{vis.source_title}</span>
					</div>
					<p class="visual-desc">{vis.description}</p>
					{#if vis.extracted_data?.length}
						<details class="data-details">
							<summary>Extracted data ({vis.extracted_data.length} rows)</summary>
							<div class="data-table-wrap">
								<table>
									<thead><tr>
										{#each Object.keys(vis.extracted_data[0]) as col}<th>{col}</th>{/each}
									</tr></thead>
									<tbody>
										{#each vis.extracted_data as row}
											<tr>{#each Object.values(row) as val}<td>{val}</td>{/each}</tr>
										{/each}
									</tbody>
								</table>
							</div>
						</details>
					{/if}
				</div>
			</div>
		{/each}
	</div>
	<p class="summary">{filtered.length} visual{filtered.length !== 1 ? 's' : ''}</p>
{:else}
	<div class="empty-state"><p>No visuals available.</p></div>
{/if}

<style>
	.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: var(--space-4); }
	.visual-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		overflow: hidden;
		box-shadow: var(--shadow-sm);
		transition: box-shadow 0.15s;
	}
	.visual-card:hover { box-shadow: var(--shadow-md); }
	.visual-img { background: var(--color-bg); padding: var(--space-3); display: flex; justify-content: center; border-bottom: 1px solid var(--color-border-light); }
	.visual-img img { max-width: 100%; max-height: 300px; object-fit: contain; border-radius: var(--radius-sm); }
	.visual-body { padding: var(--space-4); }
	.visual-meta { display: flex; gap: var(--space-2); align-items: center; margin-bottom: var(--space-2); }
	.source-name { font-size: var(--font-size-xs); color: var(--color-text-tertiary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }
	.visual-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
	.data-details { margin-top: var(--space-3); }
	.data-details summary { font-size: var(--font-size-xs); color: var(--color-primary-text); cursor: pointer; font-weight: var(--font-weight-medium); }
	.data-table-wrap { max-height: 200px; overflow: auto; margin-top: var(--space-2); }
	.data-table-wrap table { font-size: var(--font-size-xs); }
	.summary { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-top: var(--space-4); }
</style>
