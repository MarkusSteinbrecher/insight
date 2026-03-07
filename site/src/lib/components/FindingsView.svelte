<script lang="ts">
	import { findingsData, searchQuery } from '$lib/stores/data';

	let data = $derived($findingsData);
	let query = $derived($searchQuery);
	let expandedId = $state<string | null>(null);
	let selectedCategory = $state<string>('all');

	let categories = $derived(() => {
		if (!data) return [];
		const counts: Record<string, number> = {};
		for (const f of data.findings) {
			if (f.category) counts[f.category] = (counts[f.category] || 0) + 1;
		}
		return Object.entries(counts)
			.sort((a, b) => b[1] - a[1])
			.map(([cat, count]) => ({ cat, count }));
	});

	let filtered = $derived(() => {
		if (!data) return [];
		let results = data.findings;
		if (selectedCategory !== 'all') {
			results = results.filter((f) => f.category === selectedCategory);
		}
		if (query) {
			const q = query.toLowerCase();
			results = results.filter(
				(f) =>
					f.title.toLowerCase().includes(q) ||
					f.description?.toLowerCase().includes(q) ||
					f.claims.some(
						(c) =>
							c.statement.toLowerCase().includes(q) ||
							c.bottom_line.toLowerCase().includes(q)
					)
			);
		}
		return results;
	});

	function toggle(id: string) {
		expandedId = expandedId === id ? null : id;
	}

	const categoryColors: Record<string, string> = {
		'Architecture & Patterns': '#1a73e8',
		'Strategy & Transformation': '#7c3aed',
		'Governance & Risk': '#c5221f',
		'Data & Integration': '#0891b2',
		'Deployment & Operations': '#d97706',
		'People & Skills': '#188038'
	};

	function catColor(cat: string): string {
		return categoryColors[cat] ?? '#5f6368';
	}
</script>

<div class="findings-view">
	{#if categories().length > 0}
		<div class="category-pills">
			<button
				class="pill"
				class:active={selectedCategory === 'all'}
				onclick={() => (selectedCategory = 'all')}
			>
				All ({data?.total_findings ?? 0})
			</button>
			{#each categories() as { cat, count }}
				<button
					class="pill"
					class:active={selectedCategory === cat}
					style="--pill-color: {catColor(cat)}"
					onclick={() => (selectedCategory = selectedCategory === cat ? 'all' : cat)}
				>
					<span class="pill-dot" style="background: {catColor(cat)}"></span>
					{cat} ({count})
				</button>
			{/each}
		</div>
	{/if}

	{#if filtered().length > 0}
		<div class="findings-list">
			{#each filtered() as finding, i}
				<div class="finding-card" style="--accent: {catColor(finding.category)}">
					<button class="finding-header" onclick={() => toggle(finding.id)}>
						<span class="finding-number">{i + 1}</span>
						<div class="finding-body">
							<h3 class="finding-title">{finding.title}</h3>
							{#if finding.description}
								<p class="finding-desc">{finding.description}</p>
							{/if}
							<div class="finding-tags">
								<span class="category-label" style="color: {catColor(finding.category)}"
									>{finding.category}</span
								>
								<span class="claim-count"
									>{finding.claim_count} claim{finding.claim_count !== 1
										? 's'
										: ''}</span
								>
							</div>
						</div>
						<span class="chevron" class:open={expandedId === finding.id}>
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
								<path
									d="M4 6L8 10L12 6"
									stroke="currentColor"
									stroke-width="1.5"
									stroke-linecap="round"
									stroke-linejoin="round"
								/>
							</svg>
						</span>
					</button>

					{#if expandedId === finding.id}
						<div class="claims-panel">
							{#each finding.claims as claim, ci}
								<div class="claim-row">
									<div class="claim-main">
										<div class="claim-top">
											<span class="claim-num">{ci + 1}</span>
											<p class="claim-statement">{claim.statement}</p>
										</div>
										{#if claim.bottom_line}
											<p class="claim-bottomline">{claim.bottom_line}</p>
										{/if}
									</div>
									<div class="claim-meta">
										<span class="source-count"
											>{claim.source_count} source{claim.source_count !== 1
												? 's'
												: ''}</span
										>
										{#if claim.baseline_category}
											<span
												class="badge badge-{claim.baseline_category === 'new'
													? 'success'
													: claim.baseline_category === 'additional'
														? 'warning'
														: 'primary'}">{claim.baseline_category}</span
											>
										{/if}
									</div>
									{#if claim.sources.length > 0}
										<details class="claim-sources">
											<summary>View sources</summary>
											<ul>
												{#each claim.sources as src}
													<li>
														<div class="src-line">
															{#if src.url}
																<a
																	href={src.url}
																	target="_blank"
																	rel="noopener">{src.title}</a
																>
															{:else}
																<span>{src.title}</span>
															{/if}
															<span class="src-author">{src.author}</span>
														</div>
														{#if src.quotes.length > 0}
															<blockquote>{src.quotes[0]}</blockquote>
														{/if}
													</li>
												{/each}
											</ul>
										</details>
									{/if}
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/each}
		</div>

		<p class="summary">
			{filtered().length} finding{filtered().length !== 1 ? 's' : ''},
			{data?.total_claims_linked ?? 0} linked claims
		</p>
	{:else}
		<div class="empty-state">
			{#if query}
				<p>No findings match "{query}"</p>
			{:else}
				<p>No findings available. Run analysis to generate findings.</p>
			{/if}
		</div>
	{/if}
</div>

<style>
	/* Category filter pills */
	.category-pills {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2);
		margin-bottom: var(--space-6);
	}

	.pill {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 6px 14px;
		font-family: var(--font-family);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
		background: var(--color-bg);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-full);
		cursor: pointer;
		transition:
			background 0.15s,
			border-color 0.15s,
			color 0.15s;
	}

	.pill:hover {
		background: var(--color-surface);
		border-color: var(--color-text-tertiary);
	}

	.pill.active {
		background: var(--color-text);
		border-color: var(--color-text);
		color: var(--color-bg);
	}

	.pill.active .pill-dot {
		background: var(--color-bg) !important;
	}

	.pill-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	/* Findings list */
	.findings-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.finding-card {
		background: var(--color-bg);
		border: 1px solid var(--color-border);
		border-left: 3px solid var(--accent);
		border-radius: var(--radius-md);
		overflow: hidden;
		transition: box-shadow 0.15s;
	}

	.finding-card:hover {
		box-shadow: var(--shadow-sm);
	}

	/* Finding header */
	.finding-header {
		width: 100%;
		display: flex;
		align-items: flex-start;
		gap: var(--space-4);
		padding: var(--space-5) var(--space-5) var(--space-5) var(--space-4);
		background: none;
		border: none;
		cursor: pointer;
		text-align: left;
		font-family: var(--font-family);
	}

	.finding-number {
		flex-shrink: 0;
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		background: var(--color-surface);
		color: var(--color-text-secondary);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		margin-top: 1px;
	}

	.finding-body {
		flex: 1;
		min-width: 0;
	}

	.finding-title {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		line-height: var(--line-height-normal);
		color: var(--color-text);
	}

	.finding-desc {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		line-height: var(--line-height-relaxed);
		margin-top: var(--space-2);
	}

	.finding-tags {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		margin-top: var(--space-3);
	}

	.category-label {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.claim-count {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
	}

	.chevron {
		flex-shrink: 0;
		color: var(--color-text-tertiary);
		transition: transform 0.2s;
		margin-top: 4px;
	}

	.chevron.open {
		transform: rotate(180deg);
	}

	/* Claims panel */
	.claims-panel {
		border-top: 1px solid var(--color-border-light);
		background: var(--color-surface);
	}

	.claim-row {
		padding: var(--space-4) var(--space-5);
	}

	.claim-row + .claim-row {
		border-top: 1px solid var(--color-border-light);
	}

	.claim-main {
		margin-bottom: var(--space-2);
	}

	.claim-top {
		display: flex;
		gap: var(--space-3);
	}

	.claim-num {
		flex-shrink: 0;
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-tertiary);
		width: 20px;
		margin-top: 2px;
	}

	.claim-statement {
		font-size: var(--font-size-sm);
		line-height: var(--line-height-relaxed);
		color: var(--color-text);
	}

	.claim-bottomline {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		margin-top: var(--space-2);
		margin-left: calc(20px + var(--space-3));
		font-style: italic;
		line-height: var(--line-height-relaxed);
	}

	.claim-meta {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		margin-left: calc(20px + var(--space-3));
		margin-bottom: var(--space-2);
	}

	.source-count {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
	}

	/* Sources details */
	.claim-sources {
		margin-left: calc(20px + var(--space-3));
		margin-top: var(--space-2);
	}

	.claim-sources summary {
		cursor: pointer;
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		padding: var(--space-1) 0;
		user-select: none;
	}

	.claim-sources summary:hover {
		color: var(--color-primary);
	}

	.claim-sources ul {
		list-style: none;
		padding: var(--space-3) 0 0;
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.claim-sources li {
		font-size: var(--font-size-sm);
	}

	.src-line {
		display: flex;
		align-items: baseline;
		gap: var(--space-2);
	}

	.src-author {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
	}

	.claim-sources blockquote {
		margin-top: var(--space-1);
		padding-left: var(--space-4);
		border-left: 2px solid var(--color-border);
		font-size: var(--font-size-xs);
		color: var(--color-text-secondary);
		line-height: var(--line-height-relaxed);
	}

	/* Footer */
	.summary {
		font-size: var(--font-size-xs);
		color: var(--color-text-secondary);
		margin-top: var(--space-4);
	}
</style>
