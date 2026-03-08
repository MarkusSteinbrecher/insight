// Central reactive state using Svelte 5 runes (*.svelte.ts enables runes)

/** Extract short display ID from full ID, e.g. "ea-for-ai:source-001" → "S-001" */
export function shortId(id: string): string {
	const part = id.split(':').pop() ?? id;
	const m = part.match(/^(\w+?)-(\d+)$/);
	if (!m) return part;
	const prefixes: Record<string, string> = {
		source: 'S', finding: 'F', cc: 'C', extract: 'E'
	};
	return `${prefixes[m[1]] ?? m[1].charAt(0).toUpperCase()}-${m[2]}`;
}

interface Topic {
	slug: string;
	title: string;
	phase: number;
	source_count: number;
}

interface TopicManifest {
	topics: Topic[];
	default_topic: string;
}

export interface Source {
	id: string;
	title: string;
	url: string;
	author: string;
	date: string;
	type: string;
	status?: string;
	extract_count: number;
	claim_count: number;
	finding_count: number;
}

export interface ClaimSource {
	id: string;
	title: string;
	author: string;
	url: string;
	quotes: string[];
}

export interface Claim {
	id: string;
	statement: string;
	source_count: number;
	bottom_line: string;
	sources: ClaimSource[];
	baseline_category?: string;
}

export interface Finding {
	id: string;
	title: string;
	description: string;
	category: string;
	claim_count: number;
	claims: Claim[];
}

export interface Recommendation {
	id: string;
	title: string;
	description: string;
	priority: string;
	effort: string;
	dependencies: string[];
	related_findings: string[];
}

export interface Angle {
	id: string;
	title: string;
	position: string;
	why_novel: string;
	supporting_claims: string[];
	suggested_format: string;
}

export interface AuditExtract {
	id: string;
	text: string;
	position: number;
	section: string;
	format: string;
	extract_type: string;
	claims?: Array<{
		claim_id: string;
		summary: string;
		theme: string;
		finding?: { finding_id: string; finding_title: string; category: string };
	}>;
}

export interface AuditSource {
	id: string;
	title: string;
	author: string;
	date: string;
	type: string;
	url: string;
	embed_url: string;
	extract_count: number;
	metadata: Record<string, unknown>;
	markdown: { raw_markdown: string; sections: Array<{ heading: string; content: string }> };
	extracts: AuditExtract[];
	extract_sections: Record<string, AuditExtract[]>;
}

// All app state in one reactive object
function createAppState() {
	let manifest = $state<TopicManifest | null>(null);
	let currentSlug = $state('');
	let activeTab = $state('dashboard');
	let searchQuery = $state('');
	let stats = $state<any>(null);
	let sources = $state<{ topic: string; updated: string; sources: Source[] } | null>(null);
	let findings = $state<{ generated: string; total_findings: number; total_claims_linked: number; findings: Finding[] } | null>(null);
	let conclusions = $state<{ generated: string; target_audience: string; total_recommendations: number; total_angles: number; recommendations: Recommendation[]; angles: Angle[] } | null>(null);
	let audit = $state<{ topic: string; generated: string; total_sources: number; sources: AuditSource[] } | null>(null);
	let graph = $state<any>(null);
	let visuals = $state<any>(null);
	let deepDiveSourceId = $state<string | null>(null);

	let currentTitle = $derived(() => {
		if (!manifest) return '';
		const t = manifest.topics.find((t) => t.slug === currentSlug);
		return t?.title ?? currentSlug;
	});

	async function fetchJson<T>(path: string): Promise<T | null> {
		try {
			const res = await fetch(`data/${path}`);
			if (!res.ok) return null;
			return await res.json();
		} catch {
			return null;
		}
	}

	async function loadTopics() {
		manifest = await fetchJson<TopicManifest>('topics.json');
		if (manifest?.default_topic) {
			await selectTopic(manifest.default_topic);
		}
	}

	async function selectTopic(slug: string) {
		currentSlug = slug;
		const [s, src, f, c, a, g, v] = await Promise.all([
			fetchJson<any>(`${slug}/stats.json`),
			fetchJson<any>(`${slug}/sources.json`),
			fetchJson<any>(`${slug}/findings.json`),
			fetchJson<any>(`${slug}/conclusions.json`),
			fetchJson<any>(`${slug}/audit.json`),
			fetchJson<any>(`${slug}/graph.json`),
			fetchJson<any>(`${slug}/visuals.json`)
		]);
		stats = s;
		sources = src;
		findings = f;
		conclusions = c;
		audit = a;
		graph = g;
		visuals = v;
	}

	return {
		get manifest() { return manifest; },
		get currentSlug() { return currentSlug; },
		get currentTitle() { return currentTitle(); },
		get activeTab() { return activeTab; },
		set activeTab(v: string) { activeTab = v; },
		get searchQuery() { return searchQuery; },
		set searchQuery(v: string) { searchQuery = v; },
		get stats() { return stats; },
		get sources() { return sources; },
		get findings() { return findings; },
		get conclusions() { return conclusions; },
		get audit() { return audit; },
		get graph() { return graph; },
		get visuals() { return visuals; },
		get deepDiveSourceId() { return deepDiveSourceId; },
		set deepDiveSourceId(v: string | null) { deepDiveSourceId = v; },
		loadTopics,
		selectTopic
	};
}

export const app = createAppState();
