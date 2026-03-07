<script lang="ts">
	import { app } from '$lib/data.svelte';
</script>

{#if app.stats}
	{@const s = app.stats}
	<div class="stats-grid">
		<div class="stat-card">
			<div class="stat-value">{s.sources}</div>
			<div class="stat-label">Sources</div>
		</div>
		<div class="stat-card">
			<div class="stat-value">{s.canonical_claims ?? 0}</div>
			<div class="stat-label">Canonical Claims</div>
		</div>
		<div class="stat-card">
			<div class="stat-value">{s.unique_claims ?? 0}</div>
			<div class="stat-label">Unique Claims</div>
		</div>
		<div class="stat-card">
			<div class="stat-value">{s.contradictions ?? 0}</div>
			<div class="stat-label">Contradictions</div>
		</div>
	</div>

	{#if s.key_findings?.length}
		<h2 class="section-title">Key Findings</h2>
		<ul class="findings-list">
			{#each s.key_findings as f}
				<li>{f}</li>
			{/each}
		</ul>
	{/if}
{:else}
	<div class="empty-state"><p>Loading...</p></div>
{/if}

<style>
	.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: var(--space-4); margin-bottom: var(--space-8); }
	.stat-card { text-align: center; background: var(--color-surface); border-radius: var(--radius-md); padding: var(--space-6); }
	.stat-value { font-size: var(--font-size-3xl); font-weight: var(--font-weight-semibold); }
	.stat-label { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: var(--space-1); }
	.section-title { font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); margin-bottom: var(--space-4); }
	.findings-list { padding-left: var(--space-6); }
	.findings-list li { margin-bottom: var(--space-2); font-size: var(--font-size-sm); color: var(--color-text-secondary); }
</style>
