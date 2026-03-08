<script lang="ts">
	import { app, shortId } from '$lib/data.svelte';
	import type { ReviewSource, ReviewSourceDetail, ReviewBlock, ReviewExtract } from '$lib/data.svelte';
	import Icon from '$lib/components/Icon.svelte';

	const isDev = import.meta.env.DEV;

	// View state
	let selectedSourceId = $state<string | null>(null);
	let sourceDetail = $state<ReviewSourceDetail | null>(null);
	let loading = $state(false);

	// List filters
	let typeFilter = $state('all');
	let qualityFilter = $state('all');
	let sortKey = $state<string>('source_id');
	let sortAsc = $state(true);

	// Detail panel state
	let highlightBlockId = $state<string | null>(null);
	let highlightExtractIds = $state<Set<string>>(new Set());
	let expandedExtractId = $state<string | null>(null);
	let blockFilter = $state<'all' | 'ok' | 'nok' | 'changed' | 'pending'>('all');

	// Review decisions stored in localStorage as JSON: { status, comment }
	interface ReviewDecision {
		status: string;
		comment: string;
	}

	function getReviewDecision(sourceId: string): ReviewDecision {
		try {
			const raw = localStorage.getItem(`review:${sourceId}`);
			if (raw) return JSON.parse(raw);
			// Migrate old format (plain status string)
			const oldStatus = localStorage.getItem(`review-status:${sourceId}`);
			if (oldStatus) {
				const decision = { status: oldStatus, comment: '' };
				localStorage.setItem(`review:${sourceId}`, JSON.stringify(decision));
				localStorage.removeItem(`review-status:${sourceId}`);
				return decision;
			}
		} catch {}
		return { status: 'not-reviewed', comment: '' };
	}

	function saveReviewDecision(sourceId: string, decision: ReviewDecision) {
		try { localStorage.setItem(`review:${sourceId}`, JSON.stringify(decision)); } catch {}
		persistToDisk(sourceId);
	}

	function getReviewStatus(sourceId: string): string {
		return getReviewDecision(sourceId).status;
	}

	// Extract-level decisions: stored per source as { [extractId]: { status, comment, retype, content_hash } }
	interface ExtractDecision {
		status: 'ok' | 'nok' | '';
		comment: string;
		retype?: string;  // override extract type
		content_hash?: string;
	}

	const extractTypes = ['assertion', 'statistic', 'recommendation', 'example', 'definition', 'context', 'attribution', 'noise'];

	let extractDecisions = $state<Record<string, ExtractDecision>>({});
	let editingExtractCommentId = $state<string | null>(null);
	let extractFilter = $state<'all' | 'ok' | 'nok' | 'changed' | 'pending' | 'retyped'>('all');
	let changedExtractIds = $state<Set<string>>(new Set());

	function loadExtractDecisions(sourceId: string) {
		try {
			const raw = localStorage.getItem(`review-extracts:${sourceId}`);
			extractDecisions = raw ? JSON.parse(raw) : {};
		} catch { extractDecisions = {}; }

		const changed = new Set<string>();
		if (sourceDetail) {
			for (const ext of sourceDetail.extracts) {
				const ed = extractDecisions[ext.extract_id];
				if (ed?.status && ed.content_hash) {
					const currentHash = (ext as any).content_hash ?? simpleHash(ext.text);
					if (ed.content_hash !== currentHash) changed.add(ext.extract_id);
				}
			}
		}
		changedExtractIds = changed;
	}

	function saveExtractDecisions(sourceId: string) {
		try {
			const toSave: Record<string, ExtractDecision> = {};
			for (const [k, v] of Object.entries(extractDecisions)) {
				if (v.status || v.comment || v.retype) toSave[k] = v;
			}
			if (Object.keys(toSave).length) {
				localStorage.setItem(`review-extracts:${sourceId}`, JSON.stringify(toSave));
			} else {
				localStorage.removeItem(`review-extracts:${sourceId}`);
			}
		} catch {}
		persistToDisk(sourceId);
	}

	function setExtractStatus(extractId: string, status: 'ok' | 'nok' | '') {
		if (!selectedSourceId || !sourceDetail) return;
		autoPromoteStatus();
		const existing = extractDecisions[extractId] ?? { status: '', comment: '' };
		const newStatus = existing.status === status ? '' : status;
		const ext = sourceDetail.extracts.find(e => e.extract_id === extractId);
		const hash = ext ? ((ext as any).content_hash ?? simpleHash(ext.text)) : existing.content_hash;
		extractDecisions[extractId] = { ...existing, status: newStatus, content_hash: hash };
		if (newStatus === 'nok' && !existing.comment) {
			editingExtractCommentId = extractId;
		} else if (newStatus !== 'nok') {
			editingExtractCommentId = null;
		}
		if (newStatus && changedExtractIds.has(extractId)) {
			changedExtractIds = new Set([...changedExtractIds].filter(id => id !== extractId));
		}
		saveExtractDecisions(selectedSourceId);
	}

	function setExtractRetype(extractId: string, newType: string) {
		if (!selectedSourceId || !sourceDetail) return;
		autoPromoteStatus();
		const existing = extractDecisions[extractId] ?? { status: '', comment: '' };
		const ext = sourceDetail.extracts.find(e => e.extract_id === extractId);
		const originalType = ext?.extract_type ?? '';
		// Clear retype if set back to original
		const retype = newType === originalType ? undefined : newType;
		const hash = ext ? ((ext as any).content_hash ?? simpleHash(ext.text)) : existing.content_hash;
		extractDecisions[extractId] = { ...existing, retype, content_hash: hash };
		saveExtractDecisions(selectedSourceId);
	}

	function saveExtractComment(extractId: string, comment: string) {
		if (!selectedSourceId) return;
		autoPromoteStatus();
		const existing = extractDecisions[extractId] ?? { status: 'nok', comment: '' };
		extractDecisions[extractId] = { ...existing, comment };
		saveExtractDecisions(selectedSourceId);
	}

	let extractStats = $derived.by(() => {
		let ok = 0, nok = 0, retyped = 0;
		for (const v of Object.values(extractDecisions)) {
			if (v.status === 'ok') ok++;
			else if (v.status === 'nok') nok++;
			if (v.retype) retyped++;
		}
		const changed = changedExtractIds.size;
		const total = sourceDetail?.extracts.length ?? 0;
		const reviewed = ok + nok;
		const pct = total > 0 ? Math.round(reviewed / total * 100) : 0;
		return { ok, nok, retyped, changed, pct };
	});

	// Block-level decisions: stored per source as { [blockId]: { status, comment, content_hash } }
	interface BlockDecision {
		status: 'ok' | 'nok' | '';
		comment: string;
		content_hash?: string;
	}

	// Simple hash for change tracking (use export's content_hash if available, else compute)
	function simpleHash(text: string): string {
		let h = 0;
		for (let i = 0; i < text.length; i++) {
			h = ((h << 5) - h + text.charCodeAt(i)) | 0;
		}
		return (h >>> 0).toString(36);
	}

	function getBlockHash(block: ReviewBlock): string {
		return (block as any).content_hash ?? simpleHash(block.text);
	}

	let blockDecisions = $state<Record<string, BlockDecision>>({});
	let changedBlockIds = $state<Set<string>>(new Set());
	let editingBlockId = $state<string | null>(null);
	let saving = $state(false);

	function loadBlockDecisions(sourceId: string) {
		try {
			const raw = localStorage.getItem(`review-blocks:${sourceId}`);
			blockDecisions = raw ? JSON.parse(raw) : {};
		} catch { blockDecisions = {}; }

		// Detect changed blocks: compare stored hash to current content hash
		const changed = new Set<string>();
		if (sourceDetail) {
			for (const block of sourceDetail.content_blocks) {
				const bd = blockDecisions[block.block_id];
				if (bd?.status && bd.content_hash) {
					const currentHash = getBlockHash(block);
					if (bd.content_hash !== currentHash) {
						changed.add(block.block_id);
					}
				}
			}
		}
		changedBlockIds = changed;
	}

	function saveBlockDecisions(sourceId: string) {
		try {
			// Only store blocks that have a decision
			const toSave: Record<string, BlockDecision> = {};
			for (const [k, v] of Object.entries(blockDecisions)) {
				if (v.status || v.comment) toSave[k] = v;
			}
			if (Object.keys(toSave).length) {
				localStorage.setItem(`review-blocks:${sourceId}`, JSON.stringify(toSave));
			} else {
				localStorage.removeItem(`review-blocks:${sourceId}`);
			}
		} catch {}
		persistToDisk(sourceId);
	}

	// Debounced persist to disk via dev API
	let persistTimer: ReturnType<typeof setTimeout> | null = null;

	function persistToDisk(sourceId: string) {
		if (!isDev) return;
		if (persistTimer) clearTimeout(persistTimer);
		persistTimer = setTimeout(() => doPersist(sourceId), 800);
	}

	async function doPersist(sourceId: string) {
		const decision = getReviewDecision(sourceId);
		let blocks: Record<string, BlockDecision> = {};
		let extracts: Record<string, ExtractDecision> = {};
		try {
			const raw = localStorage.getItem(`review-blocks:${sourceId}`);
			if (raw) blocks = JSON.parse(raw);
		} catch {}
		try {
			const raw = localStorage.getItem(`review-extracts:${sourceId}`);
			if (raw) extracts = JSON.parse(raw);
		} catch {}

		// Skip if nothing to save
		const hasData = decision.status !== 'not-reviewed' || decision.comment || Object.keys(blocks).length || Object.keys(extracts).length;
		if (!hasData) return;

		saving = true;
		try {
			await fetch('/api/review/feedback', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					topic: app.currentSlug,
					sourceId,
					source: {
						status: decision.status,
						comment: decision.comment,
						blocks,
						extracts
					}
				})
			});
		} catch { /* dev server may be down */ }
		saving = false;
	}

	// Auto-promote source status to in-progress when reviewing starts
	function autoPromoteStatus() {
		if (selectedSourceId && detailStatus === 'not-reviewed') {
			updateStatus('in-progress');
		}
	}

	function setBlockStatus(blockId: string, status: 'ok' | 'nok' | '') {
		if (!selectedSourceId || !sourceDetail) return;
		autoPromoteStatus();
		const existing = blockDecisions[blockId] ?? { status: '', comment: '' };
		// Toggle off if clicking the same status
		const newStatus = existing.status === status ? '' : status;
		// Store content hash at review time for change detection
		const block = sourceDetail.content_blocks.find(b => b.block_id === blockId);
		const hash = block ? getBlockHash(block) : existing.content_hash;
		blockDecisions[blockId] = { ...existing, status: newStatus, content_hash: hash };
		if (newStatus === 'nok' && !existing.comment) {
			editingBlockId = blockId;
		} else if (newStatus !== 'nok') {
			editingBlockId = null;
		}
		// Clear changed flag if re-reviewed
		if (newStatus && changedBlockIds.has(blockId)) {
			changedBlockIds = new Set([...changedBlockIds].filter(id => id !== blockId));
		}
		saveBlockDecisions(selectedSourceId);
	}

	function saveBlockComment(blockId: string, comment: string) {
		if (!selectedSourceId) return;
		autoPromoteStatus();
		const existing = blockDecisions[blockId] ?? { status: 'nok', comment: '' };
		blockDecisions[blockId] = { ...existing, comment };
		saveBlockDecisions(selectedSourceId);
	}

	// Block review stats for current source
	let blockStats = $derived.by(() => {
		let ok = 0, nok = 0;
		for (const v of Object.values(blockDecisions)) {
			if (v.status === 'ok') ok++;
			else if (v.status === 'nok') nok++;
		}
		const changed = changedBlockIds.size;
		const total = sourceDetail?.content_blocks.length ?? 0;
		const reviewed = ok + nok;
		const pct = total > 0 ? Math.round(reviewed / total * 100) : 0;
		return { ok, nok, changed, pct };
	});

	function exportReviewDecisions() {
		const decisions: Record<string, any> = {};
		for (const s of allSources) {
			const d = getReviewDecision(s.source_id);
			const hasSourceDecision = d.status !== 'not-reviewed' || d.comment;
			// Check for block decisions
			let blocks: Record<string, BlockDecision> | null = null;
			try {
				const raw = localStorage.getItem(`review-blocks:${s.source_id}`);
				if (raw) blocks = JSON.parse(raw);
			} catch {}
			if (hasSourceDecision || blocks) {
				decisions[s.source_id] = {
					title: s.title,
					...d,
					...(blocks ? { blocks } : {})
				};
			}
		}
		const blob = new Blob([JSON.stringify(decisions, null, 2)], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `review-decisions-${app.currentSlug}-${new Date().toISOString().slice(0, 10)}.json`;
		a.click();
		URL.revokeObjectURL(url);
	}

	// Claim → Finding lookup (built from findings data)
	let claimToFinding = $derived.by(() => {
		const map = new Map<string, { findingId: string; findingTitle: string; category: string }>();
		if (!app.findings?.findings) return map;
		for (const f of app.findings.findings) {
			for (const c of f.claims) {
				map.set(c.id, { findingId: f.id, findingTitle: f.title, category: f.category });
			}
		}
		return map;
	});

	// Claim ID → claim data lookup
	let claimById = $derived.by(() => {
		const map = new Map<string, { id: string; statement: string; sourceCount: number }>();
		if (!app.findings?.findings) return map;
		for (const f of app.findings.findings) {
			for (const c of f.claims) {
				map.set(c.id, { id: c.id, statement: c.statement, sourceCount: c.source_count });
			}
		}
		return map;
	});

	let allSources = $derived(app.review?.sources ?? []);

	let filtered = $derived.by(() => {
		let list = [...allSources];
		if (typeFilter !== 'all') list = list.filter(s => s.type === typeFilter);
		if (qualityFilter !== 'all') list = list.filter(s => s.quality_status === qualityFilter);
		if (app.searchQuery) {
			const q = app.searchQuery.toLowerCase();
			list = list.filter(s => s.title.toLowerCase().includes(q) || s.source_id.toLowerCase().includes(q));
		}
		list.sort((a: any, b: any) => {
			const av = a[sortKey], bv = b[sortKey];
			if (typeof av === 'number' && typeof bv === 'number') return sortAsc ? av - bv : bv - av;
			return sortAsc ? String(av ?? '').localeCompare(String(bv ?? '')) : String(bv ?? '').localeCompare(String(av ?? ''));
		});
		return list;
	});

	let typeCounts = $derived.by(() => {
		const counts = new Map<string, number>();
		for (const s of allSources) counts.set(s.type, (counts.get(s.type) || 0) + 1);
		return counts;
	});

	function toggleSort(key: string) {
		if (sortKey === key) { sortAsc = !sortAsc; } else { sortKey = key; sortAsc = true; }
	}

	async function selectSource(sourceId: string) {
		selectedSourceId = sourceId;
		loading = true;
		highlightBlockId = null;
		highlightExtractIds = new Set();
		editingBlockId = null;
		blockFilter = 'all';
		extractFilter = 'all';
		const shortSrc = sourceId.split(':').pop();
		sourceDetail = await app.fetchJson<ReviewSourceDetail>(`${app.currentSlug}/review/${shortSrc}.json`);
		// Load from disk first (if dev), then overlay with localStorage
		if (isDev) {
			try {
				const res = await fetch(`/api/review/feedback?topic=${app.currentSlug}&source=${shortSrc}`);
				if (res.ok) {
					const disk = await res.json();
					if (disk) {
						// Hydrate localStorage from disk if no local data exists
						const localDecision = getReviewDecision(sourceId);
						if (localDecision.status === 'not-reviewed' && !localDecision.comment) {
							if (disk.status || disk.comment) {
								saveReviewDecision(sourceId, { status: disk.status || 'not-reviewed', comment: disk.comment || '' });
							}
						}
						const localBlocks = localStorage.getItem(`review-blocks:${sourceId}`);
						if (!localBlocks && disk.blocks && Object.keys(disk.blocks).length) {
							// Map backend rework → frontend nok
							const mapped: Record<string, BlockDecision> = {};
							for (const [k, v] of Object.entries(disk.blocks) as [string, any][]) {
								mapped[k] = { status: v.status === 'rework' ? 'nok' : v.status, comment: v.comment || '' };
							}
							localStorage.setItem(`review-blocks:${sourceId}`, JSON.stringify(mapped));
						}
					}
				}
			} catch { /* dev server may not have the endpoint yet */ }
		}
		loadBlockDecisions(sourceId);
		loadExtractDecisions(sourceId);
		loading = false;
	}

	function goBack() {
		selectedSourceId = null;
		sourceDetail = null;
	}

	// Navigate prev/next
	function navigateSource(delta: number) {
		if (!selectedSourceId) return;
		const idx = filtered.findIndex(s => s.source_id === selectedSourceId);
		const next = filtered[idx + delta];
		if (next) selectSource(next.source_id);
	}

	let currentIdx = $derived(selectedSourceId ? filtered.findIndex(s => s.source_id === selectedSourceId) : -1);

	// Extract type colors (reuse from DeepDive)
	const extractColors: Record<string, string> = {
		assertion: '#3B6EC4', statistic: '#C4841D', recommendation: '#D97757',
		example: '#3D8B37', definition: '#7C6F9B', context: '#9B9A95',
		attribution: '#3B6EC4', noise: '#C8C6BF',
	};

	function extractColor(type: string): string {
		return extractColors[type] ?? '#C8C6BF';
	}

	// Quality dot colors
	const qualityDot: Record<string, string> = {
		'ok': 'var(--color-success)', 'pending': 'var(--color-text-tertiary)',
		'thin-content': 'var(--color-warning)', 'block-quality': 'var(--color-warning)',
		'high-noise': '#EA580C', 'not-extracted': 'var(--color-text-tertiary)',
	};

	// Build extract lookup for blocks panel
	let extractById = $derived.by(() => {
		if (!sourceDetail) return new Map<string, ReviewExtract>();
		const map = new Map<string, ReviewExtract>();
		for (const e of sourceDetail.extracts) map.set(e.extract_id, e);
		return map;
	});

	// Block → extract type for coloring

	function clickBlock(block: ReviewBlock) {
		if (block.extracted_as.length) {
			highlightExtractIds = new Set(block.extracted_as);
			highlightBlockId = block.block_id;
			// Ensure extracts are visible (reset filter if needed)
			if (extractFilter !== 'all') {
				const firstId = block.extracted_as[0];
				const el = document.getElementById(`extract-${firstId}`);
				if (!el) extractFilter = 'all';
			}
			setTimeout(() => {
				const el = document.getElementById(`extract-${block.extracted_as[0]}`);
				el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
			}, 50);
		}
	}

	function clickExtract(ext: ReviewExtract) {
		highlightExtractIds = new Set([ext.extract_id]);
		// Find block that references this extract
		const block = sourceDetail?.content_blocks.find(b => b.extracted_as.includes(ext.extract_id));
		if (block) {
			highlightBlockId = block.block_id;
			// Ensure block is visible (reset filter if needed)
			if (blockFilter !== 'all') {
				const bd = blockDecisions[block.block_id];
				const isChanged = changedBlockIds.has(block.block_id);
				const status = isChanged ? 'changed' : bd?.status === 'ok' ? 'ok' : bd?.status === 'nok' ? 'nok' : 'pending';
				if (blockFilter !== status) blockFilter = 'all';
			}
			setTimeout(() => {
				const el = document.getElementById(`block-${block.block_id}`);
				el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
			}, 50);
		}
	}

	// Review decision for detail view
	let detailStatus = $state('not-reviewed');
	let detailComment = $state('');
	$effect(() => {
		if (selectedSourceId) {
			const d = getReviewDecision(selectedSourceId);
			detailStatus = d.status;
			detailComment = d.comment;
		}
	});

	function updateStatus(status: string) {
		if (selectedSourceId) {
			detailStatus = status;
			saveReviewDecision(selectedSourceId, { status, comment: detailComment });
		}
	}

	function updateComment() {
		if (selectedSourceId) {
			saveReviewDecision(selectedSourceId, { status: detailStatus, comment: detailComment });
		}
	}

	// Review summary stats
	let reviewStats = $derived.by(() => {
		let reviewed = 0, approved = 0, refinement = 0, commented = 0;
		for (const s of allSources) {
			const d = getReviewDecision(s.source_id);
			if (d.status !== 'not-reviewed') reviewed++;
			if (d.status === 'approved') approved++;
			if (d.status === 'needs-refinement') refinement++;
			if (d.comment) commented++;
		}
		return { reviewed, approved, refinement, commented };
	});
</script>

{#if !selectedSourceId}
	<!-- SOURCE LIST VIEW -->
	{#if allSources.length > 0}
		<div class="toolbar">
			<div class="category-nav">
				<button class="cat-pill" class:active={typeFilter === 'all'} onclick={() => typeFilter = 'all'}>
					All <span class="cat-count">{allSources.length}</span>
				</button>
				{#each [...typeCounts.entries()] as [t, count]}
					<button class="cat-pill" class:active={typeFilter === t} onclick={() => typeFilter = t}>
						{#if t === 'web'}<Icon name="globe" size={13} />
						{:else if t === 'youtube'}<Icon name="youtube" size={13} />
						{:else if t === 'pdf'}<Icon name="file-text" size={13} />
						{/if}
						{t} <span class="cat-count">{count}</span>
					</button>
				{/each}
			</div>
		</div>

		<div class="table-wrap">
			<table>
				<thead>
					<tr>
						<th class="sortable col-id" onclick={() => toggleSort('source_id')}>
							ID {#if sortKey === 'source_id'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
						</th>
						<th class="sortable" onclick={() => toggleSort('title')}>
							Title {#if sortKey === 'title'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
						</th>
						<th class="sortable col-type" onclick={() => toggleSort('type')}>
							Type {#if sortKey === 'type'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
						</th>
						<th class="sortable col-num" onclick={() => toggleSort('block_count')}>
							Blocks {#if sortKey === 'block_count'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
						</th>
						<th class="sortable col-num" onclick={() => toggleSort('extract_count')}>
							Extracts {#if sortKey === 'extract_count'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
						</th>
						<th class="sortable col-num" onclick={() => toggleSort('noise_count')}>
							Noise {#if sortKey === 'noise_count'}<Icon name={sortAsc ? 'arrow-up' : 'arrow-down'} size={12} />{/if}
						</th>
						<th class="col-quality">Quality</th>
						<th class="col-status">Review</th>
					</tr>
				</thead>
				<tbody>
					{#each filtered as source}
						{@const rstatus = getReviewStatus(source.source_id)}
						<tr class="clickable" onclick={() => selectSource(source.source_id)}>
							<td class="col-id dim">{shortId(source.source_id)}</td>
							<td class="col-title" title={source.title}>{source.title}</td>
							<td class="col-type">
								{#if source.type === 'web'}<Icon name="globe" size={16} />
								{:else if source.type === 'youtube'}<Icon name="youtube" size={16} />
								{:else if source.type === 'pdf'}<Icon name="file-text" size={16} />
								{/if}
							</td>
							<td class="col-num">{source.block_count}</td>
							<td class="col-num">{source.extract_count}</td>
							<td class="col-num" class:noise-high={source.noise_count > source.extract_count * 0.2}>
								{source.noise_count}
							</td>
							<td class="col-quality">
								<span class="quality-dot" style="background:{qualityDot[source.quality_status] ?? 'var(--color-text-tertiary)'}"></span>
							</td>
							<td class="col-status">
								<span class="review-badge" class:approved={rstatus === 'approved'} class:needs-refinement={rstatus === 'needs-refinement'} class:in-progress={rstatus === 'in-progress'}>
									{rstatus.replace(/-/g, ' ')}
								</span>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<div class="list-footer">
			<p class="summary">
				{filtered.length} of {allSources.length} sources &middot;
				{reviewStats.approved} approved, {reviewStats.refinement} need refinement
				{#if reviewStats.commented} &middot; {reviewStats.commented} with comments{/if}
				&middot; Updated {app.review?.generated ?? ''}
			</p>
			{#if reviewStats.reviewed > 0}
				<button class="export-btn" onclick={exportReviewDecisions}>
					<Icon name="download" size={13} />
					Export decisions
				</button>
			{/if}
		</div>
	{:else}
		<div class="empty-state"><p>No review data available. Run the back-end exporter with review output.</p></div>
	{/if}

{:else}
	<!-- DETAIL / REVIEW VIEW -->
	<div class="detail-toolbar">
		<button class="back-btn" onclick={goBack}>
			<Icon name="chevron-left" size={16} />
			Back to list
		</button>
		<div class="detail-nav">
			<button class="nav-btn" disabled={currentIdx <= 0} onclick={() => navigateSource(-1)}>
				<Icon name="chevron-left" size={14} /> Prev
			</button>
			<span class="nav-pos">{currentIdx + 1} / {filtered.length}</span>
			<button class="nav-btn" disabled={currentIdx >= filtered.length - 1} onclick={() => navigateSource(1)}>
				Next <Icon name="chevron-right" size={14} />
			</button>
		</div>
		<div class="detail-actions">
			{#if saving}
				<span class="save-indicator">saving...</span>
			{/if}
			<select class="status-select" value={detailStatus} onchange={(e) => updateStatus(e.currentTarget.value)}>
				<option value="not-reviewed">Not reviewed</option>
				<option value="in-progress">In progress</option>
				<option value="approved">Approved</option>
				<option value="needs-refinement">Needs refinement</option>
			</select>
			{#if sourceDetail?.url}
				<a href={sourceDetail.url} target="_blank" rel="noopener" class="open-btn">
					<Icon name="external" size={13} /> View original
				</a>
			{/if}
		</div>
	</div>

	{#if loading}
		<div class="empty-state"><p>Loading source data...</p></div>
	{:else if sourceDetail}
		<div class="detail-header">
			<h2 class="detail-title">{sourceDetail.title}</h2>
			<p class="detail-meta">
				{shortId(sourceDetail.source_id)} &middot; {sourceDetail.type}
				&middot; {sourceDetail.content_blocks.length} blocks &middot; {sourceDetail.extracts.length} extracts
				{#if sourceDetail.extracts.filter(e => e.claims.length > 0).length}
					&middot; {sourceDetail.extracts.filter(e => e.claims.length > 0).length} linked to claims
				{/if}
			</p>
		</div>

		<div class="panels">
			<!-- PANEL 1: Original Source -->
			<div class="panel panel-original">
				<div class="panel-header">
					<Icon name="globe" size={14} />
					Original
				</div>
				<div class="panel-body">
					{#if sourceDetail.type === 'youtube' && sourceDetail.url}
						{@const vid = sourceDetail.url.includes('v=') ? sourceDetail.url.split('v=')[1]?.split('&')[0] : sourceDetail.url.split('youtu.be/')[1]?.split('?')[0] ?? ''}
						{#if vid}
							<div class="embed-video">
								<iframe src="https://www.youtube-nocookie.com/embed/{vid}" title={sourceDetail.title} allowfullscreen></iframe>
							</div>
						{/if}
					{:else if sourceDetail.type === 'pdf' && sourceDetail.document_path}
						<embed src="/data/{app.currentSlug}/{sourceDetail.document_path}" type="application/pdf" class="embed-pdf" />
					{:else if sourceDetail.url}
						<div class="original-link-panel">
							<div class="original-link-icon">
								<Icon name="globe" size={32} />
							</div>
							<h3 class="original-link-title">{sourceDetail.title}</h3>
							<a href={sourceDetail.url} target="_blank" rel="noopener" class="original-link-btn">
								<Icon name="external" size={14} />
								Open in new tab
							</a>
							<p class="original-link-url">{sourceDetail.url}</p>
						</div>
					{:else}
						<div class="empty-state"><p>No source URL available.</p></div>
					{/if}
				</div>
			</div>

			<!-- PANEL 2: Content Blocks -->
			<div class="panel panel-blocks">
				<div class="panel-header">
					<Icon name="extract" size={14} />
					Blocks ({sourceDetail.content_blocks.length})
					{#if blockStats.ok || blockStats.nok}
						<span class="block-stats">
							{#if blockStats.ok}<span class="block-stat-ok">{blockStats.ok} OK</span>{/if}
							{#if blockStats.nok}<span class="block-stat-nok">{blockStats.nok} NOK</span>{/if}
							{#if blockStats.changed}<span class="block-stat-changed">{blockStats.changed} changed</span>{/if}
							<span class="block-stat-pct">{blockStats.pct}%</span>
						</span>
					{/if}
				</div>
				{#if blockStats.ok || blockStats.nok || blockStats.changed}
					<div class="block-filters">
						<button class="block-filter" class:active={blockFilter === 'all'} onclick={() => blockFilter = 'all'}>All</button>
						<button class="block-filter" class:active={blockFilter === 'pending'} onclick={() => blockFilter = 'pending'}>Pending</button>
						{#if blockStats.ok}<button class="block-filter filter-ok" class:active={blockFilter === 'ok'} onclick={() => blockFilter = 'ok'}>OK</button>{/if}
						{#if blockStats.nok}<button class="block-filter filter-nok" class:active={blockFilter === 'nok'} onclick={() => blockFilter = 'nok'}>NOK</button>{/if}
						{#if blockStats.changed}<button class="block-filter filter-changed" class:active={blockFilter === 'changed'} onclick={() => blockFilter = 'changed'}>Changed</button>{/if}
					</div>
				{/if}
				<div class="panel-body blocks-body">
					{#each sourceDetail.content_blocks as block}
						{@const hasExtracts = block.extracted_as.length > 0}
						{@const onlyNoise = hasExtracts && block.extracted_as.every(eid => extractById.get(eid)?.extract_type === 'noise')}
						{@const bd = blockDecisions[block.block_id]}
						{@const isChanged = changedBlockIds.has(block.block_id)}
						{@const blockStatus = isChanged ? 'changed' : bd?.status === 'ok' ? 'ok' : bd?.status === 'nok' ? 'nok' : 'pending'}
						{#if blockFilter === 'all' || blockFilter === blockStatus}
						<div
							id="block-{block.block_id}"
							class="block"
							class:block-extracted={hasExtracts && !onlyNoise}
							class:block-noise={onlyNoise}
							class:block-skipped={!hasExtracts}
							class:block-highlight={highlightBlockId === block.block_id}
							class:block-ok={bd?.status === 'ok' && !isChanged}
							class:block-nok={bd?.status === 'nok'}
							class:block-changed={isChanged}
							onclick={() => clickBlock(block)}
						>
							<div class="block-content">
								{#if block.format === 'heading'}
									<h4 class="block-heading">{block.text}</h4>
								{:else if block.format === 'bullet'}
									<p class="block-bullet">&bull; {block.text}</p>
								{:else if block.format === 'quote'}
									<blockquote class="block-quote">{block.text}</blockquote>
								{:else if block.format === 'figure' && block.image_path}
									<p class="block-figure">{block.text}</p>
								{:else}
									<p class="block-prose">{block.text}</p>
								{/if}
								{#if isChanged}
									<span class="block-changed-badge" title="Content changed since last review">changed</span>
								{/if}
								<div class="block-actions">
									<button
										class="block-verdict-btn ok"
										class:active={bd?.status === 'ok'}
										title="Mark OK"
										onclick={(e: MouseEvent) => { e.stopPropagation(); setBlockStatus(block.block_id, 'ok'); }}
									><Icon name="check" size={12} /></button>
									<button
										class="block-verdict-btn nok"
										class:active={bd?.status === 'nok'}
										title="Mark NOK"
										onclick={(e: MouseEvent) => { e.stopPropagation(); setBlockStatus(block.block_id, 'nok'); }}
									><Icon name="x" size={12} /></button>
								</div>
							</div>
							{#if bd?.status === 'nok' || editingBlockId === block.block_id}
								<textarea
									class="block-comment"
									placeholder="What's wrong with this block?"
									value={bd?.comment ?? ''}
									rows="1"
									onclick={(e: MouseEvent) => e.stopPropagation()}
									oninput={(e: Event) => { const t = e.currentTarget as HTMLTextAreaElement; t.style.height = 'auto'; t.style.height = t.scrollHeight + 'px'; }}
									onblur={(e: Event) => saveBlockComment(block.block_id, (e.currentTarget as HTMLTextAreaElement).value)}
								></textarea>
							{/if}
						</div>
						{/if}
					{/each}
				</div>
			</div>

			<!-- PANEL 3: Extracts -->
			<div class="panel panel-extracts">
				<div class="panel-header">
					<Icon name="findings" size={14} />
					Extracts ({sourceDetail.extracts.length})
					{#if extractStats.ok || extractStats.nok}
						<span class="block-stats">
							{#if extractStats.ok}<span class="block-stat-ok">{extractStats.ok} OK</span>{/if}
							{#if extractStats.nok}<span class="block-stat-nok">{extractStats.nok} NOK</span>{/if}
							{#if extractStats.retyped}<span class="block-stat-changed">{extractStats.retyped} retyped</span>{/if}
							{#if extractStats.changed}<span class="block-stat-changed">{extractStats.changed} changed</span>{/if}
							<span class="block-stat-pct">{extractStats.pct}%</span>
						</span>
					{/if}
				</div>
				{#if extractStats.ok || extractStats.nok || extractStats.changed || extractStats.retyped}
					<div class="block-filters">
						<button class="block-filter" class:active={extractFilter === 'all'} onclick={() => extractFilter = 'all'}>All</button>
						<button class="block-filter" class:active={extractFilter === 'pending'} onclick={() => extractFilter = 'pending'}>Pending</button>
						{#if extractStats.ok}<button class="block-filter filter-ok" class:active={extractFilter === 'ok'} onclick={() => extractFilter = 'ok'}>OK</button>{/if}
						{#if extractStats.nok}<button class="block-filter filter-nok" class:active={extractFilter === 'nok'} onclick={() => extractFilter = 'nok'}>NOK</button>{/if}
						{#if extractStats.retyped}<button class="block-filter filter-changed" class:active={extractFilter === 'retyped'} onclick={() => extractFilter = 'retyped'}>Retyped</button>{/if}
						{#if extractStats.changed}<button class="block-filter filter-changed" class:active={extractFilter === 'changed'} onclick={() => extractFilter = 'changed'}>Changed</button>{/if}
					</div>
				{/if}
				<div class="panel-body extracts-body">
					{#each sourceDetail.extracts as ext}
						{@const ed = extractDecisions[ext.extract_id]}
						{@const isExtChanged = changedExtractIds.has(ext.extract_id)}
						{@const extStatus = isExtChanged ? 'changed' : ed?.retype ? 'retyped' : ed?.status === 'ok' ? 'ok' : ed?.status === 'nok' ? 'nok' : 'pending'}
						{@const displayType = ed?.retype ?? ext.extract_type}
						{#if extractFilter === 'all' || extractFilter === extStatus}
						<div
							id="extract-{ext.extract_id}"
							class="extract-card"
							class:extract-highlight={highlightExtractIds.has(ext.extract_id)}
							class:has-claims={ext.claims.length > 0}
							class:block-ok={ed?.status === 'ok' && !isExtChanged}
							class:block-nok={ed?.status === 'nok'}
							class:block-changed={isExtChanged}
							style="border-left-color: {extractColor(displayType)}"
							onclick={() => clickExtract(ext)}
						>
							<div class="extract-header">
								<select
									class="extract-type-select"
									style="background: {extractColor(displayType)}; color: white"
									value={displayType}
									onclick={(e: MouseEvent) => e.stopPropagation()}
									onchange={(e: Event) => setExtractRetype(ext.extract_id, (e.currentTarget as HTMLSelectElement).value)}
								>
									{#each extractTypes as t}
										<option value={t}>{t}</option>
									{/each}
								</select>
								{#if ed?.retype}
									<span class="retype-indicator" title="Was: {ext.extract_type}">was {ext.extract_type}</span>
								{/if}
								{#if ext.claims.length}
									<button
										class="extract-claims-badge"
										class:expanded={expandedExtractId === ext.extract_id}
										onclick={(e: MouseEvent) => { e.stopPropagation(); expandedExtractId = expandedExtractId === ext.extract_id ? null : ext.extract_id; }}
									>
										<Icon name="claim" size={11} />
										{ext.claims.length} claim{ext.claims.length > 1 ? 's' : ''}
										<Icon name={expandedExtractId === ext.extract_id ? 'chevron-up' : 'chevron-down'} size={10} />
									</button>
								{/if}
								{#if isExtChanged}
									<span class="block-changed-badge">changed</span>
								{/if}
								<div class="extract-actions">
									<button
										class="block-verdict-btn ok"
										class:active={ed?.status === 'ok'}
										title="Mark OK"
										onclick={(e: MouseEvent) => { e.stopPropagation(); setExtractStatus(ext.extract_id, 'ok'); }}
									><Icon name="check" size={12} /></button>
									<button
										class="block-verdict-btn nok"
										class:active={ed?.status === 'nok'}
										title="Mark NOK"
										onclick={(e: MouseEvent) => { e.stopPropagation(); setExtractStatus(ext.extract_id, 'nok'); }}
									><Icon name="x" size={12} /></button>
								</div>
							</div>
							<p class="extract-text">{ext.text}</p>
							{#if ed?.status === 'nok' || editingExtractCommentId === ext.extract_id}
								<textarea
									class="block-comment"
									placeholder="What's wrong with this extract?"
									value={ed?.comment ?? ''}
									rows="1"
									onclick={(e: MouseEvent) => e.stopPropagation()}
									oninput={(e: Event) => { const t = e.currentTarget as HTMLTextAreaElement; t.style.height = 'auto'; t.style.height = t.scrollHeight + 'px'; }}
									onblur={(e: Event) => saveExtractComment(ext.extract_id, (e.currentTarget as HTMLTextAreaElement).value)}
								></textarea>
							{/if}
							{#if expandedExtractId === ext.extract_id && ext.claims.length}
								<div class="claim-details">
									{#each ext.claims as claimId}
										{@const claim = claimById.get(claimId)}
										{@const finding = claimToFinding.get(claimId)}
										<div class="claim-card">
											<div class="claim-card-header">
												<span class="claim-id">{shortId(claimId)}</span>
												{#if claim}
													<span class="claim-sources">{claim.sourceCount} source{claim.sourceCount !== 1 ? 's' : ''}</span>
												{/if}
											</div>
											{#if claim}
												<p class="claim-statement">{claim.statement}</p>
											{:else}
												<p class="claim-statement dim">Claim data not loaded</p>
											{/if}
											{#if finding}
												<div class="claim-finding">
													<Icon name="findings" size={11} />
													<span class="finding-category">{finding.category}</span>
													<span class="finding-title">{finding.findingTitle}</span>
												</div>
											{/if}
										</div>
									{/each}
								</div>
							{/if}
						</div>
						{/if}
					{/each}
				</div>
			</div>
		</div>
	{:else}
		<div class="empty-state"><p>Failed to load source data.</p></div>
	{/if}
{/if}

<style>
	/* Use full width */
	:global(.content:has(.panels)) {
		max-width: none;
	}
	:global(.content:has(.table-wrap)) {
		max-width: none;
	}

	/* Toolbar */
	.toolbar { margin-bottom: var(--space-4); }
	.category-nav {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2);
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
	.cat-pill:hover { border-color: var(--color-border); color: var(--color-text); }
	.cat-pill.active {
		background: var(--color-text);
		border-color: var(--color-text);
		color: var(--color-surface);
		font-weight: var(--font-weight-medium);
	}
	.cat-count { font-size: var(--font-size-xs); opacity: 0.7; }

	/* Table */
	.table-wrap {
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		overflow-x: auto;
	}
	.sortable { cursor: pointer; user-select: none; white-space: nowrap; }
	.sortable :global(.icon) { margin-left: 2px; vertical-align: middle; }
	.sortable:hover { color: var(--color-text); }
	.clickable { cursor: pointer; }
	.clickable:hover td { background: var(--color-surface-hover); }
	thead tr { background: var(--color-surface); }
	.col-id { width: 70px; text-align: center; white-space: nowrap; }
	.col-title { max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.col-type { text-align: center; color: var(--color-text-tertiary); width: 60px; }
	.col-num { text-align: center; width: 70px; }
	.col-quality { text-align: center; width: 60px; }
	.col-status { white-space: nowrap; }
	.dim { color: var(--color-text-secondary); }
	.noise-high { color: var(--color-error); font-weight: var(--font-weight-medium); }
	.quality-dot {
		display: inline-block;
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}
	.review-badge {
		font-size: var(--font-size-xs);
		padding: 1px 8px;
		border-radius: var(--radius-full);
		background: var(--color-border-light);
		color: var(--color-text-secondary);
		text-transform: capitalize;
	}
	.review-badge.approved { background: var(--color-success-bg, #e8f5e9); color: var(--color-success); }
	.review-badge.needs-refinement { background: var(--color-warning-bg); color: var(--color-warning); }
	.review-badge.in-progress { background: var(--color-claim-bg, #e3f2fd); color: var(--color-claim); }
	.summary { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-top: var(--space-3); }

	/* Detail toolbar */
	.detail-toolbar {
		display: flex;
		align-items: center;
		gap: var(--space-4);
		margin-bottom: var(--space-4);
		flex-wrap: wrap;
	}
	.back-btn {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
		padding: var(--space-1) var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-surface);
		font-family: var(--font-family);
		font-size: var(--font-size-sm);
		cursor: pointer;
		color: var(--color-text-secondary);
	}
	.back-btn:hover { color: var(--color-text); border-color: var(--color-text-secondary); }
	.detail-nav {
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}
	.nav-btn {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
		padding: var(--space-1) var(--space-2);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-sm);
		background: var(--color-surface);
		font-family: var(--font-family);
		font-size: var(--font-size-xs);
		cursor: pointer;
		color: var(--color-text-secondary);
	}
	.nav-btn:hover:not(:disabled) { color: var(--color-text); border-color: var(--color-border); }
	.nav-btn:disabled { opacity: 0.4; cursor: default; }
	.nav-pos { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
	.detail-actions {
		display: flex;
		align-items: center;
		gap: var(--space-3);
		margin-left: auto;
	}
	.status-select {
		font-family: var(--font-family);
		font-size: var(--font-size-sm);
		padding: var(--space-1) var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-surface);
		color: var(--color-text);
	}
	.open-btn {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
		padding: var(--space-1) var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		background: var(--color-surface);
	}
	.open-btn:hover { border-color: var(--color-primary); text-decoration: none; }
	.save-indicator { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

	/* Detail header */
	.detail-header { margin-bottom: var(--space-4); }
	.detail-title {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		line-height: var(--line-height-tight);
	}
	.detail-meta {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		margin-top: var(--space-1);
	}

	/* Three-panel layout */
	.panels {
		display: grid;
		grid-template-columns: 2fr 1.5fr 1.5fr;
		gap: var(--space-3);
		height: calc(100vh - var(--header-height) - 11rem);
		min-height: 400px;
	}
	.panel {
		display: flex;
		flex-direction: column;
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-sm);
		min-height: 0;
	}
	.panel-header {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-3) var(--space-4);
		border-bottom: 1px solid var(--color-border-light);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		color: var(--color-text-secondary);
		flex-shrink: 0;
	}
	.panel-body {
		flex: 1;
		overflow-y: auto;
		min-height: 0;
	}

	/* Panel 1: Original source */
	.panel-original .panel-body {
		position: relative;
	}
	.original-link-panel {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		padding: var(--space-6);
		text-align: center;
		gap: var(--space-3);
	}
	.original-link-icon {
		color: var(--color-text-tertiary);
		opacity: 0.4;
	}
	.original-link-title {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-medium);
		color: var(--color-text);
		max-width: 300px;
		line-height: var(--line-height-normal);
	}
	.original-link-btn {
		display: inline-flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-2) var(--space-4);
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		transition: border-color 0.15s, box-shadow 0.15s;
	}
	.original-link-btn:hover {
		border-color: var(--color-primary);
		text-decoration: none;
		box-shadow: var(--shadow-sm);
	}
	.original-link-url {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		word-break: break-all;
		max-width: 300px;
	}
	.embed-video {
		position: relative;
		padding-bottom: 56.25%;
		height: 0;
	}
	.embed-video iframe {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		border: none;
	}
	.embed-pdf {
		width: 100%;
		height: 100%;
		border: none;
	}

	/* Panel 2: Blocks */
	.blocks-body {
		padding: var(--space-3);
	}
	.block {
		padding: var(--space-1) var(--space-3);
		border-left: 3px solid transparent;
		cursor: pointer;
		border-radius: 2px;
		transition: background 0.1s;
		margin-bottom: 1px;
	}
	.block:hover { background: var(--color-surface-hover); }
	.block-extracted { border-left-color: var(--color-success); }
	.block-noise { border-left-color: var(--color-border); opacity: 0.5; }
	.block-skipped { border-left-color: transparent; }
	.block-highlight {
		background: var(--color-finding-bg, #fff8e1);
		outline: 2px solid var(--color-warning);
		outline-offset: -2px;
	}
	.block-heading {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		margin: var(--space-3) 0 var(--space-1);
		color: var(--color-text);
	}
	.block-prose, .block-bullet, .block-figure {
		font-size: var(--font-size-xs);
		line-height: var(--line-height-normal);
		color: var(--color-text-secondary);
		margin: 0;
	}
	.block-bullet { padding-left: var(--space-2); }
	.block-quote {
		font-size: var(--font-size-xs);
		line-height: var(--line-height-normal);
		color: var(--color-text-secondary);
		border-left: 2px solid var(--color-border);
		padding-left: var(--space-3);
		margin: var(--space-1) 0;
		font-style: italic;
	}

	/* Block verdict */
	.block-content {
		display: flex;
		align-items: flex-start;
		gap: var(--space-2);
	}
	.block-content > :first-child { flex: 1; min-width: 0; }
	.block-actions {
		display: flex;
		gap: 2px;
		flex-shrink: 0;
		opacity: 0;
		transition: opacity 0.1s;
	}
	.block:hover .block-actions,
	.block-ok .block-actions,
	.block-nok .block-actions { opacity: 1; }
	.block-verdict-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 20px;
		height: 20px;
		padding: 0;
		border-radius: 3px;
		border: 1px solid transparent;
		background: none;
		color: var(--color-text-tertiary);
		cursor: pointer;
	}
	.block-verdict-btn:hover { background: var(--color-surface-hover); }
	.block-verdict-btn.ok:hover { color: var(--color-success); }
	.block-verdict-btn.nok:hover { color: var(--color-error, #d32f2f); }
	.block-verdict-btn.ok.active {
		color: var(--color-success);
	}
	.block-verdict-btn.nok.active {
		color: var(--color-error, #d32f2f);
	}
	.block-ok { background: color-mix(in srgb, var(--color-success) 4%, transparent); }
	.block-nok { background: color-mix(in srgb, var(--color-warning) 6%, transparent); }
	.block-comment {
		width: 100%;
		padding: var(--space-1) var(--space-2);
		border: 1px solid var(--color-warning);
		border-radius: 3px;
		font-family: var(--font-family);
		font-size: var(--font-size-xs);
		color: var(--color-text);
		background: var(--color-surface);
		resize: none;
		overflow: hidden;
		margin-top: var(--space-1);
		field-sizing: content;
	}
	.block-comment:focus { outline: none; border-color: var(--color-warning); }
	.block-comment::placeholder { color: var(--color-text-tertiary); }
	.block-stats {
		display: flex;
		gap: var(--space-2);
		margin-left: auto;
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-normal);
	}
	.block-stat-ok { color: var(--color-success); }
	.block-stat-nok { color: var(--color-warning); }
	.block-stat-changed { color: var(--color-info, #1976d2); }
	.block-stat-pct { color: var(--color-text-tertiary); }

	/* Block filters */
	.block-filters {
		display: flex;
		gap: 2px;
		padding: var(--space-1) var(--space-3);
		border-bottom: 1px solid var(--color-border-light);
		flex-shrink: 0;
	}
	.block-filter {
		font-size: 10px;
		font-family: var(--font-family);
		padding: 1px 8px;
		border-radius: var(--radius-full);
		border: 1px solid var(--color-border-light);
		background: none;
		color: var(--color-text-tertiary);
		cursor: pointer;
	}
	.block-filter:hover { border-color: var(--color-border); color: var(--color-text-secondary); }
	.block-filter.active { background: var(--color-text); border-color: var(--color-text); color: var(--color-surface); }
	.block-filter.filter-ok.active { background: var(--color-success); border-color: var(--color-success); }
	.block-filter.filter-nok.active { background: var(--color-warning); border-color: var(--color-warning); }
	.block-filter.filter-changed.active { background: var(--color-info, #1976d2); border-color: var(--color-info, #1976d2); }

	/* Changed block state */
	.block-changed { background: color-mix(in srgb, var(--color-info, #1976d2) 6%, transparent); }
	.block-changed-badge {
		font-size: 9px;
		font-weight: var(--font-weight-medium);
		color: var(--color-info, #1976d2);
		background: color-mix(in srgb, var(--color-info, #1976d2) 12%, transparent);
		padding: 0 5px;
		border-radius: 3px;
		flex-shrink: 0;
	}

	/* Panel 3: Extracts */
	.extracts-body {
		padding: var(--space-3);
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}
	.extract-card {
		padding: var(--space-3);
		border: 1px solid var(--color-border-light);
		border-left: 3px solid var(--color-border);
		border-radius: var(--radius-sm);
		cursor: pointer;
		transition: box-shadow 0.1s, background 0.1s;
	}
	.extract-card:hover { box-shadow: var(--shadow-sm); }
	.extract-highlight {
		background: var(--color-finding-bg, #fff8e1);
		outline: 2px solid var(--color-warning);
		outline-offset: -2px;
	}
	.extract-header {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		margin-bottom: var(--space-1);
	}
	.extract-type-badge {
		font-size: 10px;
		font-weight: var(--font-weight-medium);
		color: white;
		padding: 1px 6px;
		border-radius: var(--radius-sm);
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}
	.extract-type-select {
		font-size: 10px;
		font-weight: var(--font-weight-medium);
		padding: 1px 4px;
		border-radius: var(--radius-sm);
		border: none;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		cursor: pointer;
		appearance: none;
		-webkit-appearance: none;
		font-family: var(--font-family);
	}
	.extract-type-select option {
		background: var(--color-surface);
		color: var(--color-text);
		text-transform: none;
	}
	.retype-indicator {
		font-size: 9px;
		color: var(--color-text-tertiary);
		font-style: italic;
	}
	.extract-actions {
		display: flex;
		gap: 2px;
		flex-shrink: 0;
		opacity: 0;
		transition: opacity 0.1s;
		margin-left: auto;
	}
	.extract-card:hover .extract-actions,
	.extract-card.block-ok .extract-actions,
	.extract-card.block-nok .extract-actions { opacity: 1; }
	.extract-claims-badge {
		display: inline-flex;
		align-items: center;
		gap: 2px;
		font-size: var(--font-size-xs);
		color: var(--color-claim);
		font-weight: var(--font-weight-medium);
		border: none;
		background: none;
		cursor: pointer;
		padding: 0;
		font-family: var(--font-family);
	}
	.extract-claims-badge:hover { opacity: 0.8; }
	.extract-claims-badge.expanded { opacity: 0.7; }
	.extract-section {
		font-size: 10px;
		color: var(--color-text-tertiary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		margin-left: auto;
	}
	.extract-text {
		font-size: var(--font-size-xs);
		line-height: var(--line-height-normal);
		color: var(--color-text);
		margin: 0;
	}

	/* Claim details (expanded from extract) */
	.claim-details {
		margin-top: var(--space-2);
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}
	.claim-card {
		padding: var(--space-2) var(--space-3);
		background: var(--color-background, #f8f8f7);
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border-light);
	}
	.claim-card-header {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		margin-bottom: var(--space-1);
	}
	.claim-id {
		font-size: 10px;
		font-weight: var(--font-weight-medium);
		color: var(--color-claim);
	}
	.claim-sources {
		font-size: 10px;
		color: var(--color-text-tertiary);
	}
	.claim-statement {
		font-size: var(--font-size-xs);
		line-height: var(--line-height-normal);
		color: var(--color-text-secondary);
		margin: 0;
	}
	.claim-finding {
		display: flex;
		align-items: center;
		gap: var(--space-1);
		margin-top: var(--space-1);
		font-size: 10px;
		color: var(--color-finding, var(--color-text-tertiary));
	}
	.finding-category {
		font-weight: var(--font-weight-medium);
		white-space: nowrap;
	}
	.finding-category::after { content: ' \2014 '; }
	.finding-title {
		color: var(--color-text-secondary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.has-claims { border-left-width: 4px; }

	/* List footer with export */
	.list-footer {
		display: flex;
		align-items: center;
		gap: var(--space-4);
		margin-top: var(--space-3);
	}
	.export-btn {
		display: inline-flex;
		align-items: center;
		gap: var(--space-1);
		padding: var(--space-1) var(--space-3);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-surface);
		font-family: var(--font-family);
		font-size: var(--font-size-xs);
		color: var(--color-text-secondary);
		cursor: pointer;
	}
	.export-btn:hover { color: var(--color-text); border-color: var(--color-text-secondary); }

	/* Empty state */
	.empty-state {
		text-align: center;
		padding: var(--space-8);
		color: var(--color-text-tertiary);
	}
</style>
