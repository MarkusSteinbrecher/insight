<script lang="ts">
	import '$lib/css/base.css';
	import { onMount } from 'svelte';
	import { app } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import { getThemes, applyTheme, type Mode } from '$lib/themes';

	let { children } = $props();
	let sidebarExpanded = $state(true);
	let darkMode = $state(false);
	let activeTheme = $state(0);

	function toggleDarkMode() {
		darkMode = !darkMode;
		const mode: Mode = darkMode ? 'dark' : 'light';
		applyTheme(activeTheme, mode);
		localStorage.setItem('insight-mode', mode);
	}

	function selectTheme(index: number) {
		activeTheme = index;
		const mode: Mode = darkMode ? 'dark' : 'light';
		applyTheme(index, mode);
		localStorage.setItem('insight-palette', String(index));
	}

	const allNavItems: Array<{ id: string; label: string; icon: string; devOnly?: boolean }> = [
		{ id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
		{ id: 'sources', label: 'Sources', icon: 'sources' },
		{ id: 'findings', label: 'Findings', icon: 'findings' },
		{ id: 'graph', label: 'Graph', icon: 'graph' },
		{ id: 'visuals', label: 'Visuals', icon: 'visuals' },
		{ id: 'conclusions', label: 'Conclusions', icon: 'conclusions' },
		{ id: 'deep-dive', label: 'Library', icon: 'deep-dive', devOnly: true },
		{ id: 'style-guide', label: 'Style Guide', icon: 'info', devOnly: true },
	];
	const navItems = allNavItems.filter(item => !item.devOnly || import.meta.env.DEV);

	function navCount(id: string): number | undefined {
		switch (id) {
			case 'sources': return app.stats?.sources;
			case 'findings': return app.findings?.total_findings;
			case 'visuals': return app.visuals?.total_visuals;
			case 'conclusions': return app.conclusions?.total_recommendations;
			case 'deep-dive': return app.audit?.total_sources;
			default: return undefined;
		}
	}

	onMount(() => {
		app.loadTopics();
		const savedPalette = localStorage.getItem('insight-palette');
		const savedMode = localStorage.getItem('insight-mode');
		if (savedPalette !== null) {
			const idx = parseInt(savedPalette);
			if (idx >= 0 && idx < getThemes().length) activeTheme = idx;
		}
		if (savedMode === 'dark') darkMode = true;
		// Apply on load (overrides tokens.css defaults with saved selection)
		applyTheme(activeTheme, darkMode ? 'dark' : 'light');
	});
</script>

<svelte:head>
	<title>{app.currentTitle ? `${app.currentTitle} — Insight` : 'Insight'}</title>
</svelte:head>

<div class="app-layout" class:collapsed={!sidebarExpanded}>
	<aside class="sidebar">
		<div class="sidebar-header">
			{#if sidebarExpanded}
				<span class="logo">Insight</span>
			{/if}
			<button class="sidebar-toggle" onclick={() => { sidebarExpanded = !sidebarExpanded; }} aria-label="Toggle sidebar" title={sidebarExpanded ? 'Collapse sidebar' : 'Expand sidebar'}>
				<Icon name="sidebar" size={18} />
			</button>
		</div>

		{#if sidebarExpanded && app.manifest}
			<div class="sidebar-topic">
				{#if app.manifest.topics.length > 1}
					<select class="topic-select" value={app.currentSlug} onchange={(e) => app.selectTopic(e.currentTarget.value)}>
						{#each app.manifest.topics as t}
							<option value={t.slug}>{t.title}</option>
						{/each}
					</select>
				{:else if app.manifest.topics.length === 1}
					<span class="topic-label">{app.manifest.topics[0].title}</span>
				{/if}
			</div>
		{/if}

		<nav class="sidebar-nav">
			{#each navItems as item}
				{@const count = navCount(item.id)}
				<button
					class="nav-item"
					class:active={app.activeTab === item.id}
					onclick={() => { app.activeTab = item.id; app.searchQuery = ''; }}
					title={sidebarExpanded ? '' : item.label}
				>
					<Icon name={item.icon} size={18} />
					{#if sidebarExpanded}
						<span class="nav-label">{item.label}</span>
						{#if count !== undefined}
							<span class="nav-count">{count}</span>
						{/if}
					{/if}
				</button>
			{/each}
		</nav>
	</aside>

	<div class="main-area">
		<header class="topbar">
			{#if app.currentTitle}
				<h1 class="page-title">{app.currentTitle} <span class="wip-badge">Work in progress</span></h1>
			{/if}
			<div class="topbar-search">
				<Icon name="search" size={14} />
				<input type="text" placeholder="Search..." value={app.searchQuery} oninput={(e) => { app.searchQuery = e.currentTarget.value; }} />
				{#if app.searchQuery}
					<button class="search-clear" onclick={() => { app.searchQuery = ''; }}>
						<Icon name="x" size={14} />
					</button>
				{/if}
			</div>
			<div class="topbar-spacer"></div>
			<div class="theme-picker">
				{#each getThemes() as t, i}
					<button
						class="theme-pick"
						class:active={i === activeTheme}
						onclick={() => selectTheme(i)}
						title={t.name}
						aria-label="Theme: {t.name}"
					>
						<Icon name={t.icon} size={14} />
					</button>
				{/each}
			</div>
			<button class="theme-toggle" onclick={toggleDarkMode} aria-label="Toggle dark mode" title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}>
				<Icon name={darkMode ? 'sun' : 'moon'} size={16} />
			</button>
		</header>
		<main class="content">
			{@render children()}
		</main>
	</div>
</div>

<style>
	.app-layout {
		display: flex;
		min-height: 100vh;
	}

	/* Sidebar */
	.sidebar {
		width: var(--sidebar-width);
		background: var(--color-sidebar);
		border-right: 1px solid var(--color-border);
		display: flex;
		flex-direction: column;
		position: fixed;
		top: 0;
		left: 0;
		bottom: 0;
		z-index: 200;
		transition: width 0.2s ease;
		overflow: hidden;
	}
	.collapsed .sidebar {
		width: 52px;
	}
	.sidebar-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--space-4) var(--space-3);
		height: var(--header-height);
		gap: var(--space-2);
	}
	.collapsed .sidebar-header {
		justify-content: center;
		padding: var(--space-4) 0;
	}
	.logo {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text);
		letter-spacing: -0.02em;
		white-space: nowrap;
		overflow: hidden;
		padding-left: var(--space-2);
	}
	.sidebar-toggle {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border: none;
		background: none;
		color: var(--color-text-secondary);
		cursor: pointer;
		border-radius: var(--radius-sm);
		flex-shrink: 0;
	}
	.sidebar-toggle:hover { background: var(--color-sidebar-hover); color: var(--color-text); }
	.sidebar-topic {
		padding: 0 var(--space-3) var(--space-4);
	}
	.topic-select {
		width: 100%;
		font-family: var(--font-family);
		font-size: var(--font-size-sm);
		padding: var(--space-2) var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-surface);
		color: var(--color-text);
	}
	.topic-label {
		display: block;
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		padding: 0 var(--space-1);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	/* Navigation */
	.sidebar-nav {
		flex: 1;
		padding: 0 var(--space-2);
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.collapsed .sidebar-nav {
		padding: 0 6px;
	}
	.nav-item {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		padding: var(--space-2) var(--space-3);
		border: none;
		background: none;
		color: var(--color-text-secondary);
		font-family: var(--font-family);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-sm);
		cursor: pointer;
		text-align: left;
		width: 100%;
		transition: background 0.1s, color 0.1s;
		white-space: nowrap;
		overflow: hidden;
	}
	.collapsed .nav-item {
		justify-content: center;
		padding: var(--space-2);
	}
	.nav-item:hover {
		background: var(--color-sidebar-hover);
		color: var(--color-text);
	}
	.nav-item.active {
		background: var(--color-sidebar-active);
		color: var(--color-text);
	}
	.nav-label { flex: 1; }
	.nav-count {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		background: var(--color-border-light);
		padding: 1px 6px;
		border-radius: var(--radius-full);
		min-width: 20px;
		text-align: center;
	}

	/* Main area */
	.main-area {
		flex: 1;
		margin-left: var(--sidebar-width);
		transition: margin-left 0.2s ease;
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}
	.collapsed .main-area { margin-left: 52px; }

	/* Top bar */
	.topbar {
		display: flex;
		align-items: center;
		gap: var(--space-4);
		height: var(--header-height);
		padding: 0 var(--space-6);
		border-bottom: 1px solid var(--color-border-light);
		background: var(--color-bg);
		position: sticky;
		top: 0;
		z-index: 100;
	}
	.page-title {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text);
	}
	.wip-badge {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		color: var(--color-warning);
		background: var(--color-warning-bg);
		padding: 2px var(--space-2);
		border-radius: var(--radius-full);
		vertical-align: middle;
		margin-left: var(--space-2);
	}
	.topbar-search {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-1) var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-surface);
		max-width: 240px;
	}
	.topbar-search input {
		border: none;
		background: none;
		outline: none;
		box-shadow: none;
		font-size: var(--font-size-sm);
		font-family: var(--font-family);
		width: 100%;
		color: var(--color-text);
	}
	.topbar-search input:focus {
		border: none;
		box-shadow: none;
	}
	.topbar-search .search-clear {
		display: flex;
		align-items: center;
		justify-content: center;
		background: none;
		border: none;
		color: var(--color-text-tertiary);
		cursor: pointer;
		padding: 2px;
		border-radius: var(--radius-sm);
		flex-shrink: 0;
	}
	.topbar-search .search-clear:hover { color: var(--color-text); }
	.topbar-spacer { flex: 1; }
	.theme-picker {
		display: flex;
		gap: 2px;
		background: var(--color-border-light);
		border-radius: var(--radius-sm);
		padding: 2px;
	}
	.theme-pick {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		border: none;
		background: none;
		color: var(--color-text-tertiary);
		cursor: pointer;
		border-radius: calc(var(--radius-sm) - 2px);
		transition: all 0.15s;
	}
	.theme-pick:hover { color: var(--color-text-secondary); background: var(--color-surface-hover); }
	.theme-pick.active {
		background: var(--color-surface);
		color: var(--color-text);
		box-shadow: var(--shadow-sm);
	}
	.theme-toggle {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border: none;
		background: none;
		color: var(--color-text-secondary);
		cursor: pointer;
		border-radius: var(--radius-sm);
		flex-shrink: 0;
		transition: color 0.15s;
	}
	.theme-toggle:hover { color: var(--color-text); background: var(--color-surface-hover); }

	/* Content */
	.content {
		flex: 1;
		padding: var(--space-6);
		max-width: var(--max-width);
		width: 100%;
	}

	/* Mobile */
	@media (max-width: 768px) {
		.sidebar { width: 52px; }
		.main-area { margin-left: 52px; }
		.logo, .nav-label, .nav-count, .sidebar-topic { display: none; }
		.nav-item { justify-content: center; padding: var(--space-2); }
		.sidebar-header { justify-content: center; padding: var(--space-4) 0; }
	}
</style>
