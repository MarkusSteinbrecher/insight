<script lang="ts">
	import { stats, sourcesData, findingsData, insightsData, conclusionsData } from '$lib/stores/data';

	let s = $derived($stats);
	let findings = $derived($findingsData);
	let conclusions = $derived($conclusionsData);
</script>

<div class="dashboard">
	{#if s}
		<div class="stats-grid">
			<div class="card stat">
				<div class="stat-value">{s.sources}</div>
				<div class="stat-label">Sources</div>
			</div>
			<div class="card stat">
				<div class="stat-value">{Object.keys(s.source_types).length}</div>
				<div class="stat-label">Source Types</div>
			</div>
			<div class="card stat">
				<div class="stat-value">{s.canonical_claims}</div>
				<div class="stat-label">Claims</div>
			</div>
			<div class="card stat">
				<div class="stat-value">{findings?.total_findings ?? 0}</div>
				<div class="stat-label">Findings</div>
			</div>
			<div class="card stat">
				<div class="stat-value">{conclusions?.total_recommendations ?? 0}</div>
				<div class="stat-label">Recommendations</div>
			</div>
			<div class="card stat">
				<div class="stat-value">{s.contradictions}</div>
				<div class="stat-label">Contradictions</div>
			</div>
		</div>

		<div class="detail-grid mt-6">
			<div class="card">
				<h3 class="section-title">Source Types</h3>
				<div class="type-list">
					{#each Object.entries(s.source_types) as [type, count]}
						<div class="type-row">
							<span class="type-name">{type}</span>
							<span class="type-bar-wrapper">
								<span class="type-bar" style="width: {(count / s.sources) * 100}%"></span>
							</span>
							<span class="type-count">{count}</span>
						</div>
					{/each}
				</div>
			</div>

			{#if findings && findings.findings.length > 0}
				<div class="card">
					<h3 class="section-title">Top Findings</h3>
					<div class="findings-list">
						{#each findings.findings.slice(0, 5) as f}
							<div class="finding-item">
								<span class="finding-title">{f.title}</span>
								<span class="badge badge-primary">{f.claim_count} claims</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>

		<p class="text-xs text-secondary mt-4">
			Generated {s.generated}
		</p>
	{:else}
		<div class="empty-state">
			<p>No data available for this topic.</p>
		</div>
	{/if}
</div>

<style>
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
		gap: var(--space-4);
	}

	.detail-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
		gap: var(--space-4);
	}

	.section-title {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: var(--space-4);
	}

	.type-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.type-row {
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}

	.type-name {
		font-size: var(--font-size-sm);
		min-width: 60px;
		text-transform: capitalize;
	}

	.type-bar-wrapper {
		flex: 1;
		height: 8px;
		background: var(--color-surface);
		border-radius: var(--radius-full);
		overflow: hidden;
	}

	.type-bar {
		display: block;
		height: 100%;
		background: var(--color-primary);
		border-radius: var(--radius-full);
	}

	.type-count {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		min-width: 24px;
		text-align: right;
	}

	.findings-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.finding-item {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--space-3);
	}

	.finding-title {
		font-size: var(--font-size-sm);
		line-height: var(--line-height-normal);
		flex: 1;
	}
</style>
