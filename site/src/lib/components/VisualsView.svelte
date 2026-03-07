<script lang="ts">
	import { visualsData, searchQuery } from '$lib/stores/data';
	import type { Visual } from '$lib/types';

	let data = $derived($visualsData);
	let query = $derived($searchQuery);

	let typeFilter = $state('all');
	let sourceFilter = $state('all');

	let visualTypes = $derived(
		data ? [...new Set(data.visuals.map((v) => v.visual_type))].sort() : []
	);

	let sources = $derived(() => {
		if (!data) return [];
		const map = new Map<string, string>();
		for (const v of data.visuals) {
			map.set(v.source_id, v.source_title);
		}
		return [...map.entries()].sort((a, b) => a[1].localeCompare(b[1]));
	});

	let filtered = $derived(() => {
		if (!data) return [];
		let list = data.visuals;
		if (typeFilter !== 'all') {
			list = list.filter((v) => v.visual_type === typeFilter);
		}
		if (sourceFilter !== 'all') {
			list = list.filter((v) => v.source_id === sourceFilter);
		}
		if (query) {
			const q = query.toLowerCase();
			list = list.filter(
				(v) =>
					v.description.toLowerCase().includes(q) ||
					v.source_title.toLowerCase().includes(q) ||
					v.visual_type.toLowerCase().includes(q) ||
					v.section_path.toLowerCase().includes(q)
			);
		}
		return list;
	});

	let selectedVisual = $state<Visual | null>(null);

	function typeBadgeClass(type: string): string {
		switch (type) {
			case 'chart': return 'vtype-chart';
			case 'diagram': return 'vtype-diagram';
			case 'table': return 'vtype-table';
			case 'infographic': return 'vtype-infographic';
			case 'screenshot': return 'vtype-screenshot';
			case 'photo': return 'vtype-photo';
			case 'framework': return 'vtype-framework';
			default: return 'vtype-other';
		}
	}

	function sourceBadgeClass(type: string): string {
		switch (type) {
			case 'pdf': return 'badge-error';
			case 'web': return 'badge-primary';
			case 'youtube': return 'badge-warning';
			default: return 'badge-primary';
		}
	}

	function closeModal() {
		selectedVisual = null;
	}

	function handleBackdropClick(e: MouseEvent) {
		if ((e.target as HTMLElement).classList.contains('modal-backdrop')) {
			closeModal();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') closeModal();
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if !data || data.total_visuals === 0}
	<div class="empty-state">
		<p>No visual extractions available.</p>
		<p class="text-sm text-secondary">Visual data is extracted from figures, charts, and diagrams in collected sources.</p>
	</div>
{:else}
	<div class="visuals-header">
		<div class="visuals-stats">
			<span class="stat-count">{data.total_visuals}</span> visual{data.total_visuals !== 1 ? 's' : ''} extracted
			{#if data.visual_types.length > 0}
				<span class="text-secondary"> &middot; {data.visual_types.length} type{data.visual_types.length !== 1 ? 's' : ''}</span>
			{/if}
		</div>
		<div class="visuals-filters">
			<select class="filter-select" bind:value={typeFilter}>
				<option value="all">All types</option>
				{#each visualTypes as t}
					<option value={t}>{t}</option>
				{/each}
			</select>
			<select class="filter-select" bind:value={sourceFilter}>
				<option value="all">All sources</option>
				{#each sources() as [id, title]}
					<option value={id}>{title.length > 40 ? title.slice(0, 40) + '...' : title}</option>
				{/each}
			</select>
		</div>
	</div>

	<!-- Cards grid -->
	<div class="visuals-grid">
		{#each filtered() as visual}
			<button
				class="visual-card"
				onclick={() => (selectedVisual = visual)}
			>
				{#if visual.image_path}
					<div class="card-image">
						<img src={visual.image_path} alt={visual.description.slice(0, 100)} />
					</div>
				{/if}
				<div class="card-body">
					<div class="card-badges">
						<span class="badge {typeBadgeClass(visual.visual_type)}">{visual.visual_type}</span>
						<span class="badge {sourceBadgeClass(visual.source_type)}">{visual.source_type}</span>
					</div>
					<div class="card-description">{visual.description}</div>
					<div class="card-source text-xs text-secondary">
						{visual.source_title.length > 50 ? visual.source_title.slice(0, 50) + '...' : visual.source_title}
					</div>
				</div>
			</button>
		{/each}
	</div>

	<p class="text-xs text-secondary mt-4">
		{filtered().length} visual{filtered().length !== 1 ? 's' : ''}
		{#if typeFilter !== 'all' || sourceFilter !== 'all' || query} (filtered){/if}
		&middot; Generated {data.generated}
	</p>

	<!-- Modal overlay -->
	{#if selectedVisual}
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="modal-backdrop" onclick={handleBackdropClick}>
			<div class="modal-content">
				<button class="modal-close" onclick={closeModal}>&times;</button>

				{#if selectedVisual.image_path}
					<div class="modal-image">
						<img src={selectedVisual.image_path} alt={selectedVisual.description} />
					</div>
				{/if}

				<div class="modal-info">
					<div class="modal-badges">
						<span class="badge {typeBadgeClass(selectedVisual.visual_type)}">{selectedVisual.visual_type}</span>
						<span class="badge {sourceBadgeClass(selectedVisual.source_type)}">{selectedVisual.source_type}</span>
					</div>
					<p class="modal-description">{selectedVisual.description}</p>
					<div class="modal-source">
						{#if selectedVisual.source_url}
							<a href={selectedVisual.source_url} target="_blank" rel="noopener">{selectedVisual.source_title}</a>
						{:else}
							{selectedVisual.source_title}
						{/if}
						<span class="text-secondary"> &middot; {selectedVisual.source_author}</span>
					</div>
					{#if selectedVisual.section_path}
						<div class="text-xs text-secondary">{selectedVisual.section_path}</div>
					{/if}

					{#if selectedVisual.extracted_data && selectedVisual.extracted_data.length > 0}
						<div class="modal-data">
							<table class="data-table">
								<thead>
									<tr>
										{#each Object.keys(selectedVisual.extracted_data[0]) as key}
											<th>{key}</th>
										{/each}
									</tr>
								</thead>
								<tbody>
									{#each selectedVisual.extracted_data as row}
										<tr>
											{#each Object.values(row) as val}
												<td>{val}</td>
											{/each}
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
{/if}

<style>
	.visuals-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-4);
		flex-wrap: wrap;
		gap: var(--space-3);
	}

	.visuals-stats {
		font-size: var(--font-size-sm);
	}

	.stat-count {
		font-weight: var(--font-weight-semibold);
		font-size: var(--font-size-lg);
	}

	.visuals-filters {
		display: flex;
		gap: var(--space-2);
	}

	.filter-select {
		font-family: var(--font-family);
		font-size: var(--font-size-xs);
		padding: var(--space-1) var(--space-2);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-bg);
		outline: none;
	}

	/* Cards grid */
	.visuals-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: var(--space-3);
		align-content: start;
	}

	.visual-card {
		display: flex;
		flex-direction: column;
		text-align: left;
		padding: 0;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		background: var(--color-bg);
		cursor: pointer;
		font-family: var(--font-family);
		transition: border-color 0.15s, box-shadow 0.15s;
		overflow: hidden;
	}

	.visual-card:hover {
		border-color: var(--color-primary);
		box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
	}

	.card-image {
		background: var(--color-surface);
		max-height: 200px;
		overflow: hidden;
	}

	.card-image img {
		width: 100%;
		height: auto;
		display: block;
		object-fit: cover;
		object-position: top left;
	}

	.card-body {
		padding: var(--space-3);
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.card-badges {
		display: flex;
		gap: var(--space-2);
	}

	.card-description {
		font-size: var(--font-size-sm);
		line-height: var(--line-height-normal);
		display: -webkit-box;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.card-source {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	/* Modal overlay */
	.modal-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.6);
		z-index: 1000;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-4);
	}

	.modal-content {
		background: var(--color-bg);
		border-radius: var(--radius-md);
		max-width: 900px;
		max-height: 90vh;
		width: 100%;
		overflow-y: auto;
		position: relative;
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
	}

	.modal-close {
		position: absolute;
		top: var(--space-2);
		right: var(--space-2);
		z-index: 10;
		font-size: 1.5rem;
		line-height: 1;
		border: none;
		background: rgba(255, 255, 255, 0.8);
		border-radius: var(--radius-full);
		width: 36px;
		height: 36px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		color: var(--color-text-secondary);
		font-family: var(--font-family);
	}

	.modal-close:hover {
		color: var(--color-text);
		background: rgba(255, 255, 255, 1);
	}

	.modal-image {
		background: var(--color-surface);
		display: flex;
		justify-content: center;
		padding: var(--space-4);
	}

	.modal-image img {
		max-width: 100%;
		max-height: 60vh;
		height: auto;
		border-radius: var(--radius-sm);
	}

	.modal-info {
		padding: var(--space-4);
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.modal-badges {
		display: flex;
		gap: var(--space-2);
	}

	.modal-description {
		font-size: var(--font-size-sm);
		line-height: var(--line-height-relaxed);
		margin: 0;
	}

	.modal-source {
		font-size: var(--font-size-sm);
	}

	.modal-source a {
		color: var(--color-primary);
	}

	.modal-data {
		margin-top: var(--space-2);
	}

	.data-table {
		width: 100%;
		font-size: var(--font-size-xs);
		border-collapse: collapse;
	}

	.data-table th,
	.data-table td {
		padding: var(--space-1) var(--space-2);
		border: 1px solid var(--color-border);
		text-align: left;
	}

	.data-table th {
		background: var(--color-surface);
		font-weight: var(--font-weight-semibold);
	}

	/* Visual type badges */
	.vtype-chart { background: #dbeafe; color: #1d4ed8; }
	.vtype-diagram { background: #e0e7ff; color: #3730a3; }
	.vtype-table { background: #fce7f3; color: #be185d; }
	.vtype-infographic { background: #fef3c7; color: #92400e; }
	.vtype-screenshot { background: #f1f5f9; color: #475569; }
	.vtype-photo { background: #d1fae5; color: #065f46; }
	.vtype-framework { background: #f3e8ff; color: #7c3aed; }
	.vtype-other { background: var(--color-surface); color: var(--color-text-secondary); }
</style>
