<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import { graphData, findingsData } from '$lib/stores/data';
	import type { GraphNode, GraphLink, GraphExportData } from '$lib/types';

	let svgEl: SVGSVGElement;
	let width = $state(800);
	let height = $state(600);

	let gData = $derived($graphData);
	let findings = $derived($findingsData);

	let visible = $state<Record<string, boolean>>({
		claim: true,
		extract: false,
		source: true
	});
	let activeLayout = $state<string | null>(null);
	let filterAuthor = $state('');
	let filterSourceType = $state('');
	let filterExtractFormat = $state('');
	let filterExtractType = $state('');
	let filterSource = $state('');
	let simulation: d3.Simulation<d3.SimulationNodeDatum, undefined> | null = null;
	let allNodes: GraphNode[] = [];
	let allLinks: GraphLink[] = [];
	let tooltip: d3.Selection<HTMLDivElement, unknown, HTMLElement, any> | null = null;

	interface DetailData {
		node: GraphNode;
		connectedIds: Set<string>;
	}
	let detail = $state<DetailData | null>(null);
	let sidebarOpen = $derived(detail !== null);

	const nodeTypes = ['claim', 'extract', 'source'] as const;

	const colorMap: Record<string, string> = {
		claim: 'var(--color-canonical)',
		extract: '#9334e9',
		source: 'var(--color-warning)'
	};

	const colorHex: Record<string, string> = {
		claim: '#1a73e8',
		extract: '#9334e9',
		source: '#e37400'
	};

	let availableAuthors = $state<string[]>([]);
	let availableSourceTypes = $state<string[]>([]);
	let availableExtractFormats = $state<string[]>([]);
	let availableExtractTypes = $state<string[]>([]);
	let availableSources = $state<Array<{ id: string; label: string }>>([]);

	function buildGraph() {
		const nodes: GraphNode[] = [];
		const links: GraphLink[] = [];
		const authorSet = new Set<string>();
		const sourceTypeSet = new Set<string>();
		const extractFormatSet = new Set<string>();
		const extractTypeSet = new Set<string>();
		const sourceList: Array<{ id: string; label: string }> = [];

		if (!gData) return { nodes, links, authors: [] as string[], sourceTypes: [] as string[], extractFormats: [] as string[], extractTypes: [] as string[], sources: sourceList };

		for (const n of gData.nodes) {
			const radius = n.type === 'source' ? 8 : n.type === 'claim' ? 7 : 2;
			nodes.push({
				id: n.id,
				label: n.label,
				type: n.type as GraphNode['type'],
				group: ['source', 'extract', 'claim'].indexOf(n.type),
				radius,
				author: n.author,
				sourceType: n.sourceType,
				format: n.format,
				extractType: n.extractType,
				theme: n.theme,
			});
			if (n.author) authorSet.add(n.author);
			if (n.sourceType) sourceTypeSet.add(n.sourceType);
			if (n.format && n.type === 'extract') extractFormatSet.add(n.format);
			if (n.extractType) extractTypeSet.add(n.extractType);
			if (n.type === 'source') {
				sourceList.push({ id: n.id, label: n.label });
			}
		}

		for (const e of gData.edges) {
			links.push({ source: e.source, target: e.target, type: e.type });
		}

		sourceList.sort((a, b) => a.id.localeCompare(b.id));

		return {
			nodes, links,
			authors: [...authorSet].sort(),
			sourceTypes: [...sourceTypeSet].sort(),
			extractFormats: [...extractFormatSet].sort(),
			extractTypes: [...extractTypeSet].sort(),
			sources: sourceList,
		};
	}

	function getVisibleTypes(): Set<string> {
		return new Set(Object.entries(visible).filter(([, v]) => v).map(([k]) => k));
	}

	function filterGraph(nodes: GraphNode[], links: GraphLink[], visibleTypes: Set<string>, author: string, sType: string, eFormat: string, eType: string, sourceId: string) {
		let filteredNodes = nodes.filter((n) => visibleTypes.has(n.type));

		if (sourceId) {
			// Build forward adjacency: source→extract→claim
			const forward = new Map<string, string[]>();
			for (const l of links) {
				const src = l.source as string;
				const tgt = l.target as string;
				if (!forward.has(src)) forward.set(src, []);
				forward.get(src)!.push(tgt);
			}
			const reachable = new Set<string>([sourceId]);
			const queue = [sourceId];
			while (queue.length > 0) {
				const cur = queue.pop()!;
				for (const neighbor of forward.get(cur) ?? []) {
					if (!reachable.has(neighbor)) {
						reachable.add(neighbor);
						queue.push(neighbor);
					}
				}
			}
			filteredNodes = filteredNodes.filter((n) => reachable.has(n.id));
		}

		if (sType) {
			filteredNodes = filteredNodes.filter((n) =>
				n.type === 'claim' || n.sourceType === sType
			);
		}
		if (author) {
			filteredNodes = filteredNodes.filter((n) =>
				n.type === 'claim' || n.author === author
			);
		}
		if (eFormat) {
			filteredNodes = filteredNodes.filter((n) =>
				n.type !== 'extract' || n.format === eFormat
			);
		}
		if (eType) {
			filteredNodes = filteredNodes.filter((n) =>
				n.type !== 'extract' || n.extractType === eType
			);
		}

		// Keep only claims that have at least one visible connection
		const visibleIds = new Set(filteredNodes.map((n) => n.id));
		const claimIds = new Set(filteredNodes.filter((n) => n.type === 'claim').map((n) => n.id));
		const connectedClaimIds = new Set<string>();
		for (const l of links) {
			if (claimIds.has(l.source as string) && visibleIds.has(l.target as string)) connectedClaimIds.add(l.source as string);
			if (claimIds.has(l.target as string) && visibleIds.has(l.source as string)) connectedClaimIds.add(l.target as string);
		}
		filteredNodes = filteredNodes.filter((n) => n.type !== 'claim' || connectedClaimIds.has(n.id));

		const finalIds = new Set(filteredNodes.map((n) => n.id));
		const filteredLinks = links.filter(
			(l) => finalIds.has(l.source as string) && finalIds.has(l.target as string)
		);
		return { nodes: filteredNodes, links: filteredLinks };
	}

	function getConnectedIds(startId: string, links: GraphLink[]): Set<string> {
		const connected = new Set<string>([startId]);
		for (const l of links) {
			const src = typeof l.source === 'object' ? (l.source as any).id : l.source;
			const tgt = typeof l.target === 'object' ? (l.target as any).id : l.target;
			if (src === startId) connected.add(tgt);
			if (tgt === startId) connected.add(src);
		}
		return connected;
	}

	function closeSidebar() {
		detail = null;
	}

	let nodeSelection: d3.Selection<SVGCircleElement, GraphNode, SVGGElement, unknown> | null = null;
	let linkSelection: d3.Selection<SVGLineElement, GraphLink, SVGGElement, unknown> | null = null;

	function renderGraph() {
		if (!svgEl) return;

		const built = buildGraph();
		if (built.nodes.length === 0) return;

		allNodes = built.nodes;
		allLinks = built.links;
		availableAuthors = built.authors;
		availableSourceTypes = built.sourceTypes;
		availableExtractFormats = built.extractFormats;
		availableExtractTypes = built.extractTypes;
		availableSources = built.sources;

		const visibleTypes = getVisibleTypes();
		const { nodes, links } = filterGraph(built.nodes, built.links, visibleTypes, filterAuthor, filterSourceType, filterExtractFormat, filterExtractType, filterSource);

		const svg = d3.select(svgEl);
		svg.selectAll('*').remove();

		if (nodes.length === 0) return;

		const container = svg.append('g');

		const zoom = d3.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.1, 4])
			.on('zoom', (event) => container.attr('transform', event.transform));
		svg.call(zoom);

		const chargeStrength = nodes.length > 2000 ? -30 : nodes.length > 500 ? -50 : -80;
		const linkDist = nodes.length > 2000 ? 20 : 40;

		simulation = d3.forceSimulation(nodes as d3.SimulationNodeDatum[])
			.force('link', d3.forceLink(links).id((d: any) => d.id).distance(linkDist))
			.force('charge', d3.forceManyBody().strength(chargeStrength))
			.force('center', d3.forceCenter(width / 2, height / 2))
			.force('collision', d3.forceCollide().radius((d: any) => d.radius + 1));

		linkSelection = container.append('g')
			.selectAll('line')
			.data(links)
			.join('line')
			.attr('stroke', 'var(--color-border)')
			.attr('stroke-opacity', 0.2)
			.attr('stroke-width', 0.5);

		nodeSelection = container.append('g')
			.selectAll('circle')
			.data(nodes)
			.join('circle')
			.attr('r', (d) => d.radius)
			.attr('fill', (d) => colorMap[d.type] ?? '#999')
			.attr('stroke', 'white')
			.attr('stroke-width', (d) => d.type === 'extract' ? 0.5 : 1.5)
			.style('cursor', 'pointer')
			.call(d3.drag<SVGCircleElement, GraphNode>()
				.on('start', (event, d: any) => {
					if (!event.active) simulation!.alphaTarget(0.3).restart();
					d.fx = d.x; d.fy = d.y;
				})
				.on('drag', (event, d: any) => { d.fx = event.x; d.fy = event.y; })
				.on('end', (event, d: any) => {
					if (!event.active) simulation!.alphaTarget(0);
					d.fx = null; d.fy = null;
				})
			);

		if (tooltip) tooltip.remove();
		tooltip = d3.select('body').append('div')
			.attr('class', 'graph-tooltip')
			.style('position', 'absolute')
			.style('max-width', '360px')
			.style('padding', '6px 10px')
			.style('background', 'var(--color-text)')
			.style('color', 'white')
			.style('border-radius', '4px')
			.style('font-size', '12px')
			.style('line-height', '1.4')
			.style('pointer-events', 'none')
			.style('opacity', '0')
			.style('z-index', '200');

		function applyHighlight(connectedIds: Set<string>) {
			nodeSelection!.transition().duration(200)
				.attr('opacity', (d: any) => connectedIds.has(d.id) ? 1 : 0.08);
			linkSelection!.transition().duration(200)
				.attr('stroke-opacity', (d: any) => {
					const srcId = typeof d.source === 'object' ? d.source.id : d.source;
					const tgtId = typeof d.target === 'object' ? d.target.id : d.target;
					return connectedIds.has(srcId) && connectedIds.has(tgtId) ? 0.6 : 0.03;
				});
		}

		function resetHighlight() {
			detail = null;
			nodeSelection!.transition().duration(200).attr('opacity', 1);
			linkSelection!.transition().duration(200).attr('stroke-opacity', 0.2);
		}

		svg.on('click', (event) => {
			if (event.target === svgEl) resetHighlight();
		});

		nodeSelection.on('click', (event, d) => {
			event.stopPropagation();
			const connectedIds = getConnectedIds(d.id, links);
			applyHighlight(connectedIds);
			detail = { node: d, connectedIds };
		});

		nodeSelection.on('mouseover', (event, d) => {
			const extra = d.extractType ? `<br/><em>${d.extractType}</em>` : d.author ? `<br/><em>${d.author}</em>` : '';
			tooltip!.transition().duration(100).style('opacity', '1');
			tooltip!.html(`<strong>${d.type}</strong>${extra}<br/>${d.label}`)
				.style('left', event.pageX + 12 + 'px')
				.style('top', event.pageY - 12 + 'px');
		}).on('mouseout', () => {
			tooltip!.transition().duration(200).style('opacity', '0');
		});

		simulation.on('tick', () => {
			linkSelection!
				.attr('x1', (d: any) => d.source.x).attr('y1', (d: any) => d.source.y)
				.attr('x2', (d: any) => d.target.x).attr('y2', (d: any) => d.target.y);
			nodeSelection!
				.attr('cx', (d: any) => d.x).attr('cy', (d: any) => d.y);
		});

		if (activeLayout && visible[activeLayout]) {
			applyLayout(activeLayout);
		}
	}

	function applyLayout(type: string | null) {
		if (!simulation) return;
		activeLayout = type;
		const visibleTypes = nodeTypes.filter((t) => visible[t]);

		if (!type) {
			simulation.force('y', null);
			simulation.force('x', null);
			simulation.force('center', d3.forceCenter(width / 2, height / 2));
		} else {
			const order = [type, ...visibleTypes.filter((t) => t !== type)];
			const bandHeight = height / (order.length + 1);
			simulation.force('center', null);
			simulation.force('y', d3.forceY<d3.SimulationNodeDatum>()
				.y((d: any) => bandHeight * (order.indexOf(d.type) + 1))
				.strength(0.8)
			);
			simulation.force('x', d3.forceX(width / 2).strength(0.05));
		}
		simulation.alpha(0.6).restart();
	}

	function toggleVisibility(type: string) {
		visible[type] = !visible[type];
		renderGraph();
	}

	function onLayoutClick(type: string) {
		if (!visible[type]) return;
		applyLayout(activeLayout === type ? null : type);
	}

	function onFilterChange() {
		// Auto-enable extracts when filtering to a specific source
		if (filterSource && !visible.extract) {
			visible.extract = true;
		}
		renderGraph();
	}

	function nodeCounts(): Record<string, number> {
		const counts: Record<string, number> = { claim: 0, extract: 0, source: 0 };
		for (const n of allNodes) counts[n.type] = (counts[n.type] || 0) + 1;
		return counts;
	}

	// Resolve detail info from the graph data
	let detailNeighbors = $derived.by(() => {
		if (!detail || !gData) return { claims: [], extracts: [], sources: [] };
		const ids = detail.connectedIds;
		const nodeMap = new Map(gData.nodes.map((n) => [n.id, n]));
		const claims: typeof gData.nodes = [];
		const extracts: typeof gData.nodes = [];
		const sources: typeof gData.nodes = [];
		for (const id of ids) {
			if (id === detail.node.id) continue;
			const n = nodeMap.get(id);
			if (!n) continue;
			if (n.type === 'claim') claims.push(n);
			else if (n.type === 'extract') extracts.push(n);
			else if (n.type === 'source') sources.push(n);
		}
		return { claims, extracts, sources };
	});

	let detailFullText = $derived.by(() => {
		if (!detail || !gData) return '';
		const n = gData.nodes.find((n) => n.id === detail!.node.id);
		return n?.text || detail.node.label;
	});

	onMount(() => {
		const resizeObserver = new ResizeObserver((entries) => {
			for (const entry of entries) {
				width = entry.contentRect.width;
				height = Math.max(400, window.innerHeight - 250);
			}
		});

		if (svgEl?.parentElement) {
			resizeObserver.observe(svgEl.parentElement);
		}

		return () => {
			resizeObserver.disconnect();
			tooltip?.remove();
			simulation?.stop();
			simulation = null;
		};
	});

	$effect(() => {
		if (gData) renderGraph();
	});
</script>

<div class="graph-wrapper" class:sidebar-open={sidebarOpen}>
	<div class="graph-container">
		{#if gData && gData.nodes.length > 0}
			<div class="graph-toolbar">
				<div class="graph-legend">
					{#each nodeTypes as type}
						{@const counts = nodeCounts()}
						<div
							class="legend-item"
							class:legend-active={activeLayout === type}
							class:legend-hidden={!visible[type]}
						>
							<span
								class="legend-label"
								role="button"
								tabindex="0"
								onclick={() => onLayoutClick(type)}
								onkeydown={(e: KeyboardEvent) => { if (e.key === 'Enter') onLayoutClick(type); }}
							>
								<span
									class="legend-dot"
									class:legend-dot-hidden={!visible[type]}
									style="background: {colorHex[type]}"
								></span>
								{type}
								<span class="legend-count">{counts[type]}</span>
							</span>
							<button
								class="legend-toggle"
								title="{visible[type] ? 'Hide' : 'Show'} {type}s"
								onclick={() => toggleVisibility(type)}
							>
								{visible[type] ? '✕' : '+'}
							</button>
						</div>
					{/each}
				</div>
				<div class="graph-filters">
					<select class="filter-select" bind:value={filterSourceType} onchange={onFilterChange}>
						<option value="">All types</option>
						{#each availableSourceTypes as st}
							<option value={st}>{st}</option>
						{/each}
					</select>
					<select class="filter-select" bind:value={filterAuthor} onchange={onFilterChange}>
						<option value="">All authors</option>
						{#each availableAuthors as author}
							<option value={author}>{author}</option>
						{/each}
					</select>
					<select class="filter-select filter-source" bind:value={filterSource} onchange={onFilterChange}>
						<option value="">All sources</option>
						{#each availableSources as src}
							<option value={src.id}>{src.id.split(':').pop()} — {src.label}</option>
						{/each}
					</select>
					{#if visible.extract}
						<select class="filter-select" bind:value={filterExtractFormat} onchange={onFilterChange}>
							<option value="">All formats</option>
							{#each availableExtractFormats as fmt}
								<option value={fmt}>{fmt}</option>
							{/each}
						</select>
						<select class="filter-select" bind:value={filterExtractType} onchange={onFilterChange}>
							<option value="">All extract types</option>
							{#each availableExtractTypes as et}
								<option value={et}>{et}</option>
							{/each}
						</select>
					{/if}
				</div>
			</div>
			<svg bind:this={svgEl} {width} {height}></svg>
		{:else if findings && findings.findings.length > 0}
			<div class="empty-state">
				<p>Graph data not available. Export graph.json to enable this view.</p>
			</div>
		{:else}
			<div class="empty-state">
				<p>No graph data available. Run analysis to generate findings and claims.</p>
			</div>
		{/if}
	</div>

	{#if detail}
		<aside class="detail-sidebar">
			<div class="sidebar-header">
				<span class="sidebar-type-badge" style="background: {colorHex[detail.node.type]}">
					{detail.node.type}
				</span>
				<button class="sidebar-close" onclick={closeSidebar}>✕</button>
			</div>

			<div class="sidebar-body">
				<h3 class="sidebar-title">{detail.node.id.split(':').pop()}</h3>
				<p class="sidebar-text">{detailFullText}</p>

				{#if detail.node.author}
					<p class="sidebar-meta">Author: {detail.node.author}</p>
				{/if}
				{#if detail.node.format}
					<p class="sidebar-meta">Format: {detail.node.format}</p>
				{/if}
				{#if detail.node.extractType}
					<p class="sidebar-meta">Type: {detail.node.extractType}</p>
				{/if}
				{#if detail.node.theme}
					<p class="sidebar-meta">Theme: {detail.node.theme}</p>
				{/if}

				{#if detailNeighbors.claims.length > 0}
					<div class="sidebar-section">
						<h4 class="sidebar-section-title">
							<span class="legend-dot" style="background: {colorHex.claim}"></span>
							Claims ({detailNeighbors.claims.length})
						</h4>
						{#each detailNeighbors.claims as c}
							<div class="sidebar-item">
								<span class="sidebar-item-id">{c.id.split(':').pop()}</span>
								{c.text || c.label}
							</div>
						{/each}
					</div>
				{/if}

				{#if detailNeighbors.extracts.length > 0}
					<div class="sidebar-section">
						<h4 class="sidebar-section-title">
							<span class="legend-dot" style="background: {colorHex.extract}"></span>
							Extracts ({detailNeighbors.extracts.length})
						</h4>
						{#each detailNeighbors.extracts.slice(0, 10) as e}
							<div class="sidebar-item">
								{#if e.extractType}<span class="extract-type-tag">{e.extractType}</span>{/if}
								{e.text || e.label}
							</div>
						{/each}
						{#if detailNeighbors.extracts.length > 10}
							<div class="sidebar-item sidebar-meta">...and {detailNeighbors.extracts.length - 10} more</div>
						{/if}
					</div>
				{/if}

				{#if detailNeighbors.sources.length > 0}
					<div class="sidebar-section">
						<h4 class="sidebar-section-title">
							<span class="legend-dot" style="background: {colorHex.source}"></span>
							Sources ({detailNeighbors.sources.length})
						</h4>
						{#each detailNeighbors.sources as s}
							<div class="sidebar-item">
								<strong>{s.label}</strong>
								{#if s.author}<span class="text-secondary"> — {s.author}</span>{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</aside>
	{/if}
</div>

<style>
	.graph-wrapper {
		display: flex;
		width: 100%;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		overflow: hidden;
		background: var(--color-bg);
		transition: all 0.2s;
	}

	.graph-container {
		flex: 1;
		min-width: 0;
	}

	svg {
		display: block;
		width: 100%;
	}

	.detail-sidebar {
		width: 360px;
		flex-shrink: 0;
		border-left: 1px solid var(--color-border);
		background: var(--color-bg);
		overflow-y: auto;
		max-height: calc(100vh - 200px);
	}

	.sidebar-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--space-3) var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
		position: sticky;
		top: 0;
		background: var(--color-bg);
		z-index: 1;
	}

	.sidebar-type-badge {
		display: inline-block;
		padding: 2px 8px;
		border-radius: var(--radius-full);
		color: white;
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		text-transform: capitalize;
	}

	.sidebar-close {
		background: none;
		border: none;
		font-size: var(--font-size-lg);
		color: var(--color-text-tertiary);
		cursor: pointer;
		padding: var(--space-1);
		line-height: 1;
	}

	.sidebar-close:hover {
		color: var(--color-text);
	}

	.sidebar-body {
		padding: var(--space-4);
	}

	.sidebar-title {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		line-height: var(--line-height-normal);
		margin-bottom: var(--space-2);
	}

	.sidebar-text {
		font-size: var(--font-size-sm);
		line-height: var(--line-height-relaxed);
		margin-bottom: var(--space-3);
	}

	.sidebar-meta {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		margin-bottom: var(--space-1);
	}

	.sidebar-section {
		margin-top: var(--space-5);
		padding-top: var(--space-4);
		border-top: 1px solid var(--color-border-light);
	}

	.sidebar-section-title {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: var(--space-3);
	}

	.sidebar-item {
		font-size: var(--font-size-sm);
		line-height: var(--line-height-relaxed);
		padding: var(--space-2) 0;
		border-bottom: 1px solid var(--color-border-light);
	}

	.sidebar-item:last-child {
		border-bottom: none;
	}

	.sidebar-item-id {
		font-family: var(--font-mono);
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		margin-right: var(--space-2);
	}

	.extract-type-tag {
		display: inline-block;
		font-size: 10px;
		padding: 1px 5px;
		border-radius: var(--radius-full);
		background: #f3e8ff;
		color: #7c3aed;
		margin-right: var(--space-1);
	}

	/* Toolbar */
	.graph-toolbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: var(--space-3);
		padding: var(--space-3) var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
	}

	.graph-legend {
		display: flex;
		gap: var(--space-2);
		font-size: var(--font-size-xs);
		color: var(--color-text-secondary);
	}

	.graph-filters {
		display: flex;
		gap: var(--space-2);
		flex-wrap: wrap;
	}

	.filter-select {
		font-family: var(--font-family);
		font-size: var(--font-size-xs);
		padding: var(--space-1) var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-bg);
		color: var(--color-text-secondary);
		outline: none;
		max-width: 200px;
	}

	.filter-select:focus {
		border-color: var(--color-primary);
	}

	.filter-source {
		max-width: 300px;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: var(--space-1);
		background: none;
		border: 1px solid var(--color-border-light);
		font-family: var(--font-family);
		font-size: var(--font-size-xs);
		color: var(--color-text-secondary);
		padding: var(--space-1) var(--space-2);
		border-radius: var(--radius-sm);
		transition: background 0.15s, opacity 0.15s;
	}

	.legend-label {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		cursor: pointer;
	}

	.legend-label:hover {
		color: var(--color-text);
	}

	.legend-active {
		background: var(--color-primary-light);
		color: var(--color-primary);
		border-color: var(--color-primary);
	}

	.legend-hidden {
		opacity: 0.5;
	}

	.legend-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.legend-dot-hidden {
		opacity: 0.3;
	}

	.legend-count {
		color: var(--color-text-tertiary);
		font-size: 10px;
	}

	.legend-toggle {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 16px;
		height: 16px;
		font-size: 10px;
		background: none;
		border: none;
		color: var(--color-text-tertiary);
		cursor: pointer;
		border-radius: 50%;
		padding: 0;
		line-height: 1;
	}

	.legend-toggle:hover {
		background: var(--color-border-light);
		color: var(--color-text);
	}

	.text-secondary {
		color: var(--color-text-secondary);
	}
</style>
