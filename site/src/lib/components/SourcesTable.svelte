<script lang="ts">
	import { sourcesData, searchQuery, activeTab, deepDiveSourceId } from '$lib/stores/data';
	import type { Source } from '$lib/types';

	let data = $derived($sourcesData);
	let query = $derived($searchQuery);

	let sortKey = $state<keyof Source>('title');
	let sortAsc = $state(true);

	let filtered = $derived(() => {
		if (!data) return [];
		let list = data.sources;
		if (query) {
			const q = query.toLowerCase();
			list = list.filter(
				(s) =>
					s.title.toLowerCase().includes(q) ||
					s.author.toLowerCase().includes(q) ||
					s.type.toLowerCase().includes(q)
			);
		}
		return [...list].sort((a, b) => {
			const av = a[sortKey];
			const bv = b[sortKey];
			if (typeof av === 'number' && typeof bv === 'number') {
				return sortAsc ? av - bv : bv - av;
			}
			const as = String(av).toLowerCase();
			const bs = String(bv).toLowerCase();
			return sortAsc ? as.localeCompare(bs) : bs.localeCompare(as);
		});
	});

	function toggleSort(key: keyof Source) {
		if (sortKey === key) {
			sortAsc = !sortAsc;
		} else {
			sortKey = key;
			sortAsc = true;
		}
	}

	function sortIndicator(key: keyof Source): string {
		if (sortKey !== key) return '';
		return sortAsc ? ' \u2191' : ' \u2193';
	}

	function goToDeepDive(sourceId: string) {
		deepDiveSourceId.set(sourceId);
		activeTab.set('deep-dive');
		if (typeof window !== 'undefined') {
			window.location.hash = 'deep-dive';
		}
	}
</script>

<div class="sources-view">
	{#if filtered().length > 0}
		<div class="table-wrapper">
			<table>
				<thead>
					<tr>
						<th class="col-num">#</th>
						<th class="sortable" onclick={() => toggleSort('title')}
							>Title{sortIndicator('title')}</th
						>
						<th class="sortable" onclick={() => toggleSort('author')}
							>Author{sortIndicator('author')}</th
						>
						<th class="sortable" onclick={() => toggleSort('type')}
							>Type{sortIndicator('type')}</th
						>
						<th class="sortable col-count" onclick={() => toggleSort('extract_count')}
							>Extracts{sortIndicator('extract_count')}</th
						>
						<th class="sortable col-count" onclick={() => toggleSort('claim_count')}
							>Claims{sortIndicator('claim_count')}</th
						>
						<th class="sortable col-count" onclick={() => toggleSort('finding_count')}
							>Findings{sortIndicator('finding_count')}</th
						>
					</tr>
				</thead>
				<tbody>
					{#each filtered() as source, i}
						<tr>
							<td class="col-num row-num">{i + 1}</td>
							<td class="col-title">
								<div class="title-cell">
									{#if source.url}
										<a href={source.url} target="_blank" rel="noopener"
											>{source.title}</a
										>
									{:else}
										<span>{source.title}</span>
									{/if}
								</div>
							</td>
							<td class="col-author">{source.author || '\u2014'}</td>
							<td>
								<span
									class="badge badge-{source.type === 'web'
										? 'primary'
										: source.type === 'pdf'
											? 'warning'
											: 'success'}">{source.type}</span
								>
							</td>
							<td class="col-count">
								<button
									class="count-link count-extract"
									onclick={() => goToDeepDive(source.id)}
									title="View in Deep Dive"
								>
									{source.extract_count}
								</button>
							</td>
							<td class="col-count">
								{#if source.claim_count > 0}
									<button
										class="count-link count-claim"
										onclick={() => goToDeepDive(source.id)}
										title="View claims in Deep Dive"
									>
										{source.claim_count}
									</button>
								{:else}
									<span class="count-zero">{source.claim_count}</span>
								{/if}
							</td>
							<td class="col-count">
								{#if source.finding_count > 0}
									<button
										class="count-link count-finding"
										onclick={() => goToDeepDive(source.id)}
										title="View findings in Deep Dive"
									>
										{source.finding_count}
									</button>
								{:else}
									<span class="count-zero">{source.finding_count}</span>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="summary">
			{filtered().length} source{filtered().length !== 1 ? 's' : ''}
			{#if query} matching "{query}"{/if}
			{#if data} &middot; Updated {data.updated}{/if}
		</p>
	{:else}
		<div class="empty-state">
			{#if query}
				<p>No sources match "{query}"</p>
			{:else}
				<p>No sources available.</p>
			{/if}
		</div>
	{/if}
</div>

<style>
	.table-wrapper {
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		overflow: hidden;
	}

	table {
		border-collapse: collapse;
	}

	thead tr {
		background: var(--color-surface);
	}

	th {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--color-text-secondary);
		padding: var(--space-3) var(--space-4);
		border-bottom: 1px solid var(--color-border);
	}

	td {
		padding: var(--space-3) var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
		font-size: var(--font-size-sm);
		vertical-align: middle;
	}

	tbody tr:last-child td {
		border-bottom: none;
	}

	tbody tr:hover td {
		background: var(--color-surface);
	}

	.sortable {
		cursor: pointer;
		user-select: none;
		transition: color 0.15s;
	}

	.sortable:hover {
		color: var(--color-text);
	}

	.col-num {
		width: 40px;
		text-align: center;
	}

	.row-num {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		font-weight: var(--font-weight-medium);
	}

	.col-title {
		max-width: 400px;
	}

	.title-cell {
		line-height: var(--line-height-tight);
	}

	.title-cell a {
		font-weight: var(--font-weight-medium);
	}

	.col-author {
		color: var(--color-text-secondary);
		max-width: 160px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.col-count {
		text-align: center;
		width: 80px;
	}

	.count-link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 28px;
		padding: 2px 8px;
		font-family: var(--font-family);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		border: none;
		border-radius: var(--radius-full);
		cursor: pointer;
		transition:
			background 0.15s,
			color 0.15s;
	}

	.count-extract {
		background: var(--color-surface);
		color: var(--color-text-secondary);
	}

	.count-extract:hover {
		background: var(--color-surface-hover);
		color: var(--color-text);
	}

	.count-claim {
		background: var(--color-primary-light);
		color: var(--color-primary);
	}

	.count-claim:hover {
		background: var(--color-primary);
		color: white;
	}

	.count-finding {
		background: var(--color-success-bg);
		color: #16a34a;
	}

	.count-finding:hover {
		background: #16a34a;
		color: white;
	}

	.count-zero {
		color: var(--color-text-tertiary);
	}

	.summary {
		font-size: var(--font-size-xs);
		color: var(--color-text-secondary);
		margin-top: var(--space-4);
	}
</style>
