<script lang="ts">
	interface Tab {
		id: string;
		label: string;
		count?: number;
	}

	let { tabs, active, onselect }: { tabs: Tab[]; active: string; onselect: (id: string) => void } = $props();
</script>

<nav class="tab-nav">
	{#each tabs as tab}
		<button
			class="tab-item"
			class:active={active === tab.id}
			onclick={() => onselect(tab.id)}
		>
			{tab.label}
			{#if tab.count !== undefined}
				<span class="tab-count">{tab.count}</span>
			{/if}
		</button>
	{/each}
</nav>

<style>
	.tab-nav {
		display: flex;
		gap: var(--space-1);
		border-bottom: 1px solid var(--color-border);
		margin-bottom: var(--space-6);
	}

	.tab-item {
		padding: var(--space-3) var(--space-5);
		font-family: var(--font-family);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
		background: none;
		border: none;
		border-bottom: 2px solid transparent;
		cursor: pointer;
		transition: color 0.15s, border-color 0.15s;
	}

	.tab-item:hover {
		color: var(--color-text);
	}

	.tab-item.active {
		color: var(--color-primary);
		border-bottom-color: var(--color-primary);
	}

	.tab-count {
		margin-left: var(--space-2);
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
	}
</style>
