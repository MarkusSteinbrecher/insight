<script lang="ts">
	import { conclusionsData } from '$lib/stores/data';

	let data = $derived($conclusionsData);
</script>

<div class="conclusions-view">
	{#if data}
		{#if data.recommendations && data.recommendations.length > 0}
			<section class="mb-6">
				<h2 class="section-heading">Recommendations</h2>
				<div class="rec-grid">
					{#each data.recommendations as rec}
						<div class="card rec-card">
							<div class="rec-header">
								<span class="badge badge-{rec.priority === 'high' ? 'error' : rec.priority === 'medium' ? 'warning' : 'primary'}">
									{rec.priority} priority
								</span>
								<span class="badge">{rec.effort} effort</span>
							</div>
							<h3 class="rec-title">{rec.title}</h3>
							<p class="rec-desc">{rec.description}</p>
							{#if rec.dependencies.length > 0}
								<p class="text-xs text-secondary mt-2">Depends on: {rec.dependencies.join(', ')}</p>
							{/if}
						</div>
					{/each}
				</div>
			</section>
		{/if}

		{#if data.angles && data.angles.length > 0}
			<section class="mb-6">
				<h2 class="section-heading">Thought Leadership Angles</h2>
				<div class="angle-grid">
					{#each data.angles as angle}
						<div class="card angle-card">
							<div class="angle-header">
								<span class="badge badge-primary">{angle.suggested_format}</span>
							</div>
							<h3 class="angle-title">{angle.title}</h3>
							<p class="angle-position">{angle.position}</p>
							<p class="text-xs text-secondary mt-2">{angle.why_novel}</p>
						</div>
					{/each}
				</div>
			</section>
		{/if}

		<p class="text-xs text-secondary">
			{data.total_recommendations} recommendations, {data.total_angles} angles · Generated {data.generated}
		</p>
	{:else}
		<div class="empty-state">
			<p>No conclusions available. Complete Phase 3 to generate recommendations.</p>
		</div>
	{/if}
</div>

<style>
	.section-heading {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		margin-bottom: var(--space-4);
	}

	.rec-grid, .angle-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
		gap: var(--space-4);
	}

	.rec-card, .angle-card {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.rec-header, .angle-header {
		display: flex;
		gap: var(--space-2);
	}

	.rec-title, .angle-title {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-medium);
	}

	.rec-desc, .angle-position {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		line-height: var(--line-height-relaxed);
	}
</style>
