<script lang="ts">
	import { app } from '$lib/data.svelte';
	import type { AuditSource, AuditExtract } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let selectedIdx = $state(0);
	let activeView = $state<'source' | 'extracts'>('source');
	let extractTypeFilter = $state('all');
	let linkedFilter = $state<'all' | 'linked' | 'unlinked'>('all');
	let searchTerm = $state('');
	let iframeError = $state(false);

	let allSources = $derived.by(() => app.audit?.sources ?? []);
	let sources = $derived.by(() => {
		if (!app.searchQuery) return allSources;
		const q = app.searchQuery.toLowerCase();
		return allSources.filter((s: AuditSource) => s.title.toLowerCase().includes(q) || (s.author && s.author.toLowerCase().includes(q)));
	});
	let selected = $derived.by(() => sources[selectedIdx] ?? null);

	let extractTypes = $derived.by(() => {
		if (!selected) return [];
		return [...new Set(selected.extracts.map((e: AuditExtract) => e.extract_type))].sort();
	});

	let linkedCount = $derived.by(() => {
		if (!selected) return 0;
		return selected.extracts.filter((e: AuditExtract) => e.claims?.length).length;
	});

	let filteredExtracts = $derived.by(() => {
		if (!selected) return [];
		let list = selected.extracts;
		if (extractTypeFilter !== 'all') list = list.filter((e: AuditExtract) => e.extract_type === extractTypeFilter);
		if (linkedFilter === 'linked') list = list.filter((e: AuditExtract) => e.claims?.length);
		if (linkedFilter === 'unlinked') list = list.filter((e: AuditExtract) => !e.claims?.length);
		if (searchTerm) {
			const q = searchTerm.toLowerCase();
			list = list.filter((e: AuditExtract) => e.text.toLowerCase().includes(q));
		}
		return list;
	});

	function selectSource(i: number) {
		selectedIdx = i;
		extractTypeFilter = 'all';
		linkedFilter = 'all';
		searchTerm = '';
		iframeError = false;
	}

	function extractColor(type: string): string {
		switch (type) {
			case 'assertion': return 'var(--color-claim)';
			case 'statistic': return 'var(--color-source)';
			case 'recommendation': return 'var(--color-finding)';
			case 'example': return 'var(--color-success)';
			case 'definition': return 'var(--color-extract)';
			case 'context': return 'var(--color-text-tertiary)';
			case 'attribution': return 'var(--color-info)';
			default: return 'var(--color-border)';
		}
	}
</script>

{#if sources.length > 0 && selected}
	<div class="detail-header">
		<h2 class="detail-title">{selected.title}</h2>
		<p class="detail-meta">
			{selected.author}
			{#if selected.date} &middot; {selected.date}{/if}
			&middot; {selected.type}
			&middot; {selected.extract_count} extracts
		</p>
		{#if selected.url}
			<a href={selected.url} target="_blank" rel="noopener" class="detail-url">
				<Icon name="external" size={11} />
				{selected.url}
			</a>
		{/if}
	</div>

	<div class="tab-bar">
		<button class="tab" class:active={activeView === 'source'} onclick={() => { activeView = 'source'; }}>
			<Icon name="source" size={15} />
			Source
		</button>
		<button class="tab" class:active={activeView === 'extracts'} onclick={() => { activeView = 'extracts'; }}>
			<Icon name="extract" size={15} />
			Extracts ({selected.extract_count})
		</button>
	</div>

	<div class="layout">
		<div class="detail">
			{#if activeView === 'source'}
				{#if selected.type === 'youtube' && selected.embed_url}
					<div class="embed-container video">
						<iframe
							src={selected.embed_url}
							title={selected.title}
							allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
							allowfullscreen
						></iframe>
					</div>
				{:else if (selected.type === 'web') && selected.embed_url && !iframeError}
					<div class="embed-container web">
						<div class="embed-bar">
							<Icon name="external" size={13} />
							<a href={selected.url || selected.embed_url} target="_blank" rel="noopener">{selected.url || selected.embed_url}</a>
						</div>
						<iframe
							src={selected.embed_url}
							title={selected.title}
							sandbox="allow-scripts allow-same-origin"
							onerror={() => { iframeError = true; }}
							onload={(e) => {
								try {
									const frame = e.currentTarget as HTMLIFrameElement;
									void frame.contentDocument;
								} catch {
									iframeError = true;
								}
							}}
						></iframe>
					</div>
				{:else}
					{#if selected.url}
						<div class="open-source-bar">
							<a href={selected.url} target="_blank" rel="noopener" class="open-source-link">
								<Icon name="external" size={14} />
								Open source in new tab
							</a>
						</div>
					{/if}
					<div class="source-content">
						{#if selected.markdown?.sections?.length}
							{#each selected.markdown.sections as section}
								<div class="md-section">
									<h3 class="md-heading">{section.heading}</h3>
									<div class="md-body">
										{#each section.content.split('\n') as line}
											{#if line.trim()}
												<p>{line}</p>
											{/if}
										{/each}
									</div>
								</div>
							{/each}
						{:else if selected.markdown?.raw_markdown}
							<div class="md-body">
								{#each selected.markdown.raw_markdown.split('\n') as line}
									{#if line.trim()}
										<p>{line}</p>
									{/if}
								{/each}
							</div>
						{:else}
							<div class="empty-state"><p>No source content available.</p></div>
						{/if}
					</div>
				{/if}
			{:else}
				<div class="toolbar">
					<Icon name="filter" size={15} />
					<select bind:value={extractTypeFilter}>
						<option value="all">All types ({selected.extracts.length})</option>
						{#each extractTypes as t}
							<option value={t}>{t}</option>
						{/each}
					</select>
					<select bind:value={linkedFilter}>
						<option value="all">All extracts</option>
						<option value="linked">Linked to claims ({linkedCount})</option>
						<option value="unlinked">Unlinked</option>
					</select>
					<div class="search-field">
						<Icon name="search" size={14} />
						<input type="text" placeholder="Search extracts..." bind:value={searchTerm} />
						{#if searchTerm}
							<button class="search-clear" onclick={() => { searchTerm = ''; }}>
								<Icon name="x" size={14} />
							</button>
						{/if}
					</div>
					<span class="toolbar-count">{filteredExtracts.length} results</span>
				</div>

				<div class="extracts">
					{#each filteredExtracts as ext}
						<div class="extract-card" class:linked={ext.claims?.length} style="border-left-color: {extractColor(ext.extract_type)}">
							<div class="extract-header">
								<span class="badge badge-extract">{ext.extract_type}</span>
								{#if ext.claims?.length}
									<span class="linked-badge">
										<Icon name="claim" size={12} />
										{ext.claims.length} claim{ext.claims.length > 1 ? 's' : ''}
									</span>
								{/if}
								{#if ext.section}
									<span class="extract-section">{ext.section}</span>
								{/if}
							</div>
							<p class="extract-text">{ext.text}</p>
							{#if ext.claims?.length}
								<div class="extract-claims">
									{#each ext.claims as c}
										<span class="claim-chip" title={c.summary}>
											<span class="claim-chip-dot"></span>
											{c.claim_id}
											{#if c.finding}
												<span class="finding-label">{c.finding.finding_title}</span>
											{/if}
										</span>
									{/each}
								</div>
							{/if}
						</div>
					{/each}
					{#if filteredExtracts.length === 0}
						<div class="empty-state"><p>No extracts match your filters.</p></div>
					{/if}
				</div>
			{/if}
		</div>

		<aside class="source-list">
			<div class="list-header">
				<Icon name="source" size={14} />
				Sources ({sources.length})
			</div>
			{#each sources as src, i}
				<button class="source-item" class:active={selectedIdx === i} onclick={() => selectSource(i)}>
					<span class="source-num">{i + 1}</span>
					<span class="source-name" title={src.title}>{src.title}</span>
					{#if src.extracts.some((e: AuditExtract) => e.claims?.length)}
						<span class="source-linked" title="Has linked claims">
							<Icon name="claim" size={11} />
						</span>
					{/if}
					<span class="source-extract-count">{src.extract_count}</span>
				</button>
			{/each}
		</aside>
	</div>
{:else if sources.length === 0}
	<div class="empty-state"><p>No audit data available.</p></div>
{/if}

<style>
	/* Use full width */
	:global(.content:has(.layout)) {
		max-width: none;
	}

	/* Layout */
	.layout {
		display: grid;
		grid-template-columns: 1fr 280px;
		grid-template-rows: 1fr;
		gap: var(--space-4);
		height: calc(100vh - var(--header-height) - var(--space-12));
	}

	/* Source list */
	.source-list {
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		overflow-y: auto;
		min-height: 0;
	}
	.list-header {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding: var(--space-3) var(--space-4);
		color: var(--color-text-tertiary);
		border-bottom: 1px solid var(--color-border-light);
		position: sticky;
		top: 0;
		background: var(--color-surface);
		z-index: 1;
	}
	.source-item {
		display: flex;
		gap: var(--space-2);
		align-items: center;
		width: 100%;
		padding: var(--space-2) var(--space-4);
		background: none;
		border: none;
		border-bottom: 1px solid var(--color-border-light);
		cursor: pointer;
		font-family: var(--font-family);
		font-size: var(--font-size-xs);
		text-align: left;
		transition: background 0.1s;
	}
	.source-item:last-child { border-bottom: none; }
	.source-item:hover { background: var(--color-surface-hover); }
	.source-item.active { background: var(--color-finding-bg); }
	.source-num {
		color: var(--color-text-tertiary);
		width: 20px;
		flex-shrink: 0;
		text-align: right;
	}
	.source-name {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--color-text);
	}
	.source-linked {
		flex-shrink: 0;
		color: var(--color-claim);
		display: flex;
		align-items: center;
	}
	.source-extract-count {
		flex-shrink: 0;
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		min-width: 20px;
		text-align: right;
	}

	/* Detail area */
	.detail {
		min-width: 0;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}
	.detail-header {
		margin-bottom: var(--space-4);
	}
	.detail-url {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		margin-top: var(--space-1);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		max-width: 100%;
	}
	.detail-url:hover { color: var(--color-primary-text); text-decoration: none; }
	.detail-title {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-semibold);
		line-height: var(--line-height-tight);
	}
	.detail-meta {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		margin-top: var(--space-2);
		display: flex;
		align-items: center;
		gap: 0;
		flex-wrap: wrap;
	}
	.detail-meta a {
		display: inline-flex;
		align-items: center;
		gap: 3px;
	}

	/* Tab bar */
	.tab-bar {
		display: flex;
		gap: 2px;
		margin-bottom: var(--space-5);
		border-bottom: 1px solid var(--color-border-light);
	}
	.tab {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-3) var(--space-4);
		background: none;
		border: none;
		border-bottom: 2px solid transparent;
		cursor: pointer;
		font-family: var(--font-family);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
		transition: color 0.15s, border-color 0.15s;
		margin-bottom: -1px;
	}
	.tab:hover { color: var(--color-text); }
	.tab.active {
		color: var(--color-text);
		border-bottom-color: var(--color-finding);
	}

	/* Embeds */
	.embed-container {
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		overflow: hidden;
	}
	.embed-container iframe {
		width: 100%;
		border: none;
		display: block;
	}
	.embed-container.video {
		position: relative;
		padding-bottom: 56.25%; /* 16:9 */
		height: 0;
	}
	.embed-container.video iframe {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
	}
	.embed-container.web iframe {
		height: calc(100vh - var(--header-height) - 14rem);
	}
	.embed-container.web {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}
	.embed-bar {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-2) var(--space-4);
		background: var(--color-bg);
		border-bottom: 1px solid var(--color-border-light);
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
	}
	.embed-bar a {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	/* Open source link */
	.open-source-bar {
		margin-bottom: var(--space-3);
	}
	.open-source-link {
		display: inline-flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-2) var(--space-4);
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		transition: border-color 0.15s, box-shadow 0.15s;
	}
	.open-source-link:hover {
		border-color: var(--color-primary);
		text-decoration: none;
		box-shadow: var(--shadow-sm);
	}

	/* Source content */
	.source-content {
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		padding: var(--space-6);
		overflow-y: auto;
		flex: 1;
		min-height: 0;
	}
	.md-section {
		margin-bottom: var(--space-6);
	}
	.md-section:last-child { margin-bottom: 0; }
	.md-heading {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		margin-bottom: var(--space-3);
		padding-bottom: var(--space-2);
		border-bottom: 1px solid var(--color-border-light);
		color: var(--color-text);
	}
	.md-body {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		line-height: var(--line-height-normal);
	}
	.md-body p {
		margin-bottom: var(--space-2);
	}

	/* Toolbar count */
	.toolbar-count {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		margin-left: auto;
	}

	/* Extracts */
	.extracts {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
		overflow-y: auto;
		flex: 1;
		min-height: 0;
	}
	.extract-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-left: 3px solid var(--color-border);
		border-radius: var(--radius-md);
		padding: var(--space-4);
		box-shadow: var(--shadow-sm);
		transition: box-shadow 0.15s;
	}
	.extract-card:hover { box-shadow: var(--shadow-md); }
	.extract-card.linked {
		background: var(--color-surface);
	}
	.extract-header {
		display: flex;
		gap: var(--space-2);
		align-items: center;
		margin-bottom: var(--space-2);
	}
	.linked-badge {
		display: inline-flex;
		align-items: center;
		gap: 3px;
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		color: var(--color-claim);
		background: var(--color-claim-bg);
		padding: 1px 6px;
		border-radius: var(--radius-sm);
	}
	.extract-section {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.extract-text {
		font-size: var(--font-size-sm);
		line-height: var(--line-height-normal);
		color: var(--color-text);
	}
	.extract-claims {
		margin-top: var(--space-3);
		padding-top: var(--space-3);
		border-top: 1px solid var(--color-border-light);
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2);
	}
	.claim-chip {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
		font-size: var(--font-size-xs);
		background: var(--color-claim-bg);
		color: var(--color-claim);
		padding: 2px 8px;
		border-radius: var(--radius-sm);
		font-weight: var(--font-weight-medium);
	}
	.claim-chip-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--color-claim);
	}
	.finding-label {
		color: var(--color-finding);
		margin-left: var(--space-1);
		font-weight: var(--font-weight-normal);
	}
</style>
