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
	let searchNode = $state('');
	let hoveredNode = $state<any>(null);
	let selectedNode = $state<any>(null);

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
			case 'finding': return '#D97757';
			case 'claim': return '#3D8B37';
			case 'extract': return '#9B9A95';
			case 'source': return '#C4841D';
			default: return '#64635E';
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

		const node = g.append('g')
			.selectAll('circle').data(nodes).join('circle')
			.attr('r', d => d.radius)
			.attr('fill', d => typeColor(d.type))
			.attr('stroke', '#fff').attr('stroke-width', 1.5)
			.style('cursor', 'pointer')
			.on('mouseenter', (_, d) => { hoveredNode = d; })
			.on('mouseleave', () => { hoveredNode = null; })
			.on('click', (_, d) => { selectedNode = selectedNode?.id === d.id ? null : d; })
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
		<div class="search-field">
			<Icon name="search" size={14} />
			<input type="text" placeholder="Search nodes..." bind:value={searchNode} />
		</div>
	</div>

	<div class="graph-layout">
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
			<div class="detail-panel">
				<div class="detail-header">
					<span class="type-badge" style="background:{typeColor(selectedNode.type)}">{selectedNode.type}</span>
					<button class="close-btn" onclick={() => { selectedNode = null; }}>
						<Icon name="x" size={16} />
					</button>
				</div>
				<h3 class="detail-title">{selectedNode.label}</h3>
				{#if selectedNode.text && selectedNode.text !== selectedNode.label}
					<p class="detail-text">{selectedNode.text}</p>
				{/if}
				<dl class="detail-fields">
					{#if selectedNode.id}<dt>ID</dt><dd>{selectedNode.id}</dd>{/if}
					{#if selectedNode.author}<dt>Author</dt><dd>{selectedNode.author}</dd>{/if}
					{#if selectedNode.category}<dt>Category</dt><dd>{selectedNode.category}</dd>{/if}
					{#if selectedNode.theme}<dt>Theme</dt><dd>{selectedNode.theme}</dd>{/if}
				</dl>
			</div>
		{/if}
	</div>
{:else}
	<div class="empty-state"><p>No graph data available.</p></div>
{/if}

<style>
	.controls {
		display: flex;
		gap: var(--space-4);
		align-items: center;
		flex-wrap: wrap;
		margin-bottom: var(--space-4);
	}
	.toggles { display: flex; gap: var(--space-4); }
	.toggle { display: flex; align-items: center; gap: var(--space-1); font-size: var(--font-size-sm); cursor: pointer; color: var(--color-text-secondary); }
	.toggle input { accent-color: var(--color-primary); }
	.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
	.search-field {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-1) var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-surface);
		color: var(--color-text-tertiary);
	}
	.search-field input {
		border: none;
		background: none;
		outline: none;
		font-size: var(--font-size-sm);
		font-family: var(--font-family);
		width: 140px;
		color: var(--color-text);
	}

	.graph-layout { display: flex; gap: var(--space-4); }
	.graph-container {
		flex: 1;
		position: relative;
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		overflow: hidden;
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

	.detail-panel {
		width: 300px;
		flex-shrink: 0;
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		padding: var(--space-4);
		align-self: flex-start;
	}
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-3);
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
	.detail-title {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		margin-bottom: var(--space-3);
		line-height: var(--line-height-tight);
	}
	.detail-text {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		margin-bottom: var(--space-4);
		line-height: var(--line-height-normal);
	}
	.detail-fields { font-size: var(--font-size-sm); }
	.detail-fields dt {
		font-weight: var(--font-weight-medium);
		color: var(--color-text-tertiary);
		font-size: var(--font-size-xs);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-top: var(--space-2);
	}
	.detail-fields dd {
		color: var(--color-text-secondary);
		margin: var(--space-1) 0 0 0;
		word-break: break-word;
	}
</style>
