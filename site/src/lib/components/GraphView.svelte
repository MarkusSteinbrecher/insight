<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import { app } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let svgEl: SVGSVGElement;
	let width = $state(900);
	let height = $state(600);

	let visible = $state<Record<string, boolean>>({ finding: true, claim: true, extract: false, source: true });
	let alignBy = $state<string>('');
	let filterAuthor = $state('');
	let categoryFilter = $state('all');
	let hoveredNode = $state<any>(null);
	let selectedNode = $state<any>(null);
	let graphStats = $state({ nodes: 0, links: 0, indirect: 0 });

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

	let categories = $derived.by(() => {
		if (!app.graph) return [];
		const cats = new Set<string>();
		for (const n of app.graph.nodes) if (n.category) cats.add(n.category);
		return [...cats].sort();
	});

	let categoryCounts = $derived.by(() => {
		if (!app.graph) return new Map<string, number>();
		const counts = new Map<string, number>();
		for (const n of app.graph.nodes) {
			if (n.category) counts.set(n.category, (counts.get(n.category) || 0) + 1);
		}
		return counts;
	});

	let typeCounts = $derived.by(() => {
		if (!app.graph) return new Map<string, number>();
		const counts = new Map<string, number>();
		for (const n of app.graph.nodes) {
			counts.set(n.type, (counts.get(n.type) || 0) + 1);
		}
		return counts;
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

	function typeColor(type: string): string {
		const token = `--color-${type}`;
		const val = getComputedStyle(document.documentElement).getPropertyValue(token).trim();
		return val || '#64635E';
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

		const allNodeTypes = new Map<string, string>();
		for (const n of data.nodes) allNodeTypes.set(n.id, n.type);

		// When a category is selected, find matching finding IDs and their connected node IDs
		let categoryAllowedIds: Set<string> | null = null;
		if (categoryFilter !== 'all') {
			categoryAllowedIds = new Set<string>();
			for (const n of data.nodes) {
				if (n.category === categoryFilter) categoryAllowedIds.add(n.id);
			}
			// Include nodes connected to matching findings
			for (const e of data.edges) {
				const src = typeof e.source === 'string' ? e.source : (e.source as any).id;
				const tgt = typeof e.target === 'string' ? e.target : (e.target as any).id;
				if (categoryAllowedIds.has(src)) categoryAllowedIds.add(tgt);
				if (categoryAllowedIds.has(tgt)) categoryAllowedIds.add(src);
			}
		}

		// Compute source impact: how many claims from each source reach a finding
		const sourceExtractsMap = new Map<string, Set<string>>();
		const extractClaimsMap = new Map<string, Set<string>>();
		const claimHasFinding = new Set<string>();

		for (const e of data.edges) {
			const src = typeof e.source === 'string' ? e.source : (e.source as any).id;
			const tgt = typeof e.target === 'string' ? e.target : (e.target as any).id;
			const srcType = allNodeTypes.get(src), tgtType = allNodeTypes.get(tgt);
			if (srcType === 'source' && tgtType === 'extract') {
				if (!sourceExtractsMap.has(src)) sourceExtractsMap.set(src, new Set());
				sourceExtractsMap.get(src)!.add(tgt);
			}
			if (srcType === 'extract' && tgtType === 'claim') {
				if (!extractClaimsMap.has(src)) extractClaimsMap.set(src, new Set());
				extractClaimsMap.get(src)!.add(tgt);
			}
			if (tgtType === 'extract' && srcType === 'claim') {
				if (!extractClaimsMap.has(tgt)) extractClaimsMap.set(tgt, new Set());
				extractClaimsMap.get(tgt)!.add(src);
			}
			if ((srcType === 'claim' && tgtType === 'finding') || (tgtType === 'claim' && srcType === 'finding')) {
				if (srcType === 'claim') claimHasFinding.add(src);
				if (tgtType === 'claim') claimHasFinding.add(tgt);
			}
		}

		const sourceImpact = new Map<string, number>();
		for (const [sourceId, extracts] of sourceExtractsMap) {
			let count = 0;
			for (const ext of extracts) {
				for (const claimId of extractClaimsMap.get(ext) ?? []) {
					if (claimHasFinding.has(claimId)) count++;
				}
			}
			sourceImpact.set(sourceId, count);
		}
		const maxImpact = Math.max(1, ...sourceImpact.values());

		// When extracts are visible, only include "chain" extracts that connect to a claim
		// (otherwise we'd show 5000+ leaf extracts that add no insight)
		const chainExtracts = new Set<string>();
		if (visibleTypes.has('extract')) {
			for (const extractId of extractClaimsMap.keys()) {
				chainExtracts.add(extractId);
			}
		}

		let nodes: GNode[] = [];
		for (const n of data.nodes) {
			if (!visibleTypes.has(n.type)) continue;
			if (n.type === 'extract' && !chainExtracts.has(n.id)) continue;
			if (filterAuthor && n.author && n.author !== filterAuthor) continue;
			if (categoryAllowedIds && !categoryAllowedIds.has(n.id)) continue;
			if (app.searchQuery && !n.label.toLowerCase().includes(app.searchQuery.toLowerCase())) continue;
			let radius: number;
			if (n.type === 'source') {
				const impact = sourceImpact.get(n.id) ?? 0;
				radius = 5 + 10 * (impact / maxImpact); // 5–15 based on impact
			} else if (n.type === 'finding') {
				radius = 12;
			} else if (n.type === 'claim') {
				radius = 7;
			} else {
				radius = 4;
			}
			nodes.push({ ...n, group: 0, radius });
			visibleIds.add(n.id);
		}

		// Build adjacency for hidden nodes so we can create transitive links
		// e.g. source→extract→claim becomes source→claim when extracts are hidden
		const hiddenAdj = new Map<string, Set<string>>(); // hidden node → set of visible neighbors

		for (const e of data.edges) {
			const src = typeof e.source === 'string' ? e.source : (e.source as any).id;
			const tgt = typeof e.target === 'string' ? e.target : (e.target as any).id;
			const srcHidden = !visibleIds.has(src) && allNodeTypes.has(src);
			const tgtHidden = !visibleIds.has(tgt) && allNodeTypes.has(tgt);

			if (srcHidden) {
				if (!hiddenAdj.has(src)) hiddenAdj.set(src, new Set());
				if (visibleIds.has(tgt)) hiddenAdj.get(src)!.add(tgt);
			}
			if (tgtHidden) {
				if (!hiddenAdj.has(tgt)) hiddenAdj.set(tgt, new Set());
				if (visibleIds.has(src)) hiddenAdj.get(tgt)!.add(src);
			}
		}

		let links: GLink[] = [];
		const linkSet = new Set<string>();
		for (const e of data.edges) {
			const src = typeof e.source === 'string' ? e.source : (e.source as any).id;
			const tgt = typeof e.target === 'string' ? e.target : (e.target as any).id;
			if (visibleIds.has(src) && visibleIds.has(tgt)) {
				const key = `${src}→${tgt}`;
				if (!linkSet.has(key)) {
					linkSet.add(key);
					links.push({ source: src, target: tgt, type: e.type });
				}
			}
		}

		// Add transitive links through hidden nodes
		for (const [, neighbors] of hiddenAdj) {
			const arr = [...neighbors];
			for (let i = 0; i < arr.length; i++) {
				for (let j = i + 1; j < arr.length; j++) {
					const key = `${arr[i]}→${arr[j]}`;
					const keyRev = `${arr[j]}→${arr[i]}`;
					if (!linkSet.has(key) && !linkSet.has(keyRev)) {
						linkSet.add(key);
						links.push({ source: arr[i], target: arr[j], type: 'indirect' });
					}
				}
			}
		}

		graphStats = { nodes: nodes.length, links: links.length, indirect: links.filter(l => l.type === 'indirect').length };

		const svg = d3.select(svgEl);
		svg.selectAll('*').remove();

		if (nodes.length === 0) return;

		const g = svg.append('g');

		svg.call(d3.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.1, 4])
			.on('zoom', (event) => g.attr('transform', event.transform))
		);

		const linkColor = getComputedStyle(document.documentElement).getPropertyValue('--color-border').trim() || '#E5E2DB';
		const link = g.append('g').attr('stroke', linkColor).attr('stroke-opacity', 0.5)
			.selectAll('line').data(links).join('line')
			.attr('stroke-width', (d: any) => d.type === 'indirect' ? 1 : 1.5)
			.attr('stroke-dasharray', (d: any) => d.type === 'indirect' ? '4,3' : null);

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

		const cx = width / 2, cy = height / 2;

		// Layered Y positions: source → claim/extract → finding (top to bottom)
		const layerY: Record<string, number> = {
			source: cy * 0.35,
			extract: cy,
			claim: cy,
			finding: cy * 1.65
		};

		const hasAlign = alignBy !== '';

		simulation = d3.forceSimulation(nodes)
			.force('link', d3.forceLink<GNode, GLink>(links).id(d => d.id).distance(d => {
				if (hasAlign) {
					const s = (d.source as GNode).type, t = (d.target as GNode).type;
					return (s === alignBy || t === alignBy) ? 20 : 40;
				}
				return 30;
			}))
			.force('charge', d3.forceManyBody().strength(d => hasAlign && (d as GNode).type === alignBy ? -80 : -40))
			.force('x', d3.forceX(cx).strength(d => hasAlign && (d as GNode).type === alignBy ? 0.15 : 0.02))
			.force('y', d3.forceY<GNode>(d => {
				if (hasAlign) return (d as GNode).type === alignBy ? cy : cy;
				return layerY[(d as GNode).type] ?? cy;
			}).strength(d => hasAlign ? ((d as GNode).type === alignBy ? 0.15 : 0.02) : 0.12))
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

	// Select the first source node on initial load
	$effect(() => {
		if (app.graph && !selectedNode) {
			const firstSource = app.graph.nodes.find((n: any) => n.type === 'source');
			if (firstSource) selectedNode = firstSource;
		}
	});

	$effect(() => {
		void app.graph;
		void visible;
		void alignBy;
		void filterAuthor;
		void categoryFilter;
		void app.searchQuery;
		void width;
		buildGraph();
	});
</script>

{#if app.graph}
	<div class="toolbar">
		{#each Object.entries(visible) as [type, on]}
			<div class="entity-group">
				<button class="cat-pill entity-pill" class:active={on} onclick={() => { visible = { ...visible, [type]: !on }; }}>
					<span class="entity-dot" style="background:{typeColor(type)}"></span>
					{type}s <span class="cat-count">{typeCounts.get(type) ?? 0}</span>
				</button>
				{#if on}
					<button
						class="align-btn"
						class:aligned={alignBy === type}
						title="Align graph by {type}s"
						onclick={() => { alignBy = alignBy === type ? '' : type; }}
					>
						<Icon name="conclusions" size={12} />
					</button>
				{/if}
			</div>
		{/each}

		<span class="toolbar-sep"></span>
		{#if categories.length > 0}
			<select bind:value={categoryFilter}>
				<option value="all">All categories</option>
				{#each categories as cat}
					<option value={cat}>{cat} ({categoryCounts.get(cat) ?? 0})</option>
				{/each}
			</select>
		{/if}
		<select bind:value={filterAuthor}>
			<option value="">All authors</option>
			{#each authors as a}<option value={a}>{a}</option>{/each}
		</select>
		<span class="graph-stats">{graphStats.nodes} nodes · {graphStats.links} links{graphStats.indirect > 0 ? ` (${graphStats.indirect} indirect)` : ''}</span>
	</div>

	<div class="graph-layout">
		<div class="graph-container">
			<svg bind:this={svgEl} {width} {height}></svg>
			{#if hoveredNode}
				<div class="tooltip">
					<span class="type-badge" style="background:{typeColor(hoveredNode.type)}">{hoveredNode.type}</span>
					<strong>{hoveredNode.label}</strong>
				</div>
			{/if}
		</div>

		<aside class="detail-panel">
			{#if selectedNode}
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
			{:else}
				<div class="panel-empty">
					<p class="panel-empty-text">Click a node to inspect it</p>
				</div>
			{/if}
		</aside>
	</div>
{:else}
	<div class="empty-state"><p>No graph data available.</p></div>
{/if}

<style>
	/* Use more width than default */
	:global(.content:has(.graph-layout)) {
		max-width: 80vw;
	}

	.toolbar-sep {
		width: 1px;
		height: 20px;
		background: var(--color-border-light);
		margin: 0 var(--space-1);
	}
	.entity-group {
		display: inline-flex;
		align-items: center;
		gap: 2px;
	}
	.align-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 22px;
		height: 22px;
		border: 1px solid var(--color-border-light);
		border-radius: 50%;
		background: var(--color-surface);
		color: var(--color-text-tertiary);
		cursor: pointer;
		transition: all 0.15s;
		padding: 0;
	}
	.align-btn:hover {
		border-color: var(--color-border);
		color: var(--color-text);
	}
	.align-btn.aligned {
		background: var(--color-primary);
		border-color: var(--color-primary);
		color: white;
	}
	.cat-pill {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
		padding: var(--space-1) var(--space-3);
		border-radius: var(--radius-full, 9999px);
		border: 1px solid var(--color-border-light);
		background: var(--color-surface);
		font-size: var(--font-size-sm);
		font-family: var(--font-family);
		color: var(--color-text-secondary);
		cursor: pointer;
		transition: all 0.15s;
	}
	.cat-pill:hover {
		border-color: var(--color-border);
		color: var(--color-text);
	}
	.cat-pill.active {
		background: var(--color-surface-hover);
		border-color: var(--color-border);
		color: var(--color-text);
		font-weight: var(--font-weight-medium);
	}
	.cat-count {
		font-size: var(--font-size-xs);
		opacity: 0.7;
	}
	.entity-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.entity-pill:not(.active) {
		opacity: 0.5;
	}

	.graph-stats {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		margin-left: auto;
	}

	/* Layout */
	.graph-layout {
		display: flex;
		gap: var(--space-4);
		height: calc(80vh - var(--header-height));
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
		min-height: 0;
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
		min-height: 0;
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
	.panel-empty {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100%;
	}
	.panel-empty-text {
		font-size: var(--font-size-sm);
		color: var(--color-text-tertiary);
	}
</style>
