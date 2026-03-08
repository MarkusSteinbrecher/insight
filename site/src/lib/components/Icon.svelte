<script lang="ts">
	let { name, size = 18 }: { name: string; size?: number } = $props();
</script>

<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	stroke="currentColor"
	stroke-width="1.75"
	stroke-linecap="round"
	stroke-linejoin="round"
	class="icon icon-{name}"
>
	{#if name === 'dashboard'}
		<rect x="3" y="3" width="7" height="7" rx="1" />
		<rect x="14" y="3" width="7" height="4" rx="1" />
		<rect x="3" y="14" width="7" height="7" rx="1" />
		<rect x="14" y="11" width="7" height="10" rx="1" />
	{:else if name === 'sources'}
		<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
		<path d="M8 7h6" /><path d="M8 11h8" />
	{:else if name === 'findings'}
		<path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 1 1 7.072 0l-.548.547A3.374 3.374 0 0 0 12 18.469a3.374 3.374 0 0 0-.964-1.46z" />
	{:else if name === 'graph'}
		<circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
		<path d="m8.59 13.51 6.83 3.98M15.41 6.51l-6.82 3.98" />
	{:else if name === 'visuals'}
		<rect x="3" y="3" width="18" height="18" rx="2" />
		<circle cx="9" cy="9" r="2" />
		<path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
	{:else if name === 'conclusions'}
		<circle cx="12" cy="12" r="10" />
		<circle cx="12" cy="12" r="6" />
		<circle cx="12" cy="12" r="2" />
	{:else if name === 'deep-dive'}
		<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
		<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
	{:else if name === 'search'}
		<circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
	{:else if name === 'sidebar'}
		<rect x="3" y="3" width="18" height="18" rx="2" />
		<path d="M9 3v18" />
	{:else if name === 'chevron-down'}
		<path d="m6 9 6 6 6-6" />
	{:else if name === 'chevron-right'}
		<path d="m9 18 6-6-6-6" />
	{:else if name === 'external'}
		<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
		<polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
	{:else if name === 'filter'}
		<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
	{:else if name === 'x'}
		<path d="M18 6 6 18" /><path d="m6 6 12 12" />
	{:else if name === 'arrow-up'}
		<path d="m5 12 7-7 7 7" /><path d="M12 19V5" />
	{:else if name === 'arrow-down'}
		<path d="M12 5v14" /><path d="m19 12-7 7-7-7" />
	{:else if name === 'info'}
		<circle cx="12" cy="12" r="10" /><path d="M12 16v-4" /><path d="M12 8h.01" />
	{:else if name === 'extract'}
		<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
		<path d="M14 2v6h6" /><path d="M8 13h8" /><path d="M8 17h8" />
	{:else if name === 'claim'}
		<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
	{:else if name === 'source'}
		<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
	{:else if name === 'contradiction'}
		<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
		<path d="M12 9v4" /><path d="M12 17h.01" />
	{:else if name === 'zap'}
		<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
	{:else if name === 'flame'}
		<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />
	{:else if name === 'rocket'}
		<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" />
		<path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" />
		<path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" />
		<path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" />
	{:else if name === 'sparkles'}
		<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
		<path d="M5 3v4" /><path d="M19 17v4" /><path d="M3 5h4" /><path d="M17 19h4" />
	{:else if name === 'sun'}
		<circle cx="12" cy="12" r="4" />
		<path d="M12 2v2" /><path d="M12 20v2" /><path d="m4.93 4.93 1.41 1.41" /><path d="m17.66 17.66 1.41 1.41" />
		<path d="M2 12h2" /><path d="M20 12h2" /><path d="m6.34 17.66-1.41 1.41" /><path d="m19.07 4.93-1.41 1.41" />
	{:else if name === 'moon'}
		<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
	{:else if name === 'globe'}
		<circle cx="12" cy="12" r="10" />
		<path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
		<path d="M2 12h20" />
	{:else if name === 'youtube'}
		<path d="M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 1.4-1.4 49.56 49.56 0 0 1 16.2 0A2 2 0 0 1 21.5 7a24.12 24.12 0 0 1 0 10 2 2 0 0 1-1.4 1.4 49.55 49.55 0 0 1-16.2 0A2 2 0 0 1 2.5 17" />
		<path d="m10 15 5-3-5-3z" />
	{:else if name === 'file-text'}
		<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
		<path d="M14 2v6h6" /><path d="M16 13H8" /><path d="M16 17H8" /><path d="M10 9H8" />
	{/if}
</svg>

<style>
	.icon {
		flex-shrink: 0;
		transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
	}

	/* Nav-item hover animations — triggered by parent :hover */
	:global(.nav-item:hover) .icon-dashboard {
		transform: scale(1.12);
	}
	:global(.nav-item:hover) .icon-sources {
		transform: rotate(-4deg) scale(1.08);
	}
	:global(.nav-item:hover) .icon-findings {
		transform: rotate(12deg);
	}
	:global(.nav-item:hover) .icon-graph {
		transform: scale(1.15);
	}
	:global(.nav-item:hover) .icon-visuals {
		transform: scale(1.1) rotate(2deg);
	}
	:global(.nav-item:hover) .icon-conclusions {
		transform: rotate(45deg);
	}
	:global(.nav-item:hover) .icon-deep-dive {
		transform: translateY(-1px) scale(1.08);
	}
</style>
