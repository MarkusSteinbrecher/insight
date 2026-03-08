<script lang="ts">
	import { app } from '$lib/data.svelte';
	import Dashboard from '$lib/components/Dashboard.svelte';
	import SourcesTable from '$lib/components/SourcesTable.svelte';
	import FindingsView from '$lib/components/FindingsView.svelte';
	import GraphView from '$lib/components/GraphView.svelte';
	import VisualsView from '$lib/components/VisualsView.svelte';
	import ConclusionsView from '$lib/components/ConclusionsView.svelte';
	import DeepDive from '$lib/components/DeepDive.svelte';
	import StyleGuide from '$lib/components/StyleGuide.svelte';

	const isDev = import.meta.env.DEV;
</script>

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
{:else if isDev && app.activeTab === 'deep-dive'}
	<DeepDive />
{:else if isDev && app.activeTab === 'style-guide'}
	<StyleGuide />
{/if}
