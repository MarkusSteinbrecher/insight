<script lang="ts">
	import '$lib/css/base.css';
	import Header from '$lib/components/Header.svelte';
	import { loadTopics } from '$lib/stores/data';
	import { onMount } from 'svelte';

	let { children } = $props();

	onMount(() => {
		loadTopics();
	});
</script>

<Header />
<main class="container">
	{@render children()}
</main>

<style>
	main {
		padding-top: calc(var(--header-height) + var(--space-6));
		padding-bottom: var(--space-16);
	}
</style>
