<script lang="ts">
	import TabNav from '$lib/components/TabNav.svelte';
	import Dashboard from '$lib/components/Dashboard.svelte';
	import SourcesTable from '$lib/components/SourcesTable.svelte';
	import FindingsView from '$lib/components/FindingsView.svelte';
	import GraphView from '$lib/components/GraphView.svelte';
	import ConclusionsView from '$lib/components/ConclusionsView.svelte';
	import { stats, sourcesData, findingsData, conclusionsData, currentTopicTitle } from '$lib/stores/data';

	let activeTab = $state('dashboard');
	let title = $derived($currentTopicTitle);
	let s = $derived($stats);
	let src = $derived($sourcesData);
	let findings = $derived($findingsData);
	let conclusions = $derived($conclusionsData);

	let tabs = $derived([
		{ id: 'dashboard', label: 'Dashboard' },
		{ id: 'sources', label: 'Sources', count: s?.sources ?? 0 },
		{ id: 'findings', label: 'Findings', count: findings?.total_findings ?? 0 },
		{ id: 'graph', label: 'Graph' },
		{ id: 'conclusions', label: 'Conclusions', count: conclusions?.total_recommendations ?? 0 }
	]);
</script>

<svelte:head>
	<title>{title ? `${title} — Insight` : 'Insight'}</title>
</svelte:head>

{#if title}
	<h1 class="page-title">{title}</h1>
{/if}

<TabNav {tabs} active={activeTab} onselect={(id) => (activeTab = id)} />

{#if activeTab === 'dashboard'}
	<Dashboard />
{:else if activeTab === 'sources'}
	<SourcesTable />
{:else if activeTab === 'findings'}
	<FindingsView />
{:else if activeTab === 'graph'}
	<GraphView />
{:else if activeTab === 'conclusions'}
	<ConclusionsView />
{/if}

<style>
	.page-title {
		font-size: var(--font-size-2xl);
		font-weight: var(--font-weight-semibold);
		margin-bottom: var(--space-4);
	}
</style>
