<script lang="ts">
	import { app, shortId } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let sortKey = $state<string>('title');
	let sortAsc = $state(true);
	let typeFilter = $state('all');

	const statusSteps = ['discovered', 'collected', 'extracted', 'analyzed'] as const;
	function statusLevel(status: string | undefined): number {
		if (!status || status === 'failed') return -1;
		return statusSteps.indexOf(status as any);
	}

	let sourceTypes = $derived.by(() => {
		if (!app.sources) return [];
		const types = new Set(app.sources.sources.map((s: any) => s.type));
		return [...types].sort();
	});

	let typeCounts = $derived.by(() => {
		if (!app.sources) return new Map<string, number>();
		const counts = new Map<string, number>();
		for (const s of app.sources.sources) {
			counts.set(s.type, (counts.get(s.type) || 0) + 1);
		}
		return counts;
	});

	let sorted = $derived.by(() => {
		if (!app.sources) return [];
		let list = [...app.sources.sources];
		if (typeFilter !== 'all') list = list.filter((s: any) => s.type === typeFilter);
		if (app.searchQuery) {
			const q = app.searchQuery.toLowerCase();
			list = list.filter((s: any) => s.title.toLowerCase().includes(q) || (s.author && s.author.toLowerCase().includes(q)));
		}
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

{#if app.sources}
	<div class="toolbar">
		<div class="category-nav">
			<button class="cat-pill" class:active={typeFilter === 'all'} onclick={() => typeFilter = 'all'}>
				All <span class="cat-count">{app.sources.sources.length}</span>
			</button>
			{#each sourceTypes as t}
				<button class="cat-pill" class:active={typeFilter === t} onclick={() => typeFilter = t}>
					{#if t === 'web'}<Icon name="globe" size={13} />
					{:else if t === 'youtube'}<Icon name="youtube" size={13} />
					{:else if t === 'pdf'}<Icon name="file-text" size={13} />
					{:else}<Icon name="sources" size={13} />
					{/if}
					{t} <span class="cat-count">{typeCounts.get(t) ?? 0}</span>
				</button>
			{/each}
		</div>
	</div>

	<div class="table-wrap">
		<table>
			<thead>
				<tr>
					<th class="col-num">ID</th>
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
					<th class="sortable" onclick={() => toggleSort('status')}>
						Status
						{#if sortKey === 'status'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
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
						<td class="col-num dim">{source.id ? shortId(source.id) : '\u2014'}</td>
						<td class="col-title" title={source.title}>
							{#if source.url}
								<a href={source.url} target="_blank" rel="noopener">
									<span>{source.title}</span>
									<Icon name="external" size={11} />
								</a>
							{:else}
								{source.title}
							{/if}
						</td>
						<td class="col-author dim" title={source.author}>{source.author || '\u2014'}</td>
						<td class="col-type" title={source.type}>
							{#if source.type === 'web'}
								<Icon name="globe" size={16} />
							{:else if source.type === 'youtube'}
								<Icon name="youtube" size={16} />
							{:else if source.type === 'pdf'}
								<Icon name="file-text" size={16} />
							{:else}
								<Icon name="sources" size={16} />
							{/if}
						</td>
						<td class="col-status">
							{#if source.status === 'failed'}
								<span class="status-failed-label">failed</span>
							{:else}
								{@const level = statusLevel(source.status)}
								<div class="status-steps" title={source.status ?? ''}>
									{#each statusSteps as step, i}
										<div class="step" class:done={i < level} class:current={i === level} class:open={i > level}></div>
									{/each}
								</div>
							{/if}
						</td>
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
	<div class="empty-state"><p>No source data available.</p></div>
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
	.category-nav {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2);
	}
	.cat-pill {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
		padding: var(--space-1) var(--space-3);
		border-radius: var(--radius-full, 9999px);
		border: 1px solid var(--color-border-light);
		background: var(--color-surface);
		font-size: var(--font-size-sm);
		font-family: var(--font-family);
		color: var(--color-text-secondary);
		cursor: pointer;
		transition: all 0.15s;
	}
	.cat-pill:hover {
		border-color: var(--color-border);
		color: var(--color-text);
	}
	.cat-pill.active {
		background: var(--color-text);
		border-color: var(--color-text);
		color: var(--color-surface);
		font-weight: var(--font-weight-medium);
	}
	.cat-count {
		font-size: var(--font-size-xs);
		opacity: 0.7;
	}
	.col-num { text-align: center; width: 60px; white-space: nowrap; }
	.col-title { max-width: 480px; }
	.col-title a {
		font-weight: var(--font-weight-medium);
		display: inline-flex;
		align-items: center;
		gap: 4px;
	}
	.col-author { max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.col-type { text-align: center; color: var(--color-text-tertiary); }
	.dim { color: var(--color-text-secondary); }
	.col-status { white-space: nowrap; }
	.status-steps {
		display: inline-flex;
		gap: 3px;
		align-items: center;
	}
	.step {
		width: 14px;
		height: 8px;
		border-radius: 2px;
		border: 1px solid var(--color-border-light);
	}
	.step.done { background: var(--color-success); border-color: var(--color-success); }
	.step.current { background: var(--color-warning); border-color: var(--color-warning); }
	.step.open { background: var(--color-surface); }
	.status-failed-label {
		font-size: var(--font-size-xs);
		color: var(--color-error);
		font-weight: var(--font-weight-medium);
	}
	thead tr { background: var(--color-surface); }
	tbody tr:hover td { background: var(--color-surface-hover); }
	tbody tr:last-child td { border-bottom: none; }
	.summary { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-top: var(--space-3); }
</style>
