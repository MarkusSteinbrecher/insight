<script lang="ts">
	import { app } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';

	function goTo(tab: string) {
		app.activeTab = tab;
	}
</script>

<div class="about">
	<section class="hero">
		<h2 class="hero-title">What is Insight?</h2>
		<p class="hero-text">
			Insight is a research analysis tool that helps consultants build defensible, sourced positions on complex topics.
			It collects sources from across the web, aligns claims across them, and surfaces findings and contradictions —
			all traceable back to the original source material.
		</p>
	</section>

	<section class="pipeline-section">
		<h3 class="section-title">The Traceability Chain</h3>
		<p class="section-desc">Every insight traces back to a specific location in a specific source. Nothing is asserted without evidence.</p>

		<div class="pipeline-svg-wrap">
			<svg class="pipeline-svg" viewBox="0 0 900 320" fill="none" xmlns="http://www.w3.org/2000/svg">
				<!-- Connecting lines (drawn first so they appear behind nodes) -->
				<path class="flow-line line-1" d="M 170 100 C 230 100, 230 100, 280 100" stroke="var(--color-border)" stroke-width="2" stroke-dasharray="6 4" />
				<path class="flow-line line-2" d="M 370 100 C 430 100, 430 100, 460 100" stroke="var(--color-border)" stroke-width="2" stroke-dasharray="6 4" />
				<path class="flow-line line-3" d="M 550 100 C 610 100, 610 100, 640 100" stroke="var(--color-border)" stroke-width="2" stroke-dasharray="6 4" />
				<path class="flow-line line-4" d="M 730 100 C 790 100, 790 100, 810 100" stroke="var(--color-border)" stroke-width="2" stroke-dasharray="6 4" />

				<!-- Animated particles along the lines -->
				<circle class="particle p-1" r="3" fill="var(--color-source)">
					<animateMotion dur="2.5s" repeatCount="indefinite" begin="0s" keyPoints="0;1" keyTimes="0;1" calcMode="spline" keySplines="0.4 0 0.2 1">
						<mpath href="#path-1" />
					</animateMotion>
				</circle>
				<circle class="particle p-2" r="3" fill="var(--color-extract)">
					<animateMotion dur="2.5s" repeatCount="indefinite" begin="0.6s" keyPoints="0;1" keyTimes="0;1" calcMode="spline" keySplines="0.4 0 0.2 1">
						<mpath href="#path-2" />
					</animateMotion>
				</circle>
				<circle class="particle p-3" r="3" fill="var(--color-claim)">
					<animateMotion dur="2.5s" repeatCount="indefinite" begin="1.2s" keyPoints="0;1" keyTimes="0;1" calcMode="spline" keySplines="0.4 0 0.2 1">
						<mpath href="#path-3" />
					</animateMotion>
				</circle>
				<circle class="particle p-4" r="3" fill="var(--color-finding)">
					<animateMotion dur="2.5s" repeatCount="indefinite" begin="1.8s" keyPoints="0;1" keyTimes="0;1" calcMode="spline" keySplines="0.4 0 0.2 1">
						<mpath href="#path-4" />
					</animateMotion>
				</circle>

				<!-- Hidden paths for animateMotion -->
				<path id="path-1" d="M 170 100 C 230 100, 230 100, 280 100" fill="none" />
				<path id="path-2" d="M 370 100 C 430 100, 430 100, 460 100" fill="none" />
				<path id="path-3" d="M 550 100 C 610 100, 610 100, 640 100" fill="none" />
				<path id="path-4" d="M 730 100 C 790 100, 790 100, 810 100" fill="none" />

				<!-- Arrow heads -->
				<polygon class="arrow arrow-1" points="278,94 290,100 278,106" fill="var(--color-border)" />
				<polygon class="arrow arrow-2" points="458,94 470,100 458,106" fill="var(--color-border)" />
				<polygon class="arrow arrow-3" points="638,94 650,100 638,106" fill="var(--color-border)" />
				<polygon class="arrow arrow-4" points="808,94 820,100 808,106" fill="var(--color-border)" />

				<!-- Node 1: Source -->
				<g class="node node-source">
					<rect x="30" y="60" width="140" height="80" rx="12" fill="var(--color-source-bg)" stroke="var(--color-source)" stroke-width="2" />
					<text x="100" y="92" text-anchor="middle" fill="var(--color-source)" font-size="13" font-weight="600">SOURCES</text>
					<text x="100" y="112" text-anchor="middle" fill="var(--color-text-secondary)" font-size="11">Web, PDF, Video</text>
					<text x="100" y="128" text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10">Collected material</text>
				</g>

				<!-- Node 2: Extract -->
				<g class="node node-extract">
					<rect x="290" y="60" width="140" height="80" rx="12" fill="var(--color-extract-bg)" stroke="var(--color-extract)" stroke-width="2" />
					<text x="360" y="92" text-anchor="middle" fill="var(--color-extract)" font-size="13" font-weight="600">EXTRACTS</text>
					<text x="360" y="112" text-anchor="middle" fill="var(--color-text-secondary)" font-size="11">Atomic statements</text>
					<text x="360" y="128" text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10">Facts, stats, evidence</text>
				</g>

				<!-- Node 3: Claim -->
				<g class="node node-claim">
					<rect x="470" y="60" width="140" height="80" rx="12" fill="var(--color-claim-bg)" stroke="var(--color-claim)" stroke-width="2" />
					<text x="540" y="92" text-anchor="middle" fill="var(--color-claim)" font-size="13" font-weight="600">CLAIMS</text>
					<text x="540" y="112" text-anchor="middle" fill="var(--color-text-secondary)" font-size="11">Cross-source positions</text>
					<text x="540" y="128" text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10">Aligned & validated</text>
				</g>

				<!-- Node 4: Finding -->
				<g class="node node-finding">
					<rect x="650" y="60" width="140" height="80" rx="12" fill="var(--color-finding-bg)" stroke="var(--color-finding)" stroke-width="2" />
					<text x="720" y="92" text-anchor="middle" fill="var(--color-finding)" font-size="13" font-weight="600">FINDINGS</text>
					<text x="720" y="112" text-anchor="middle" fill="var(--color-text-secondary)" font-size="11">Thematic patterns</text>
					<text x="720" y="128" text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10">Emergent insights</text>
				</g>

				<!-- Node 5: Recommendation (below finding, centered) -->
				<path class="flow-line line-5" d="M 720 140 C 720 170, 720 170, 720 190" stroke="var(--color-border)" stroke-width="2" stroke-dasharray="6 4" />
				<polygon class="arrow arrow-5" points="714,188 720,200 726,188" fill="var(--color-border)" />
				<circle class="particle p-5" r="3" fill="var(--color-primary)">
					<animateMotion dur="2.5s" repeatCount="indefinite" begin="2.4s" keyPoints="0;1" keyTimes="0;1" calcMode="spline" keySplines="0.4 0 0.2 1">
						<mpath href="#path-5" />
					</animateMotion>
				</circle>
				<path id="path-5" d="M 720 140 C 720 170, 720 170, 720 190" fill="none" />

				<g class="node node-recommendation">
					<rect x="640" y="200" width="160" height="80" rx="12" fill="var(--color-primary-light)" stroke="var(--color-primary)" stroke-width="2" />
					<text x="720" y="232" text-anchor="middle" fill="var(--color-primary-text)" font-size="13" font-weight="600">RECOMMENDATIONS</text>
					<text x="720" y="252" text-anchor="middle" fill="var(--color-text-secondary)" font-size="11">Actionable conclusions</text>
					<text x="720" y="268" text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10">Evidence-backed</text>
				</g>

				<!-- Multiplicity indicators -->
				<text x="100" y="50" text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10" class="multiplicity">many</text>
				<text x="360" y="50" text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10" class="multiplicity">many per source</text>
				<text x="540" y="50" text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10" class="multiplicity">cross-source</text>
				<text x="720" y="50" text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10" class="multiplicity">grouped</text>
			</svg>
		</div>
	</section>

	<section class="pages-section">
		<h3 class="section-title">Explore the Dashboard</h3>
		<div class="page-grid">
			<button class="page-card" onclick={() => goTo('dashboard')}>
				<div class="page-icon"><Icon name="dashboard" size={24} /></div>
				<h4 class="page-name">Dashboard</h4>
				<p class="page-desc">Overview stats, source breakdown, pipeline progress, and top contributing sources.</p>
			</button>
			<button class="page-card" onclick={() => goTo('sources')}>
				<div class="page-icon"><Icon name="sources" size={24} /></div>
				<h4 class="page-name">Sources</h4>
				<p class="page-desc">Sortable table of all collected sources with quality indicators, status tracking, and type filtering.</p>
			</button>
			<button class="page-card" onclick={() => goTo('findings')}>
				<div class="page-icon"><Icon name="findings" size={24} /></div>
				<h4 class="page-name">Findings</h4>
				<p class="page-desc">Expandable findings with linked claims, source quotes, and category grouping.</p>
			</button>
			<button class="page-card" onclick={() => goTo('graph')}>
				<div class="page-icon"><Icon name="graph" size={24} /></div>
				<h4 class="page-name">Graph</h4>
				<p class="page-desc">Force-directed knowledge graph showing the connections between sources, claims, and findings.</p>
			</button>
			<button class="page-card" onclick={() => goTo('conclusions')}>
				<div class="page-icon"><Icon name="conclusions" size={24} /></div>
				<h4 class="page-name">Conclusions</h4>
				<p class="page-desc">Recommendations and thought leadership angles backed by the full evidence chain.</p>
			</button>
		</div>
	</section>

	<section class="built-section">
		<h3 class="section-title">Built With</h3>
		<div class="tech-row">
			<span class="tech-badge">SvelteKit</span>
			<span class="tech-badge">Svelte 5</span>
			<span class="tech-badge">D3.js</span>
			<span class="tech-badge">KuzuDB</span>
		</div>
	</section>
</div>

<style>
	.about {
		display: flex;
		flex-direction: column;
		gap: var(--space-10);
	}

	/* Hero */
	.hero {
		text-align: center;
		max-width: 640px;
		margin: 0 auto;
		padding: var(--space-6) 0;
	}
	.hero-title {
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text);
		margin-bottom: var(--space-4);
		letter-spacing: -0.02em;
	}
	.hero-text {
		font-size: var(--font-size-base);
		color: var(--color-text-secondary);
		line-height: var(--line-height-relaxed);
	}

	/* Sections */
	.section-title {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text);
		margin-bottom: var(--space-2);
	}
	.section-desc {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		margin-bottom: var(--space-6);
	}

	/* Pipeline SVG */
	.pipeline-section {
		text-align: center;
	}
	.pipeline-svg-wrap {
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		padding: var(--space-6) var(--space-4);
		overflow-x: auto;
	}
	.pipeline-svg {
		width: 100%;
		max-width: 900px;
		height: auto;
		margin: 0 auto;
		display: block;
		font-family: var(--font-family);
	}

	/* Node entrance animations */
	.node {
		opacity: 0;
		animation: nodeIn 0.5s ease-out forwards;
	}
	.node-source { animation-delay: 0.1s; }
	.node-extract { animation-delay: 0.3s; }
	.node-claim { animation-delay: 0.5s; }
	.node-finding { animation-delay: 0.7s; }
	.node-recommendation { animation-delay: 0.9s; }

	@keyframes nodeIn {
		from { opacity: 0; transform: translateY(8px); }
		to { opacity: 1; transform: translateY(0); }
	}

	/* Line draw-in animation */
	.flow-line {
		stroke-dashoffset: 120;
		animation: drawLine 0.8s ease-out forwards;
	}
	.line-1 { animation-delay: 0.2s; }
	.line-2 { animation-delay: 0.4s; }
	.line-3 { animation-delay: 0.6s; }
	.line-4 { animation-delay: 0.8s; }
	.line-5 { animation-delay: 1.0s; }

	@keyframes drawLine {
		to { stroke-dashoffset: 0; }
	}

	/* Arrow fade-in */
	.arrow {
		opacity: 0;
		animation: fadeIn 0.3s ease-out forwards;
	}
	.arrow-1 { animation-delay: 0.5s; }
	.arrow-2 { animation-delay: 0.7s; }
	.arrow-3 { animation-delay: 0.9s; }
	.arrow-4 { animation-delay: 1.1s; }
	.arrow-5 { animation-delay: 1.3s; }

	.multiplicity {
		opacity: 0;
		animation: fadeIn 0.4s ease-out forwards;
		animation-delay: 1.2s;
	}

	@keyframes fadeIn {
		to { opacity: 1; }
	}

	/* Particles pulse */
	.particle {
		opacity: 0.8;
	}

	/* Page cards grid */
	.pages-section {
		text-align: center;
	}
	.page-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: var(--space-4);
		text-align: left;
	}
	.page-card {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
		padding: var(--space-5);
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		cursor: pointer;
		transition: all 0.2s;
		text-align: left;
		font-family: var(--font-family);
	}
	.page-card:hover {
		border-color: var(--color-border);
		box-shadow: var(--shadow-md);
		transform: translateY(-2px);
	}
	.page-icon {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--color-primary-light);
		color: var(--color-primary-text);
		border-radius: var(--radius-sm);
	}
	.page-name {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text);
	}
	.page-desc {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		line-height: var(--line-height-normal);
	}

	/* Built with */
	.built-section {
		text-align: center;
		padding-bottom: var(--space-8);
	}
	.tech-row {
		display: flex;
		justify-content: center;
		gap: var(--space-3);
		flex-wrap: wrap;
		margin-top: var(--space-4);
	}
	.tech-badge {
		padding: var(--space-2) var(--space-4);
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-full);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
	}

	@media (max-width: 768px) {
		.page-grid {
			grid-template-columns: 1fr;
		}
		.pipeline-svg-wrap {
			padding: var(--space-3);
		}
	}
</style>
