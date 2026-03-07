<script lang="ts">
	import { auditData } from '$lib/stores/data';
	import type { AuditSource } from '$lib/types';

	let data = $derived($auditData);
	let sources = $derived(data?.sources ?? []);

	let selectedIndex = $state(0);
	let selected = $derived<AuditSource | null>(sources[selectedIndex] ?? null);
	let typeFilter = $state('all');
	let searchTerm = $state('');
	let leftView = $state<'original' | 'notes'>('original');
	let formatFilter = $state('all');
	let extractTypeFilter = $state('all');

	let extractFormats = $derived(
		selected ? [...new Set(selected.extracts.map((e: any) => e.format))].sort() : []
	);

	let extractTypes = $derived(
		selected ? [...new Set(selected.extracts.map((e: any) => e.extract_type))].sort() : []
	);

	let filteredExtractSections = $derived.by(() => {
		if (!selected) return {};
		const sections = selected.extract_sections;
		if (formatFilter === 'all' && extractTypeFilter === 'all') return sections;
		const result: Record<string, any[]> = {};
		for (const [section, extracts] of Object.entries(sections)) {
			const filtered = (extracts as any[]).filter((e) => {
				if (formatFilter !== 'all' && e.format !== formatFilter) return false;
				if (extractTypeFilter !== 'all' && e.extract_type !== extractTypeFilter) return false;
				return true;
			});
			if (filtered.length > 0) result[section] = filtered;
		}
		return result;
	});

	let filteredSources = $derived(
		sources.filter((s) => {
			if (typeFilter !== 'all' && s.type !== typeFilter) return false;
			if (searchTerm) {
				const q = searchTerm.toLowerCase();
				return (
					s.title.toLowerCase().includes(q) ||
					s.author.toLowerCase().includes(q) ||
					s.id.toLowerCase().includes(q)
				);
			}
			return true;
		})
	);

	let sourceTypes = $derived([...new Set(sources.map((s) => s.type))].sort());

	function selectSource(idx: number) {
		selectedIndex = sources.indexOf(filteredSources[idx]);
	}

	function typeBadgeClass(type: string): string {
		switch (type) {
			case 'pdf': return 'badge-error';
			case 'web': return 'badge-primary';
			case 'youtube': return 'badge-warning';
			default: return 'badge-primary';
		}
	}

	function formatBadgeClass(format: string): string {
		switch (format) {
			case 'prose': return 'format-prose';
			case 'bullet': return 'format-bullet';
			case 'heading': return 'format-heading';
			case 'table': return 'format-table';
			case 'quote': return 'format-quote';
			default: return 'format-other';
		}
	}

	function extractTypeBadgeClass(etype: string): string {
		switch (etype) {
			case 'claim': return 'etype-claim';
			case 'statistic': return 'etype-statistic';
			case 'evidence': return 'etype-evidence';
			case 'recommendation': return 'etype-recommendation';
			case 'definition': return 'etype-definition';
			case 'context': return 'etype-context';
			case 'noise': return 'etype-noise';
			default: return 'etype-other';
		}
	}

	function embedLabel(source: AuditSource): string {
		switch (source.type) {
			case 'pdf': return 'PDF';
			case 'youtube': return 'Video';
			case 'web': return 'Webpage';
			default: return 'Source';
		}
	}
</script>

{#if !data}
	<div class="empty-state">No audit data available.</div>
{:else}
	<div class="audit-layout">
		<!-- Source selector sidebar -->
		<div class="source-list">
			<div class="list-header">
				<div class="list-title">{filteredSources.length} Sources</div>
				<div class="list-filters">
					<select class="filter-select" bind:value={typeFilter}>
						<option value="all">All types</option>
						{#each sourceTypes as t}
							<option value={t}>{t}</option>
						{/each}
					</select>
					<input
						class="filter-search"
						type="text"
						placeholder="Filter..."
						bind:value={searchTerm}
					/>
				</div>
			</div>
			<div class="list-items">
				{#each filteredSources as source, i}
					<button
						class="source-item"
						class:active={sources.indexOf(source) === selectedIndex}
						onclick={() => selectSource(i)}
					>
						<div class="source-item-header">
							<span class="badge {typeBadgeClass(source.type)}">{source.type}</span>
							<span class="text-xs text-secondary">{source.extract_count} extracts</span>
						</div>
						<div class="source-item-title">{source.title}</div>
						<div class="source-item-author text-xs text-secondary">{source.author}</div>
					</button>
				{/each}
			</div>
		</div>

		<!-- Split content area -->
		{#if selected}
			<div class="split-view">
				<!-- Left: Original source or notes -->
				<div class="panel panel-left">
					<div class="panel-header">
						<div class="panel-tabs">
							<button
								class="panel-tab"
								class:active={leftView === 'original'}
								onclick={() => (leftView = 'original')}
							>
								{embedLabel(selected)}
							</button>
							<button
								class="panel-tab"
								class:active={leftView === 'notes'}
								onclick={() => (leftView = 'notes')}
							>
								Notes
							</button>
						</div>
						<div class="panel-meta">
							<span class="badge {typeBadgeClass(selected.type)}">{selected.type}</span>
							{#if selected.url}
								<a href={selected.url} target="_blank" class="text-xs">Open in new tab</a>
							{/if}
						</div>
					</div>

					{#if leftView === 'original'}
						<div class="panel-embed">
							{#if selected.embed_url}
								{#if selected.type === 'youtube'}
									<iframe
										src={selected.embed_url}
										title={selected.title}
										class="embed-frame"
										allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
										allowfullscreen
									></iframe>
								{:else if selected.type === 'pdf' && !selected.embed_url.startsWith('http')}
									<!-- Local PDF -->
									<iframe
										src={selected.embed_url}
										title={selected.title}
										class="embed-frame"
									></iframe>
								{:else}
									<!-- Web page or remote PDF — may be blocked by X-Frame-Options -->
									<iframe
										src={selected.embed_url}
										title={selected.title}
										class="embed-frame"
										sandbox="allow-same-origin allow-scripts allow-popups"
									></iframe>
								{/if}
							{:else}
								<div class="embed-fallback">
									<p>No embeddable source available.</p>
									{#if selected.url}
										<a href={selected.url} target="_blank" class="btn btn-primary">
											Open source in new tab
										</a>
									{/if}
								</div>
							{/if}
						</div>
					{:else}
						<div class="panel-content">
							<div class="source-meta">
								<h2 class="source-title">{selected.title}</h2>
								<div class="text-sm text-secondary">
									{selected.author}{#if selected.date} &middot; {selected.date}{/if}
								</div>
							</div>
							{#if selected.markdown.sections.length > 0}
								{#each selected.markdown.sections as section}
									<div class="md-section">
										<h4 class="md-heading">{section.heading}</h4>
										<div class="md-content">{@html markdownToHtml(section.content)}</div>
									</div>
								{/each}
							{:else}
								<div class="empty-panel">
									No source notes available for this source.
								</div>
							{/if}
						</div>
					{/if}
				</div>

				<!-- Right: Extracts -->
				<div class="panel panel-right">
					<div class="panel-source-banner">
						<span class="source-id">{selected.id.split(':').pop()}</span>
						<span class="source-name">{selected.title}</span>
					</div>
					<div class="panel-header">
						<h3>Extracts ({selected.extract_count})</h3>
						<div class="panel-header-filters">
							<select class="filter-select" bind:value={formatFilter}>
								<option value="all">All formats</option>
								{#each extractFormats as fmt}
									<option value={fmt}>{fmt}</option>
								{/each}
							</select>
							<select class="filter-select" bind:value={extractTypeFilter}>
								<option value="all">All types</option>
								{#each extractTypes as et}
									<option value={et}>{et}</option>
								{/each}
							</select>
						</div>
					</div>
					<div class="panel-content">
						{#each Object.entries(filteredExtractSections) as [section, extracts]}
							<div class="extract-section">
								<div class="extract-section-header">{section}</div>
								{#each extracts as extract}
									<div class="extract-item">
										<div class="extract-meta">
											<span class="format-badge {formatBadgeClass(extract.format)}">{extract.format}</span>
											<span class="extract-type-badge {extractTypeBadgeClass(extract.extract_type)}">{extract.extract_type}</span>
											<span class="text-xs text-secondary">#{extract.position}</span>
										</div>
										<div class="extract-text">{extract.text}</div>
										{#if extract.claims?.length}
											<div class="extract-claims">
												{#each extract.claims as claim}
													<span class="claim-badge" title={claim.summary}>
														{claim.theme}
													</span>
												{/each}
											</div>
										{/if}
									</div>
								{/each}
							</div>
						{/each}
					</div>
				</div>
			</div>
		{/if}
	</div>
{/if}

<script lang="ts" module>
	function markdownToHtml(md: string): string {
		return md
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
			.replace(/\*(.+?)\*/g, '<em>$1</em>')
			.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
			.replace(/^- (.+)$/gm, '<li>$1</li>')
			.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
			.replace(/\n\n/g, '</p><p>')
			.replace(/\n/g, '<br>')
			.replace(/^/, '<p>')
			.replace(/$/, '</p>');
	}
</script>

<style>
	.audit-layout {
		display: flex;
		gap: 0;
		height: calc(100vh - var(--header-height) - 140px);
		min-height: 500px;
	}

	.source-list {
		width: 280px;
		flex-shrink: 0;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.list-header {
		padding: var(--space-3) var(--space-4);
		border-bottom: 1px solid var(--color-border);
		background: var(--color-surface);
	}

	.list-title {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		margin-bottom: var(--space-2);
	}

	.list-filters {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.filter-select,
	.filter-search {
		width: 100%;
		font-family: var(--font-family);
		font-size: var(--font-size-xs);
		padding: var(--space-1) var(--space-2);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-bg);
		outline: none;
	}

	.list-items {
		flex: 1;
		overflow-y: auto;
	}

	.source-item {
		display: block;
		width: 100%;
		text-align: left;
		padding: var(--space-3) var(--space-4);
		border: none;
		border-bottom: 1px solid var(--color-border-light);
		background: var(--color-bg);
		cursor: pointer;
		font-family: var(--font-family);
		transition: background 0.1s;
	}

	.source-item:hover {
		background: var(--color-surface);
	}

	.source-item.active {
		background: var(--color-primary-light);
		border-left: 3px solid var(--color-primary);
	}

	.source-item-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-1);
	}

	.source-item-title {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		line-height: var(--line-height-tight);
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.source-item-author {
		margin-top: var(--space-1);
	}

	.split-view {
		flex: 1;
		display: flex;
		gap: var(--space-4);
		margin-left: var(--space-4);
		min-width: 0;
	}

	.panel {
		flex: 1;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		display: flex;
		flex-direction: column;
		overflow: hidden;
		min-width: 0;
	}

	.panel-header {
		padding: var(--space-2) var(--space-4);
		border-bottom: 1px solid var(--color-border);
		background: var(--color-surface);
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-shrink: 0;
	}

	.panel-header h3 {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		margin: 0;
	}

	.panel-header-filters {
		display: flex;
		gap: var(--space-2);
	}

	.panel-tabs {
		display: flex;
		gap: 0;
	}

	.panel-tab {
		font-family: var(--font-family);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		padding: var(--space-2) var(--space-4);
		border: none;
		background: none;
		color: var(--color-text-secondary);
		cursor: pointer;
		border-bottom: 2px solid transparent;
		transition: color 0.15s, border-color 0.15s;
	}

	.panel-tab:hover {
		color: var(--color-text);
	}

	.panel-tab.active {
		color: var(--color-primary);
		border-bottom-color: var(--color-primary);
	}

	.panel-meta {
		display: flex;
		gap: var(--space-2);
		align-items: center;
	}

	.panel-embed {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.embed-frame {
		width: 100%;
		flex: 1;
		border: none;
		min-height: 0;
	}

	.embed-fallback {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-4);
		flex: 1;
		color: var(--color-text-secondary);
		font-size: var(--font-size-sm);
	}

	.panel-content {
		flex: 1;
		overflow-y: auto;
		padding: var(--space-4);
	}

	.source-meta {
		margin-bottom: var(--space-4);
		padding-bottom: var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
	}

	.source-title {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		line-height: var(--line-height-tight);
		margin-bottom: var(--space-2);
	}

	.md-section {
		margin-bottom: var(--space-4);
	}

	.md-heading {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		color: var(--color-primary);
		margin-bottom: var(--space-2);
	}

	.md-content {
		font-size: var(--font-size-sm);
		line-height: var(--line-height-relaxed);
		color: var(--color-text);
	}

	.md-content :global(blockquote) {
		border-left: 3px solid var(--color-border);
		padding-left: var(--space-3);
		color: var(--color-text-secondary);
		margin: var(--space-2) 0;
	}

	.md-content :global(li) {
		margin-left: var(--space-4);
		margin-bottom: var(--space-1);
	}

	.md-content :global(strong) {
		font-weight: var(--font-weight-semibold);
	}

	.empty-panel {
		color: var(--color-text-tertiary);
		font-size: var(--font-size-sm);
		padding: var(--space-8);
		text-align: center;
	}

	.panel-source-banner {
		padding: var(--space-2) var(--space-4);
		background: var(--color-primary-light);
		border-bottom: 1px solid var(--color-border);
		display: flex;
		align-items: center;
		gap: var(--space-2);
		flex-shrink: 0;
	}

	.source-id {
		font-family: var(--font-mono);
		font-size: var(--font-size-xs);
		color: var(--color-primary);
		font-weight: var(--font-weight-semibold);
		flex-shrink: 0;
	}

	.source-name {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	/* Right panel extracts */
	.extract-section {
		margin-bottom: var(--space-4);
	}

	.extract-section-header {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-primary);
		padding: var(--space-1) var(--space-2);
		background: var(--color-primary-light);
		border-radius: var(--radius-sm);
		margin-bottom: var(--space-2);
		position: sticky;
		top: 0;
		z-index: 1;
	}

	.extract-item {
		padding: var(--space-2) var(--space-3);
		border-left: 2px solid var(--color-border-light);
		margin-bottom: var(--space-2);
		transition: border-color 0.1s;
	}

	.extract-item:hover {
		border-left-color: var(--color-primary);
		background: var(--color-surface);
	}

	.extract-meta {
		display: flex;
		gap: var(--space-2);
		align-items: center;
		margin-bottom: var(--space-1);
	}

	.extract-text {
		font-size: var(--font-size-sm);
		line-height: var(--line-height-normal);
	}

	.format-badge {
		font-size: 10px;
		padding: 1px 6px;
		border-radius: var(--radius-full);
		font-weight: var(--font-weight-medium);
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.format-prose { background: #e8f0fe; color: #1a73e8; }
	.format-bullet { background: #e6f4ea; color: #188038; }
	.format-heading { background: #fef7e0; color: #e37400; }
	.format-table { background: #fce8e6; color: #c5221f; }
	.format-quote { background: #f3e8ff; color: #7c3aed; }
	.format-other { background: var(--color-surface); color: var(--color-text-secondary); }

	.extract-type-badge {
		font-size: 10px;
		padding: 1px 6px;
		border-radius: var(--radius-full);
		font-weight: var(--font-weight-medium);
	}

	.etype-claim { background: #dbeafe; color: #1d4ed8; }
	.etype-statistic { background: #fce7f3; color: #be185d; }
	.etype-evidence { background: #d1fae5; color: #065f46; }
	.etype-recommendation { background: #fef3c7; color: #92400e; }
	.etype-definition { background: #e0e7ff; color: #3730a3; }
	.etype-context { background: #f1f5f9; color: #475569; }
	.etype-noise { background: #f1f5f9; color: #94a3b8; }
	.etype-other { background: var(--color-surface); color: var(--color-text-secondary); }

	.extract-claims {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-1);
		margin-top: var(--space-2);
	}

	.claim-badge {
		font-size: 10px;
		padding: 2px 8px;
		border-radius: var(--radius-full);
		background: #f3e8ff;
		color: #7c3aed;
		font-weight: var(--font-weight-medium);
		cursor: default;
		max-width: 200px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
</style>
