<script lang="ts">
	import { app } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let sortKey = $state<string>('title');
	let sortAsc = $state(true);

	let sorted = $derived.by(() => {
		if (!app.sources) return [];
		let list = [...app.sources.sources];
		list.sort((a: any, b: any) => {
			const av = a[sortKey], bv = b[sortKey];
			if (typeof av === 'number' && typeof bv === 'number') return sortAsc ? av - bv : bv - av;
			return sortAsc ? String(av ?? '').localeCompare(String(bv ?? '')) : String(bv ?? '').localeCompare(String(av ?? ''));
		});
		return list;
	});

	function toggleSort(key: string) {
		if (sortKey === key) { sortAsc = !sortAsc; } else { sortKey = key; sortAsc = true; }
	}
</script>

{#if sorted.length > 0}
	<div class="table-wrap">
		<table>
			<thead>
				<tr>
					<th class="col-num">#</th>
					<th class="sortable" onclick={() => toggleSort('title')}>
						Title
						{#if sortKey === 'title'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
					</th>
					<th class="sortable" onclick={() => toggleSort('author')}>
						Author
						{#if sortKey === 'author'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
					</th>
					<th class="sortable" onclick={() => toggleSort('type')}>
						Type
						{#if sortKey === 'type'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
					</th>
					<th class="sortable col-num" onclick={() => toggleSort('extract_count')}>
						Extracts
						{#if sortKey === 'extract_count'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
					</th>
					<th class="sortable col-num" onclick={() => toggleSort('claim_count')}>
						Claims
						{#if sortKey === 'claim_count'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
					</th>
					<th class="sortable col-num" onclick={() => toggleSort('finding_count')}>
						Findings
						{#if sortKey === 'finding_count'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
					</th>
				</tr>
			</thead>
			<tbody>
				{#each sorted as source, i}
					<tr>
						<td class="col-num dim">{i + 1}</td>
						<td class="col-title">
							{#if source.url}
								<a href={source.url} target="_blank" rel="noopener">
									{source.title}
									<Icon name="external" size={11} />
								</a>
							{:else}
								{source.title}
							{/if}
						</td>
						<td class="dim">{source.author || '\u2014'}</td>
						<td><span class="badge badge-{source.type === 'web' ? 'info' : source.type === 'pdf' ? 'warning' : 'success'}">{source.type}</span></td>
						<td class="col-num">{source.extract_count ?? 0}</td>
						<td class="col-num">{source.claim_count ?? 0}</td>
						<td class="col-num">{source.finding_count ?? 0}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	<p class="summary">{sorted.length} sources &middot; Updated {app.sources?.updated ?? ''}</p>
{:else}
	<div class="empty-state"><p>No sources available.</p></div>
{/if}

<style>
	.table-wrap {
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		overflow-x: auto;
	}
	.sortable { cursor: pointer; user-select: none; white-space: nowrap; }
	.sortable :global(.icon) { margin-left: 2px; vertical-align: middle; }
	.sortable:hover { color: var(--color-text); }
	.col-num { text-align: center; width: 70px; }
	.col-title { max-width: 400px; }
	.col-title a {
		font-weight: var(--font-weight-medium);
		display: inline-flex;
		align-items: center;
		gap: 4px;
	}
	.dim { color: var(--color-text-secondary); }
	thead tr { background: var(--color-surface); }
	tbody tr:hover td { background: var(--color-surface-hover); }
	tbody tr:last-child td { border-bottom: none; }
	.summary { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-top: var(--space-3); }
</style>
