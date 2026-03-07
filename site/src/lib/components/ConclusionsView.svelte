<script lang="ts">
	import { app } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let filteredRecs = $derived.by(() => {
		if (!app.conclusions?.recommendations) return [];
		if (!app.searchQuery) return app.conclusions.recommendations;
		const q = app.searchQuery.toLowerCase();
		return app.conclusions.recommendations.filter((r: any) => r.title.toLowerCase().includes(q) || r.description.toLowerCase().includes(q));
	});

	let filteredAngles = $derived.by(() => {
		if (!app.conclusions?.angles) return [];
		if (!app.searchQuery) return app.conclusions.angles;
		const q = app.searchQuery.toLowerCase();
		return app.conclusions.angles.filter((a: any) => a.title.toLowerCase().includes(q) || a.position.toLowerCase().includes(q));
	});
</script>

{#if app.conclusions}
	{#if filteredRecs.length}
		<div class="section">
			<h2 class="section-title">
				<Icon name="conclusions" size={20} />
				Recommendations
			</h2>
			<div class="cards">
				{#each filteredRecs as rec}
					<div class="rec-card">
						<div class="rec-header">
							<h3>{rec.title}</h3>
							<div class="rec-meta">
								<span class="badge badge-{rec.priority === 'high' ? 'primary' : rec.priority === 'medium' ? 'warning' : 'success'}">{rec.priority}</span>
								{#if rec.effort}<span class="effort">{rec.effort}</span>{/if}
							</div>
						</div>
						<p class="rec-desc">{rec.description}</p>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	{#if filteredAngles.length}
		<div class="section">
			<h2 class="section-title">
				<Icon name="findings" size={20} />
				Thought Leadership Angles
			</h2>
			<div class="cards">
				{#each filteredAngles as angle}
					<div class="rec-card">
						<h3>{angle.title}</h3>
						<p class="rec-desc">{angle.position}</p>
						{#if angle.why_novel}
							<div class="novel">
								<strong>Why novel:</strong> {angle.why_novel}
							</div>
						{/if}
						{#if angle.suggested_format}
							<span class="format-badge badge badge-info">{angle.suggested_format}</span>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{/if}
{:else}
	<div class="empty-state"><p>No conclusions available yet.</p></div>
{/if}

<style>
	.section { margin-bottom: var(--space-8); }
	.section-title {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		margin-bottom: var(--space-4);
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}
	.cards { display: flex; flex-direction: column; gap: var(--space-3); }
	.rec-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		padding: var(--space-5);
		box-shadow: var(--shadow-sm);
		transition: box-shadow 0.15s;
	}
	.rec-card:hover { box-shadow: var(--shadow-md); }
	.rec-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: var(--space-2);
	}
	.rec-header h3 { font-size: var(--font-size-base); font-weight: var(--font-weight-semibold); }
	.rec-meta { display: flex; gap: var(--space-3); align-items: center; flex-shrink: 0; }
	.effort { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
	.rec-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); line-height: var(--line-height-normal); }
	.novel { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: var(--space-2); padding-top: var(--space-2); border-top: 1px solid var(--color-border-light); }
	.format-badge { margin-top: var(--space-3); }
</style>
