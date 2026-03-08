<script lang="ts">
	import { app, shortId } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';

	const statusColorTokens: Record<string, string> = {
		analyzed: '--color-success',
		extracted: '--color-warning',
		collected: '--color-info',
		discovered: '--color-text-tertiary',
		failed: '--color-error'
	};

	function getColor(token: string): string {
		if (typeof document === 'undefined') return '#888';
		return getComputedStyle(document.documentElement).getPropertyValue(token).trim() || '#888';
	}

	const statusLabels: Record<string, string> = {
		analyzed: 'Analyzed',
		extracted: 'Extracted',
		collected: 'Collected',
		discovered: 'Discovered',
		failed: 'Failed'
	};

	const typeIcons: Record<string, string> = {
		web: 'globe',
		youtube: 'youtube',
		pdf: 'file-text'
	};

	const typeColorTokens: Record<string, string> = {
		web: '--color-info',
		youtube: '--color-error',
		pdf: '--color-warning'
	};

	/** Relevance score: weights findings > claims > extracts */
	function relevanceScore(s: { extract_count: number; claim_count: number; finding_count: number }): number {
		return (s.extract_count ?? 0) + (s.claim_count ?? 0) * 5 + (s.finding_count ?? 0) * 10;
	}

	let statusCounts = $derived.by(() => {
		if (!app.sources) return new Map<string, number>();
		const counts = new Map<string, number>();
		for (const s of app.sources.sources) {
			const st = s.status ?? 'discovered';
			counts.set(st, (counts.get(st) || 0) + 1);
		}
		return counts;
	});

	let typeCounts = $derived.by(() => {
		if (!app.sources) return new Map<string, number>();
		const counts = new Map<string, number>();
		for (const s of app.sources.sources) {
			counts.set(s.type, (counts.get(s.type) || 0) + 1);
		}
		return counts;
	});

	let totalSources = $derived(app.sources?.sources.length ?? 0);

	/** SVG donut segments: ordered by pipeline stage */
	let donutSegments = $derived.by(() => {
		const order = ['analyzed', 'extracted', 'collected', 'discovered', 'failed'];
		const total = totalSources || 1;
		const circumference = 2 * Math.PI * 40; // r=40
		let offset = 0;
		const segments: Array<{ status: string; count: number; pct: number; dashArray: string; dashOffset: number; color: string }> = [];

		for (const status of order) {
			const count = statusCounts.get(status) ?? 0;
			if (count === 0) continue;
			const pct = count / total;
			const length = pct * circumference;
			segments.push({
				status,
				count,
				pct,
				dashArray: `${length} ${circumference - length}`,
				dashOffset: -offset,
				color: getColor(statusColorTokens[status] ?? '--color-text-tertiary')
			});
			offset += length;
		}
		return segments;
	});

	/** SVG donut segments for source types */
	let typeDonutSegments = $derived.by(() => {
		const total = totalSources || 1;
		const circumference = 2 * Math.PI * 40;
		let offset = 0;
		const entries = [...typeCounts.entries()].sort((a, b) => b[1] - a[1]);
		const segments: Array<{ type: string; count: number; pct: number; dashArray: string; dashOffset: number; color: string }> = [];

		for (const [type, count] of entries) {
			const pct = count / total;
			const length = pct * circumference;
			segments.push({
				type,
				count,
				pct,
				dashArray: `${length} ${circumference - length}`,
				dashOffset: -offset,
				color: getColor(typeColorTokens[type] ?? '--color-text-tertiary')
			});
			offset += length;
		}
		return segments;
	});

	let topSources = $derived.by(() => {
		if (!app.sources) return [];
		return [...app.sources.sources]
			.filter(s => s.status !== 'discovered' && s.status !== 'failed')
			.map(s => ({ ...s, score: relevanceScore(s) }))
			.sort((a, b) => b.score - a.score)
			.slice(0, 10);
	});

	let maxScore = $derived(topSources.length > 0 ? topSources[0].score : 1);

	let processedCount = $derived.by(() => {
		if (!app.sources) return 0;
		return app.sources.sources.filter(s => s.status === 'analyzed' || s.status === 'extracted').length;
	});

	let totalExtracts = $derived.by(() => {
		if (!app.sources) return 0;
		return app.sources.sources.reduce((sum, s) => sum + (s.extract_count ?? 0), 0);
	});

	let uniqueAuthors = $derived.by(() => {
		if (!app.sources) return 0;
		const authors = new Set(app.sources.sources.map(s => s.author).filter(a => a && a.trim()));
		return authors.size;
	});
</script>

{#if app.sources}
	{@const s = app.stats}

	<!-- Stat cards -->
	<div class="stats-grid">
		<div class="stat-card">
			<div class="stat-icon sources"><Icon name="source" size={22} /></div>
			<div class="stat-value">{totalSources}</div>
			<div class="stat-label">Sources</div>
		</div>
		<div class="stat-card">
			<div class="stat-icon extracts"><Icon name="extract" size={22} /></div>
			<div class="stat-value">{totalExtracts.toLocaleString()}</div>
			<div class="stat-label">Extracts</div>
		</div>
		<div class="stat-card">
			<div class="stat-icon claims"><Icon name="claim" size={22} /></div>
			<div class="stat-value">{s?.canonical_claims ?? 0}</div>
			<div class="stat-label">Claims</div>
		</div>
		<div class="stat-card">
			<div class="stat-icon findings"><Icon name="findings" size={22} /></div>
			<div class="stat-value">{s?.findings ?? 0}</div>
			<div class="stat-label">Findings</div>
		</div>
	</div>

	<!-- Charts row -->
	<div class="charts-row">
		<!-- Status donut -->
		<div class="chart-card">
			<h3 class="chart-title">Sources by Status</h3>
			<div class="donut-wrap">
				<svg viewBox="4 4 92 92" class="donut">
					{#each donutSegments as seg}
						<circle
							cx="50" cy="50" r="40"
							fill="none"
							stroke={seg.color}
							stroke-width="12"
							stroke-dasharray={seg.dashArray}
							stroke-dashoffset={seg.dashOffset}
							transform="rotate(-90 50 50)"
						/>
					{/each}
					<text x="50" y="47" text-anchor="middle" class="donut-number">{totalSources}</text>
					<text x="50" y="58" text-anchor="middle" class="donut-label">sources</text>
				</svg>
				<div class="donut-legend">
					{#each donutSegments as seg}
						<div class="legend-row">
							<span class="legend-dot" style="background: {seg.color}"></span>
							<span class="legend-name">{statusLabels[seg.status] ?? seg.status}</span>
							<span class="legend-count">{seg.count}</span>
							<span class="legend-pct">{Math.round(seg.pct * 100)}%</span>
						</div>
					{/each}
				</div>
			</div>

			<div class="pipeline-divider"></div>
			<h3 class="chart-title">Pipeline Progress</h3>
			<div class="pipeline-stat">
				<div class="pipeline-label">
					<span>{processedCount} of {totalSources} sources processed</span>
					<span class="pipeline-pct">{Math.round((processedCount / totalSources) * 100)}%</span>
				</div>
				<div class="pipeline-bar-wrap">
					<div class="pipeline-bar" style="width: {(processedCount / totalSources) * 100}%"></div>
				</div>
			</div>
		</div>

		<!-- Source types -->
		<div class="chart-card">
			<h3 class="chart-title">Source Types</h3>
			<div class="donut-wrap">
				<svg viewBox="4 4 92 92" class="donut">
					{#each typeDonutSegments as seg}
						<circle
							cx="50" cy="50" r="40"
							fill="none"
							stroke={seg.color}
							stroke-width="12"
							stroke-dasharray={seg.dashArray}
							stroke-dashoffset={seg.dashOffset}
							transform="rotate(-90 50 50)"
						/>
					{/each}
					<text x="50" y="47" text-anchor="middle" class="donut-number">{typeCounts.size}</text>
					<text x="50" y="58" text-anchor="middle" class="donut-label">types</text>
				</svg>
				<div class="donut-legend">
					{#each typeDonutSegments as seg}
						<div class="legend-row">
							<span class="legend-dot" style="background: {seg.color}"></span>
							<Icon name={typeIcons[seg.type] ?? 'sources'} size={13} />
							<span class="legend-name">{seg.type}</span>
							<span class="legend-count">{seg.count}</span>
							<span class="legend-pct">{Math.round(seg.pct * 100)}%</span>
						</div>
					{/each}
				</div>
			</div>

			<div class="authors-stat">
				<span class="authors-count">{uniqueAuthors}</span>
				<span class="authors-label">unique authors</span>
			</div>
		</div>
	</div>

	<!-- Top sources by relevance -->
	<div class="section">
		<h2 class="section-title">Top Sources by Relevance</h2>
		<p class="section-desc">Scored by contribution: extracts &times;1 + claims &times;5 + findings &times;10</p>
		<div class="relevance-list">
			{#each topSources as source, i}
				<div class="relevance-item">
					<span class="relevance-rank">{i + 1}</span>
					<div class="relevance-info">
						<div class="relevance-title" title={source.title}>
							<button class="link-btn" onclick={() => { app.deepDiveSourceId = source.id; app.activeTab = 'deep-dive'; }}>
								{source.title}
								<Icon name="deep-dive" size={11} />
							</button>
						</div>
						<div class="relevance-meta">
							<Icon name={typeIcons[source.type] ?? 'sources'} size={12} />
							<span>{source.author || 'Unknown'}</span>
							<span class="relevance-counts">
								<span class="relevance-count-item" title="Findings"><Icon name="findings" size={11} /> {source.finding_count}</span>
								<span class="relevance-count-item" title="Claims"><Icon name="claim" size={11} /> {source.claim_count}</span>
								<span class="relevance-count-item" title="Extracts"><Icon name="extract" size={11} /> {source.extract_count}</span>
							</span>
						</div>
					</div>
					<span class="relevance-score">{source.score}</span>
				</div>
			{/each}
		</div>
	</div>

	<!-- Key Findings -->
	{#if s?.key_findings?.length}
		<div class="section">
			<h2 class="section-title">Key Findings</h2>
			<div class="findings-list">
				{#each s.key_findings as f, i}
					<div class="finding-item">
						<span class="finding-num">{i + 1}</span>
						<span>{f}</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}
{:else}
	<div class="empty-state"><p>Loading...</p></div>
{/if}

<style>
	/* Stat cards */
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
		gap: var(--space-4);
		margin-bottom: var(--space-6);
	}
	.stat-card {
		background: var(--color-surface);
		border-radius: var(--radius-md);
		padding: var(--space-5) var(--space-6);
		box-shadow: var(--shadow-sm);
		border: 1px solid var(--color-border-light);
		text-align: center;
	}
	.stat-icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		border-radius: var(--radius-sm);
		margin-bottom: var(--space-3);
	}
	.stat-icon.sources { background: var(--color-source-bg); color: var(--color-source); }
	.stat-icon.extracts { background: var(--color-extract-bg); color: var(--color-extract); }
	.stat-icon.claims { background: var(--color-claim-bg); color: var(--color-claim); }
	.stat-icon.findings { background: var(--color-finding-bg); color: var(--color-finding); }
	.stat-value { font-size: var(--font-size-3xl); font-weight: var(--font-weight-semibold); line-height: 1; }
	.stat-label { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: var(--space-2); }

	/* Charts row */
	.charts-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--space-4);
		margin-bottom: var(--space-6);
	}
	.chart-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		padding: var(--space-5) var(--space-6);
		box-shadow: var(--shadow-sm);
	}
	.chart-title {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		margin-bottom: var(--space-4);
	}

	/* Donut chart */
	.donut-wrap {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		min-height: 130px;
	}
	.donut {
		width: 120px;
		height: 120px;
		flex-shrink: 0;
	}
	.donut-number {
		font-size: 16px;
		font-weight: 600;
		fill: var(--color-text);
	}
	.donut-label {
		font-size: 8px;
		fill: var(--color-text-tertiary);
	}
	.donut-legend {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
		flex: 1;
	}
	.legend-row {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-size: var(--font-size-sm);
	}
	.legend-dot {
		width: 10px;
		height: 10px;
		border-radius: 2px;
		flex-shrink: 0;
	}
	.legend-name {
		color: var(--color-text-secondary);
	}
	.legend-count {
		font-weight: var(--font-weight-medium);
		min-width: 24px;
		text-align: right;
	}
	.legend-pct {
		color: var(--color-text-tertiary);
		font-size: var(--font-size-xs);
		min-width: 32px;
		text-align: right;
	}

	/* Type donut legend icons */
	.legend-row :global(.icon) {
		flex-shrink: 0;
		color: var(--color-text-tertiary);
	}



	/* Authors stat */
	.authors-stat {
		margin-top: var(--space-5);
		padding-top: var(--space-5);
		border-top: 1px solid var(--color-border-light);
		display: flex;
		align-items: baseline;
		gap: var(--space-2);
	}
	.authors-count {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-semibold);
	}
	.authors-label {
		font-size: var(--font-size-sm);
		color: var(--color-text-tertiary);
	}

	/* Pipeline divider */
	.pipeline-divider {
		border-top: 1px solid var(--color-border-light);
		margin: var(--space-5) 0;
	}

	/* Pipeline progress */
	.pipeline-stat {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}
	.pipeline-label {
		display: flex;
		justify-content: space-between;
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
	}
	.pipeline-pct {
		font-weight: var(--font-weight-medium);
		color: var(--color-text);
	}
	.pipeline-bar-wrap {
		height: 8px;
		background: var(--color-border-light);
		border-radius: 4px;
		overflow: hidden;
	}
	.pipeline-bar {
		height: 100%;
		background: var(--color-success);
		border-radius: 4px;
		transition: width 0.3s ease;
	}

	/* Relevance list */
	.section { margin-top: var(--space-4); }
	.section-title { font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); margin-bottom: var(--space-1); }
	.section-desc { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-bottom: var(--space-4); }
	.relevance-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}
	.relevance-item {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		padding: var(--space-3) var(--space-4);
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-sm);
	}
	.relevance-rank {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-tertiary);
		width: 20px;
		text-align: center;
		flex-shrink: 0;
	}
	.relevance-info {
		flex: 1;
		min-width: 0;
	}
	.relevance-title {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.relevance-title .link-btn {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		background: none;
		border: none;
		padding: 0;
		font: inherit;
		font-weight: var(--font-weight-medium);
		color: var(--color-text);
		cursor: pointer;
		text-align: left;
		max-width: 100%;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.relevance-title .link-btn:hover {
		color: var(--color-primary);
	}
	.relevance-title .link-btn :global(.icon) {
		opacity: 0;
		transition: opacity 0.15s;
		flex-shrink: 0;
	}
	.relevance-item:hover .link-btn :global(.icon) {
		opacity: 0.5;
	}
	.relevance-meta {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		margin-top: 2px;
	}
	.relevance-counts {
		margin-left: auto;
		display: inline-flex;
		align-items: center;
		gap: var(--space-3);
	}
	.relevance-count-item {
		display: inline-flex;
		align-items: center;
		gap: 2px;
		color: var(--color-text-tertiary);
	}
	.relevance-score {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-secondary);
		min-width: 36px;
		text-align: right;
		flex-shrink: 0;
	}

	/* Key findings */
	.findings-list { display: flex; flex-direction: column; gap: var(--space-2); }
	.finding-item {
		display: flex;
		align-items: baseline;
		gap: var(--space-3);
		padding: var(--space-3) var(--space-4);
		background: var(--color-surface);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		border: 1px solid var(--color-border-light);
	}
	.finding-num {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-finding);
		background: var(--color-finding-bg);
		width: 22px;
		height: 22px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: var(--radius-full);
		flex-shrink: 0;
	}

	@media (max-width: 768px) {
		.charts-row { grid-template-columns: 1fr; }
		.donut-wrap { flex-direction: column; align-items: flex-start; }
	}
</style>
