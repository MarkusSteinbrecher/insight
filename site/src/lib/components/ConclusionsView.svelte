<script lang="ts">
	import { app } from '$lib/data.svelte';
</script>

{#if app.conclusions}
	{@const c = app.conclusions}

	{#if c.recommendations?.length}
		<h2 class="section-title">Recommendations</h2>
		{#each c.recommendations as rec}
			<div class="rec-card">
				<div class="rec-header">
					<h3>{rec.title}</h3>
					<div class="rec-meta">
						<span class="badge badge-{rec.priority === 'high' ? 'primary' : rec.priority === 'medium' ? 'warning' : 'success'}">{rec.priority}</span>
						{#if rec.effort}<span class="dim">Effort: {rec.effort}</span>{/if}
					</div>
				</div>
				<p class="rec-desc">{rec.description}</p>
			</div>
		{/each}
	{/if}

	{#if c.angles?.length}
		<h2 class="section-title" style="margin-top: var(--space-8)">Thought Leadership Angles</h2>
		{#each c.angles as angle}
			<div class="rec-card">
				<h3>{angle.title}</h3>
				<p class="rec-desc">{angle.position}</p>
				{#if angle.why_novel}<p class="novel"><strong>Why novel:</strong> {angle.why_novel}</p>{/if}
				{#if angle.suggested_format}<span class="dim">Format: {angle.suggested_format}</span>{/if}
			</div>
		{/each}
	{/if}
{:else}
	<div class="empty-state"><p>No conclusions available yet.</p></div>
{/if}

<style>
	.section-title { font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); margin-bottom: var(--space-4); }
	.rec-card { border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: var(--space-5); margin-bottom: var(--space-4); }
	.rec-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-2); }
	.rec-header h3 { font-size: var(--font-size-base); font-weight: var(--font-weight-semibold); }
	.rec-meta { display: flex; gap: var(--space-3); align-items: center; }
	.rec-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
	.novel { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: var(--space-2); }
	.dim { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
</style>
