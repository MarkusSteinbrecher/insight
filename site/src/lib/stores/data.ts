import { writable, derived } from 'svelte/store';
import type {
	TopicManifest,
	Stats,
	SourcesData,
	FindingsData,
	InsightsData,
	ConclusionsData,
	AuditData,
	GraphExportData,
	VisualsData
} from '$lib/types';

export const topicManifest = writable<TopicManifest | null>(null);
export const currentTopic = writable<string>('');
export const stats = writable<Stats | null>(null);
export const sourcesData = writable<SourcesData | null>(null);
export const findingsData = writable<FindingsData | null>(null);
export const insightsData = writable<InsightsData | null>(null);
export const conclusionsData = writable<ConclusionsData | null>(null);
export const auditData = writable<AuditData | null>(null);
export const graphData = writable<GraphExportData | null>(null);
export const visualsData = writable<VisualsData | null>(null);
export const searchQuery = writable('');
export const activeTab = writable('dashboard');
export const deepDiveSourceId = writable<string | null>(null);

const DATA_BASE = 'data';

async function fetchJson<T>(path: string): Promise<T | null> {
	try {
		const res = await fetch(`${DATA_BASE}/${path}`);
		if (!res.ok) return null;
		return await res.json();
	} catch {
		return null;
	}
}

export async function loadTopics(): Promise<void> {
	const manifest = await fetchJson<TopicManifest>('topics.json');
	if (manifest) {
		topicManifest.set(manifest);
		if (manifest.default_topic) {
			await selectTopic(manifest.default_topic);
		}
	}
}

export async function selectTopic(slug: string): Promise<void> {
	currentTopic.set(slug);

	const [s, src, f, i, c, a, g, v] = await Promise.all([
		fetchJson<Stats>(`${slug}/stats.json`),
		fetchJson<SourcesData>(`${slug}/sources.json`),
		fetchJson<FindingsData>(`${slug}/findings.json`),
		fetchJson<InsightsData>(`${slug}/insights.json`),
		fetchJson<ConclusionsData>(`${slug}/conclusions.json`),
		fetchJson<AuditData>(`${slug}/audit.json`),
		fetchJson<GraphExportData>(`${slug}/graph.json`),
		fetchJson<VisualsData>(`${slug}/visuals.json`)
	]);

	stats.set(s);
	sourcesData.set(src);
	findingsData.set(f);
	insightsData.set(i);
	conclusionsData.set(c);
	auditData.set(a);
	graphData.set(g);
	visualsData.set(v);
}

export const currentTopicTitle = derived(
	[topicManifest, currentTopic],
	([$manifest, $topic]) => {
		if (!$manifest) return '';
		const t = $manifest.topics.find((t) => t.slug === $topic);
		return t?.title ?? $topic;
	}
);
