<script lang="ts">
	import { app } from '$lib/data.svelte';

	let typeFilter = $state('all');
	let sourceFilter = $state('all');
	let searchTerm = $state('');

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
		if (searchTerm) {
			const q = searchTerm.toLowerCase();
			list = list.filter((v: any) => v.description.toLowerCase().includes(q) || v.source_title.toLowerCase().includes(q));
		}
		return list;
	});
</script>

{#if app.visuals && app.visuals.visuals.length > 0}
	<div class="controls">
		<select bind:value={typeFilter}>
			<option value="all">All types ({app.visuals.total_visuals})</option>
			{#each visualTypes as t}<option value={t}>{t}</option>{/each}
		</select>
		<select bind:value={sourceFilter}>
			<option value="all">All sources</option>
			{#each [...sourcesMap.entries()] as [id, title]}<option value={id}>{title}</option>{/each}
		</select>
		<input type="text" placeholder="Search visuals..." bind:value={searchTerm} class="search" />
	</div>

	<div class="grid">
		{#each filtered as vis}
			<div class="visual-card">
				{#if vis.image_path}
					<div class="visual-img">
						<img src="data/images/{vis.image_path}" alt={vis.description} loading="lazy" />
					</div>
				{/if}
				<div class="visual-body">
					<div class="visual-meta">
						<span class="badge badge-primary">{vis.visual_type}</span>
						<span class="dim">{vis.source_title}</span>
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
	.controls { display: flex; gap: var(--space-3); flex-wrap: wrap; margin-bottom: var(--space-6); }
	.controls select, .search { font-family: var(--font-family); font-size: var(--font-size-sm); padding: var(--space-2) var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-sm); }
	.search { flex: 1; max-width: 300px; }
	.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: var(--space-4); }
	.visual-card { border: 1px solid var(--color-border); border-radius: var(--radius-md); overflow: hidden; }
	.visual-img { background: var(--color-surface); padding: var(--space-3); display: flex; justify-content: center; }
	.visual-img img { max-width: 100%; max-height: 300px; object-fit: contain; }
	.visual-body { padding: var(--space-4); }
	.visual-meta { display: flex; gap: var(--space-2); align-items: center; margin-bottom: var(--space-2); }
	.visual-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
	.dim { font-size: var(--font-size-xs); color: var(--color-text-tertiary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }
	.data-details { margin-top: var(--space-3); }
	.data-details summary { font-size: var(--font-size-xs); color: var(--color-primary); cursor: pointer; }
	.data-table-wrap { max-height: 200px; overflow: auto; margin-top: var(--space-2); }
	.data-table-wrap table { font-size: var(--font-size-xs); }
	.summary { font-size: var(--font-size-xs); color: var(--color-text-secondary); margin-top: var(--space-4); }
</style>
