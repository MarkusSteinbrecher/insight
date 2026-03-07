<script lang="ts">
	import { topicManifest, currentTopic, selectTopic, searchQuery } from '$lib/stores/data';

	let manifest = $derived($topicManifest);
	let topic = $derived($currentTopic);
	let query = $state('');

	function onSearch() {
		searchQuery.set(query);
	}

	function onTopicChange(e: Event) {
		const slug = (e.target as HTMLSelectElement).value;
		selectTopic(slug);
	}
</script>

<header class="header">
	<div class="header-inner container">
		<div class="header-left">
			<a href="/" class="logo">Insight</a>
			{#if manifest && manifest.topics.length > 1}
				<select class="topic-select" value={topic} onchange={onTopicChange}>
					{#each manifest.topics as t}
						<option value={t.slug}>{t.title}</option>
					{/each}
				</select>
			{:else if manifest && manifest.topics.length === 1}
				<span class="topic-label">{manifest.topics[0].title}</span>
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
					bind:value={query}
					oninput={onSearch}
				/>
			</div>
		</div>
	</div>
</header>

<style>
	.header {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		height: var(--header-height);
		background: var(--color-bg);
		border-bottom: 1px solid var(--color-border);
		z-index: 100;
	}

	.header-inner {
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: 100%;
		gap: var(--space-6);
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: var(--space-4);
		flex-shrink: 0;
	}

	.header-right {
		flex: 1;
		display: flex;
		justify-content: flex-end;
	}

	.logo {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text);
		text-decoration: none;
	}

	.logo:hover {
		text-decoration: none;
	}

	.topic-select {
		font-family: var(--font-family);
		font-size: var(--font-size-sm);
		padding: var(--space-1) var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-bg);
		color: var(--color-text-secondary);
		outline: none;
	}

	.topic-label {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
	}

	.search-input {
		max-width: 400px;
	}
</style>
