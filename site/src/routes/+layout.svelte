<script lang="ts">
	import '$lib/css/base.css';
	import { onMount } from 'svelte';
	import { app } from '$lib/data.svelte';

	let { children } = $props();

	onMount(() => {
		app.loadTopics();
	});
</script>

<header class="header">
	<div class="header-inner container">
		<div class="header-left">
			<span class="logo">Insight</span>
			{#if app.manifest && app.manifest.topics.length > 1}
				<select class="topic-select" value={app.currentSlug} onchange={(e) => app.selectTopic(e.currentTarget.value)}>
					{#each app.manifest.topics as t}
						<option value={t.slug}>{t.title}</option>
					{/each}
				</select>
			{:else if app.manifest && app.manifest.topics.length === 1}
				<span class="topic-label">{app.manifest.topics[0].title}</span>
			{/if}
		</div>
		<div class="header-right">
			<div class="search-wrapper">
				<svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
				</svg>
				<input
					class="search-input"
					type="text"
					placeholder="Search claims, sources, findings..."
					value={app.searchQuery}
					oninput={(e) => { app.searchQuery = e.currentTarget.value; }}
				/>
			</div>
		</div>
	</div>
</header>
<main class="container">
	{@render children()}
</main>

<style>
	.header {
		position: fixed; top: 0; left: 0; right: 0;
		height: var(--header-height);
		background: var(--color-bg);
		border-bottom: 1px solid var(--color-border);
		z-index: 100;
	}
	.header-inner { display: flex; align-items: center; justify-content: space-between; height: 100%; gap: var(--space-6); }
	.header-left { display: flex; align-items: center; gap: var(--space-4); flex-shrink: 0; }
	.header-right { flex: 1; display: flex; justify-content: flex-end; }
	.logo { font-size: var(--font-size-xl); font-weight: var(--font-weight-semibold); color: var(--color-text); }
	.topic-select {
		font-family: var(--font-family); font-size: var(--font-size-sm);
		padding: var(--space-1) var(--space-3);
		border: 1px solid var(--color-border); border-radius: var(--radius-sm);
		background: var(--color-bg); color: var(--color-text-secondary);
	}
	.topic-label { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
	.search-wrapper { position: relative; display: inline-flex; width: 100%; max-width: 400px; }
	.search-icon { position: absolute; left: var(--space-3); top: 50%; transform: translateY(-50%); color: var(--color-text-tertiary); pointer-events: none; }
	.search-input {
		width: 100%; padding: var(--space-2) var(--space-4) var(--space-2) var(--space-10);
		font-family: var(--font-family); font-size: var(--font-size-sm);
		border: 1px solid var(--color-border); border-radius: var(--radius-full);
		background: var(--color-bg); outline: none;
	}
	.search-input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-light); }
	main { padding-top: calc(var(--header-height) + var(--space-6)); padding-bottom: var(--space-16); }
</style>
