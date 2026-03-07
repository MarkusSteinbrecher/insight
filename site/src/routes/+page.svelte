<script lang="ts">
	import { app } from '$lib/data.svelte';
	import Dashboard from '$lib/components/Dashboard.svelte';
	import SourcesTable from '$lib/components/SourcesTable.svelte';
	import FindingsView from '$lib/components/FindingsView.svelte';
	import GraphView from '$lib/components/GraphView.svelte';
	import VisualsView from '$lib/components/VisualsView.svelte';
	import ConclusionsView from '$lib/components/ConclusionsView.svelte';
	import DeepDive from '$lib/components/DeepDive.svelte';

	let tabs = $derived([
		{ id: 'dashboard', label: 'Dashboard' },
		{ id: 'sources', label: 'Sources', count: app.stats?.sources ?? 0 },
		{ id: 'findings', label: 'Findings', count: app.findings?.total_findings ?? 0 },
		{ id: 'graph', label: 'Graph' },
		{ id: 'visuals', label: 'Visuals', count: app.visuals?.total_visuals ?? 0 },
		{ id: 'conclusions', label: 'Conclusions', count: app.conclusions?.total_recommendations ?? 0 },
		{ id: 'deep-dive', label: 'Deep Dive', count: app.audit?.total_sources ?? 0 }
	]);
</script>

<svelte:head>
	<title>{app.currentTitle ? `${app.currentTitle} — Insight` : 'Insight'}</title>
</svelte:head>

{#if app.currentTitle}
	<h1 class="page-title">{app.currentTitle}</h1>
{/if}

<nav class="tab-nav">
	{#each tabs as tab}
		<button
			class="tab-btn"
			class:active={app.activeTab === tab.id}
			onclick={() => { app.activeTab = tab.id; }}
		>
			{tab.label}
			{#if tab.count !== undefined}
				<span class="tab-count">{tab.count}</span>
			{/if}
		</button>
	{/each}
</nav>

{#if app.activeTab === 'dashboard'}
	<Dashboard />
{:else if app.activeTab === 'sources'}
	<SourcesTable />
{:else if app.activeTab === 'findings'}
	<FindingsView />
{:else if app.activeTab === 'graph'}
	<GraphView />
{:else if app.activeTab === 'visuals'}
	<VisualsView />
{:else if app.activeTab === 'conclusions'}
	<ConclusionsView />
{:else if app.activeTab === 'deep-dive'}
	<DeepDive />
{/if}

<style>
	.page-title { font-size: var(--font-size-2xl); font-weight: var(--font-weight-semibold); margin-bottom: var(--space-4); }
	.tab-nav { display: flex; gap: var(--space-1); border-bottom: 1px solid var(--color-border); margin-bottom: var(--space-6); }
	.tab-btn {
		padding: var(--space-3) var(--space-5);
		font-family: var(--font-family); font-size: var(--font-size-sm); font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary); background: none; border: none;
		border-bottom: 2px solid transparent; cursor: pointer;
	}
	.tab-btn:hover { color: var(--color-text); }
	.tab-btn.active { color: var(--color-primary); border-bottom-color: var(--color-primary); }
	.tab-count { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-left: var(--space-1); }
</style>
