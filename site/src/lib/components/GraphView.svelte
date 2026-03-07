<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import { app } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let svgEl: SVGSVGElement;
	let width = $state(900);
	let height = $state(600);

	let visible = $state<Record<string, boolean>>({ finding: true, claim: true, extract: false, source: true });
	let filterAuthor = $state('');
	let hoveredNode = $state<any>(null);
	let selectedNode = $state<any>(null);

	interface GNode extends d3.SimulationNodeDatum {
		id: string; label: string; type: string; group: number; radius: number;
		author?: string; category?: string; theme?: string; text?: string;
		format?: string; extractType?: string; sourceType?: string;
	}
	interface GLink extends d3.SimulationLinkDatum<GNode> {
		type: string;
	}

	let simulation: d3.Simulation<GNode, GLink> | null = null;

	let authors = $derived.by(() => {
		if (!app.graph) return [];
		const set = new Set<string>();
		for (const n of app.graph.nodes) if (n.author) set.add(n.author);
		return [...set].sort();
	});

	// Find connected nodes for the selected node
	let connections = $derived.by(() => {
		if (!selectedNode || !app.graph) return { incoming: [] as any[], outgoing: [] as any[] };
		const nodeMap = new Map<string, any>();
		for (const n of app.graph.nodes) nodeMap.set(n.id, n);

		const incoming: any[] = [];
		const outgoing: any[] = [];
		for (const e of app.graph.edges) {
			const src = typeof e.source === 'string' ? e.source : e.source.id;
			const tgt = typeof e.target === 'string' ? e.target : e.target.id;
			if (src === selectedNode.id && nodeMap.has(tgt)) {
				outgoing.push({ node: nodeMap.get(tgt), edgeType: e.type });
			}
			if (tgt === selectedNode.id && nodeMap.has(src)) {
				incoming.push({ node: nodeMap.get(src), edgeType: e.type });
			}
		}
		return { incoming, outgoing };
	});

	const entityColors: Record<string, string> = {
		finding: getComputedStyle(document.documentElement).getPropertyValue('--color-finding').trim() || '#D97757',
		claim: getComputedStyle(document.documentElement).getPropertyValue('--color-claim').trim() || '#3B6EC4',
		extract: getComputedStyle(document.documentElement).getPropertyValue('--color-extract').trim() || '#7C6F9B',
		source: getComputedStyle(document.documentElement).getPropertyValue('--color-source').trim() || '#C4841D',
	};

	function typeColor(type: string): string {
		return entityColors[type] ?? '#64635E';
	}

	function selectNodeById(id: string) {
		if (!app.graph) return;
		const node = app.graph.nodes.find((n: any) => n.id === id);
		if (node) selectedNode = node;
	}

	function buildGraph() {
		if (!app.graph || !svgEl) return;

		const data = app.graph;
		const visibleTypes = new Set(Object.entries(visible).filter(([, v]) => v).map(([k]) => k));
		const visibleIds = new Set<string>();

		let nodes: GNode[] = [];
		for (const n of data.nodes) {
			if (!visibleTypes.has(n.type)) continue;
			if (filterAuthor && n.author && n.author !== filterAuthor) continue;
			if (app.searchQuery && !n.label.toLowerCase().includes(app.searchQuery.toLowerCase())) continue;
			const radius = n.type === 'finding' ? 12 : n.type === 'claim' ? 7 : n.type === 'source' ? 9 : 4;
			nodes.push({ ...n, group: 0, radius });
			visibleIds.add(n.id);
		}

		let links: GLink[] = [];
		for (const e of data.edges) {
			const src = typeof e.source === 'string' ? e.source : (e.source as any).id;
			const tgt = typeof e.target === 'string' ? e.target : (e.target as any).id;
			if (visibleIds.has(src) && visibleIds.has(tgt)) {
				links.push({ source: src, target: tgt, type: e.type });
			}
		}

		if (nodes.length > 500) {
			const priority = { finding: 0, claim: 1, source: 2, extract: 3 };
			nodes.sort((a, b) => (priority[a.type as keyof typeof priority] ?? 9) - (priority[b.type as keyof typeof priority] ?? 9));
			const kept = new Set(nodes.slice(0, 500).map(n => n.id));
			nodes = nodes.filter(n => kept.has(n.id));
			links = links.filter(l => {
				const s = typeof l.source === 'string' ? l.source : (l.source as any).id;
				const t = typeof l.target === 'string' ? l.target : (l.target as any).id;
				return kept.has(s) && kept.has(t);
			});
		}

		const svg = d3.select(svgEl);
		svg.selectAll('*').remove();

		if (nodes.length === 0) return;

		const g = svg.append('g');

		svg.call(d3.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.1, 4])
			.on('zoom', (event) => g.attr('transform', event.transform))
		);

		const link = g.append('g').attr('stroke', '#E5E2DB').attr('stroke-opacity', 0.6)
			.selectAll('line').data(links).join('line').attr('stroke-width', 1);

		let dragged = false;
		const node = g.append('g')
			.selectAll('circle').data(nodes).join('circle')
			.attr('r', d => d.radius)
			.attr('fill', d => typeColor(d.type))
			.attr('stroke', '#fff').attr('stroke-width', 1.5)
			.style('cursor', 'pointer')
			.on('mouseenter', (_, d) => { hoveredNode = d; })
			.on('mouseleave', () => { hoveredNode = null; })
			.call(d3.drag<SVGCircleElement, GNode>()
				.on('start', (event, d) => { dragged = false; if (!event.active) simulation?.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
				.on('drag', (event, d) => { dragged = true; d.fx = event.x; d.fy = event.y; })
				.on('end', (event, d) => {
					if (!event.active) simulation?.alphaTarget(0);
					d.fx = null; d.fy = null;
					if (!dragged) { selectedNode = selectedNode?.id === d.id ? null : d; }
				})
			);

		simulation = d3.forceSimulation(nodes)
			.force('link', d3.forceLink<GNode, GLink>(links).id(d => d.id).distance(30))
			.force('charge', d3.forceManyBody().strength(-40))
			.force('center', d3.forceCenter(width / 2, height / 2))
			.force('collision', d3.forceCollide<GNode>().radius(d => d.radius + 2))
			.on('tick', () => {
				link.attr('x1', (d: any) => d.source.x).attr('y1', (d: any) => d.source.y)
					.attr('x2', (d: any) => d.target.x).attr('y2', (d: any) => d.target.y);
				node.attr('cx', (d: any) => d.x).attr('cy', (d: any) => d.y);
			});
	}

	onMount(() => {
		const observer = new ResizeObserver(entries => {
			for (const entry of entries) {
				width = entry.contentRect.width;
				height = Math.max(500, entry.contentRect.height);
			}
		});
		observer.observe(svgEl.parentElement!);
		return () => observer.disconnect();
	});

	$effect(() => {
		void app.graph;
		void visible;
		void filterAuthor;
		void app.searchQuery;
		void width;
		buildGraph();
	});
</script>

{#if app.graph}
	<div class="toolbar">
		<div class="toggles">
			{#each Object.entries(visible) as [type, on]}
				<label class="toggle">
					<input type="checkbox" checked={on} onchange={() => { visible = { ...visible, [type]: !on }; }} />
					<span class="dot" style="background:{typeColor(type)}"></span>
					{type}s
				</label>
			{/each}
		</div>
		<select bind:value={filterAuthor}>
			<option value="">All authors</option>
			{#each authors as a}<option value={a}>{a}</option>{/each}
		</select>
	</div>

	<div class="graph-layout" class:panel-open={selectedNode}>
		<div class="graph-container">
			<svg bind:this={svgEl} {width} {height}></svg>
			{#if hoveredNode && !selectedNode}
				<div class="tooltip">
					<span class="type-badge" style="background:{typeColor(hoveredNode.type)}">{hoveredNode.type}</span>
					<strong>{hoveredNode.label}</strong>
				</div>
			{/if}
		</div>

		{#if selectedNode}
			<aside class="detail-panel">
				<div class="panel-header">
					<span class="type-badge" style="background:{typeColor(selectedNode.type)}">{selectedNode.type}</span>
					<button class="close-btn" onclick={() => { selectedNode = null; }}>
						<Icon name="x" size={16} />
					</button>
				</div>

				<h3 class="panel-title">{selectedNode.label}</h3>

				{#if selectedNode.text && selectedNode.text !== selectedNode.label}
					<p class="panel-text">{selectedNode.text}</p>
				{/if}

				<div class="panel-fields">
					<div class="field">
						<span class="field-label">ID</span>
						<span class="field-value mono">{selectedNode.id}</span>
					</div>
					{#if selectedNode.author}
						<div class="field">
							<span class="field-label">Author</span>
							<span class="field-value">{selectedNode.author}</span>
						</div>
					{/if}
					{#if selectedNode.theme}
						<div class="field">
							<span class="field-label">Theme</span>
							<span class="field-value">{selectedNode.theme}</span>
						</div>
					{/if}
					{#if selectedNode.category}
						<div class="field">
							<span class="field-label">Category</span>
							<span class="field-value">{selectedNode.category}</span>
						</div>
					{/if}
					{#if selectedNode.extractType}
						<div class="field">
							<span class="field-label">Extract Type</span>
							<span class="field-value">{selectedNode.extractType}</span>
						</div>
					{/if}
					{#if selectedNode.format}
						<div class="field">
							<span class="field-label">Format</span>
							<span class="field-value">{selectedNode.format}</span>
						</div>
					{/if}
					{#if selectedNode.sourceType}
						<div class="field">
							<span class="field-label">Source Type</span>
							<span class="field-value">{selectedNode.sourceType}</span>
						</div>
					{/if}
				</div>

				{#if connections.incoming.length > 0}
					<div class="connections-section">
						<h4 class="connections-title">Incoming ({connections.incoming.length})</h4>
						{#each connections.incoming as conn}
							<button class="connection-item" onclick={() => selectNodeById(conn.node.id)}>
								<span class="conn-dot" style="background:{typeColor(conn.node.type)}"></span>
								<span class="conn-label">{conn.node.label}</span>
								<span class="conn-edge">{conn.edgeType}</span>
							</button>
						{/each}
					</div>
				{/if}

				{#if connections.outgoing.length > 0}
					<div class="connections-section">
						<h4 class="connections-title">Outgoing ({connections.outgoing.length})</h4>
						{#each connections.outgoing as conn}
							<button class="connection-item" onclick={() => selectNodeById(conn.node.id)}>
								<span class="conn-dot" style="background:{typeColor(conn.node.type)}"></span>
								<span class="conn-label">{conn.node.label}</span>
								<span class="conn-edge">{conn.edgeType}</span>
							</button>
						{/each}
					</div>
				{/if}
			</aside>
		{/if}
	</div>
{:else}
	<div class="empty-state"><p>No graph data available.</p></div>
{/if}

<style>
	/* Use more width than default */
	:global(.content:has(.graph-layout)) {
		max-width: 80vw;
	}

	/* Layout */
	.graph-layout {
		display: flex;
		gap: var(--space-4);
		min-height: calc(100vh - var(--header-height) - var(--space-12));
	}
	.graph-container {
		flex: 1;
		position: relative;
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		overflow: hidden;
		min-width: 0;
	}
	svg { display: block; width: 100%; min-height: 500px; }

	.tooltip {
		position: absolute;
		top: var(--space-3);
		left: var(--space-3);
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		padding: var(--space-2) var(--space-3);
		font-size: var(--font-size-sm);
		box-shadow: var(--shadow-md);
		pointer-events: none;
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}
	.type-badge {
		display: inline-block;
		padding: 1px 6px;
		border-radius: var(--radius-sm);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		color: white;
		text-transform: capitalize;
	}
	.tooltip strong { font-weight: var(--font-weight-medium); }

	/* Detail panel */
	.detail-panel {
		width: 360px;
		flex-shrink: 0;
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		padding: var(--space-5);
		overflow-y: auto;
		max-height: 80vh;
	}
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-4);
	}
	.close-btn {
		background: none;
		border: none;
		color: var(--color-text-tertiary);
		cursor: pointer;
		padding: var(--space-1);
		border-radius: var(--radius-sm);
	}
	.close-btn:hover { background: var(--color-surface-hover); color: var(--color-text); }
	.panel-title {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		line-height: var(--line-height-tight);
		margin-bottom: var(--space-3);
	}
	.panel-text {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		line-height: var(--line-height-normal);
		margin-bottom: var(--space-4);
		padding-bottom: var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
	}

	/* Fields */
	.panel-fields {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
		padding-bottom: var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
		margin-bottom: var(--space-4);
	}
	.field {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.field-label {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-tertiary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	.field-value {
		font-size: var(--font-size-sm);
		color: var(--color-text);
		word-break: break-word;
	}
	.mono { font-family: monospace; font-size: var(--font-size-xs); color: var(--color-text-secondary); }

	/* Connections */
	.connections-section {
		margin-bottom: var(--space-4);
	}
	.connections-title {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-tertiary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: var(--space-2);
	}
	.connection-item {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		width: 100%;
		padding: var(--space-2) var(--space-3);
		background: none;
		border: 1px solid transparent;
		border-radius: var(--radius-sm);
		cursor: pointer;
		font-family: var(--font-family);
		font-size: var(--font-size-sm);
		text-align: left;
		color: var(--color-text);
		transition: background 0.1s, border-color 0.1s;
	}
	.connection-item:hover {
		background: var(--color-surface-hover);
		border-color: var(--color-border-light);
	}
	.conn-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
	.conn-label {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.conn-edge {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		flex-shrink: 0;
		padding: 1px 6px;
		background: var(--color-border-light);
		border-radius: var(--radius-sm);
	}
</style>
