<script lang="ts">
	import { app } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';
</script>

{#if app.stats}
	{@const s = app.stats}
	<div class="stats-grid">
		<div class="stat-card">
			<div class="stat-icon sources"><Icon name="source" size={22} /></div>
			<div class="stat-value">{s.sources}</div>
			<div class="stat-label">Sources</div>
		</div>
		<div class="stat-card">
			<div class="stat-icon claims"><Icon name="claim" size={22} /></div>
			<div class="stat-value">{s.canonical_claims ?? 0}</div>
			<div class="stat-label">Canonical Claims</div>
		</div>
		<div class="stat-card">
			<div class="stat-icon findings"><Icon name="findings" size={22} /></div>
			<div class="stat-value">{s.unique_claims ?? 0}</div>
			<div class="stat-label">Unique Claims</div>
		</div>
		<div class="stat-card">
			<div class="stat-icon contradictions"><Icon name="contradiction" size={22} /></div>
			<div class="stat-value">{s.contradictions ?? 0}</div>
			<div class="stat-label">Contradictions</div>
		</div>
	</div>

	{#if s.key_findings?.length}
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
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: var(--space-4);
		margin-bottom: var(--space-8);
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
	.stat-icon.claims { background: var(--color-claim-bg); color: var(--color-claim); }
	.stat-icon.findings { background: var(--color-finding-bg); color: var(--color-finding); }
	.stat-icon.contradictions { background: var(--color-error-bg); color: var(--color-error); }
	.stat-value { font-size: var(--font-size-3xl); font-weight: var(--font-weight-semibold); line-height: 1; }
	.stat-label { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: var(--space-2); }

	.section { margin-top: var(--space-4); }
	.section-title { font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); margin-bottom: var(--space-4); }
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
</style>
