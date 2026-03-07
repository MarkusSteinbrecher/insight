<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import { app } from '$lib/data.svelte';

	let svgEl: SVGSVGElement;
	let width = $state(900);
	let height = $state(600);

	let visible = $state<Record<string, boolean>>({ finding: true, claim: true, extract: false, source: true });
	let filterAuthor = $state('');
	let searchNode = $state('');
	let hoveredNode = $state<any>(null);

	interface GNode extends d3.SimulationNodeDatum {
		id: string; label: string; type: string; group: number; radius: number;
		author?: string; category?: string; theme?: string; text?: string;
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

	function typeColor(type: string): string {
		switch (type) {
			case 'finding': return '#2563eb';
			case 'claim': return '#059669';
			case 'extract': return '#9ca3af';
			case 'source': return '#d97706';
			default: return '#6b7280';
		}
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
			if (searchNode && !n.label.toLowerCase().includes(searchNode.toLowerCase())) continue;
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

		// Cap nodes for performance
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

		// Clear
		const svg = d3.select(svgEl);
		svg.selectAll('*').remove();

		if (nodes.length === 0) return;

		const g = svg.append('g');

		// Zoom
		svg.call(d3.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.1, 4])
			.on('zoom', (event) => g.attr('transform', event.transform))
		);

		const link = g.append('g').attr('stroke', '#e5e7eb').attr('stroke-opacity', 0.6)
			.selectAll('line').data(links).join('line').attr('stroke-width', 1);

		const node = g.append('g')
			.selectAll('circle').data(nodes).join('circle')
			.attr('r', d => d.radius)
			.attr('fill', d => typeColor(d.type))
			.attr('stroke', '#fff').attr('stroke-width', 1)
			.style('cursor', 'pointer')
			.on('mouseenter', (_, d) => { hoveredNode = d; })
			.on('mouseleave', () => { hoveredNode = null; })
			.call(d3.drag<SVGCircleElement, GNode>()
				.on('start', (event, d) => { if (!event.active) simulation?.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
				.on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
				.on('end', (event, d) => { if (!event.active) simulation?.alphaTarget(0); d.fx = null; d.fy = null; })
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
		// Track dependencies
		void app.graph;
		void visible;
		void filterAuthor;
		void searchNode;
		void width;
		buildGraph();
	});
</script>

{#if app.graph}
	<div class="controls">
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
		<input type="text" placeholder="Search nodes..." bind:value={searchNode} class="node-search" />
	</div>

	<div class="graph-container">
		<svg bind:this={svgEl} {width} {height}></svg>
		{#if hoveredNode}
			<div class="tooltip">
				<span class="badge" style="background:{typeColor(hoveredNode.type)}; color:white">{hoveredNode.type}</span>
				<strong>{hoveredNode.label}</strong>
				{#if hoveredNode.text && hoveredNode.text !== hoveredNode.label}
					<p>{hoveredNode.text.slice(0, 200)}</p>
				{/if}
			</div>
		{/if}
	</div>
{:else}
	<div class="empty-state"><p>No graph data available. Run the exporter to generate graph.json.</p></div>
{/if}

<style>
	.controls { display: flex; gap: var(--space-4); align-items: center; flex-wrap: wrap; margin-bottom: var(--space-4); }
	.toggles { display: flex; gap: var(--space-4); }
	.toggle { display: flex; align-items: center; gap: var(--space-1); font-size: var(--font-size-sm); cursor: pointer; }
	.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
	.controls select, .node-search { font-family: var(--font-family); font-size: var(--font-size-sm); padding: var(--space-1) var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-sm); }
	.node-search { max-width: 200px; }
	.graph-container { position: relative; border: 1px solid var(--color-border); border-radius: var(--radius-md); overflow: hidden; background: #fafafa; }
	svg { display: block; width: 100%; min-height: 500px; }
	.tooltip { position: absolute; top: var(--space-4); right: var(--space-4); max-width: 300px; background: white; border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: var(--space-3) var(--space-4); font-size: var(--font-size-sm); box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
	.tooltip strong { display: block; margin-top: var(--space-1); }
	.tooltip p { margin-top: var(--space-1); color: var(--color-text-secondary); font-size: var(--font-size-xs); }
</style>
