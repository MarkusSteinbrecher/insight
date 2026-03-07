export interface Topic {
	slug: string;
	title: string;
	phase: number;
	source_count: number;
}

export interface TopicManifest {
	topics: Topic[];
	default_topic: string;
}

export interface Stats {
	generated: string;
	sources: number;
	source_types: Record<string, number>;
	total_extracts: number;
	canonical_claims: number;
	unique_claims: number;
	contradictions: number;
}

export interface Source {
	id: string;
	title: string;
	url: string;
	author: string;
	date: string;
	type: string;
	extract_count: number;
	claim_count: number;
	finding_count: number;
}

export interface SourcesData {
	topic: string;
	updated: string;
	sources: Source[];
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

export interface FindingsData {
	generated: string;
	total_findings: number;
	total_claims_linked: number;
	findings: Finding[];
}

export interface Insight {
	id: string;
	theme: string;
	statement: string;
	source_count: number;
	ocaf: {
		value_score: number;
		value_category: string;
	};
	critique: string;
	practical_value: string;
	action_steps: string[];
	bottom_line: string;
	sources: ClaimSource[];
}

export interface InsightsData {
	generated: string;
	total_findings: number;
	total_contradictions: number;
	analyses: Insight[];
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

export interface ConclusionsData {
	generated: string;
	target_audience: string;
	total_recommendations: number;
	total_angles: number;
	actionability: Array<{
		finding_id: string;
		finding_title: string;
		actionability: string;
		barriers: string[];
		missing_for_action: string;
	}>;
	recommendations: Recommendation[];
	angles: Angle[];
}

/** Audit data for source quality inspection */
export interface AuditExtractClaim {
	claim_id: string;
	summary: string;
	theme: string;
	finding?: {
		finding_id: string;
		finding_title: string;
		category: string;
	};
}

export interface AuditExtract {
	id: string;
	text: string;
	position: number;
	section: string;
	format: string;
	extract_type: string;
	claims?: AuditExtractClaim[];
}

export interface AuditMarkdown {
	raw_markdown: string;
	sections: Array<{ heading: string; content: string }>;
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
	markdown: AuditMarkdown;
	extracts: AuditExtract[];
	extract_sections: Record<string, AuditExtract[]>;
}

export interface AuditData {
	topic: string;
	generated: string;
	total_sources: number;
	sources: AuditSource[];
}

/** Visual extraction data */
export interface Visual {
	id: string;
	visual_type: string;
	description: string;
	extracted_data: Array<Record<string, unknown>>;
	extraction_method: string;
	metadata: Record<string, unknown>;
	block_id: string;
	section_path: string;
	image_path: string;
	source_id: string;
	source_title: string;
	source_author: string;
	source_type: string;
	source_url: string;
}

export interface VisualsData {
	topic: string;
	generated: string;
	total_visuals: number;
	visual_types: string[];
	visuals: Visual[];
}

/** Graph node for D3 visualization */
export interface GraphNode {
	id: string;
	label: string;
	type: 'finding' | 'claim' | 'extract' | 'source';
	group: number;
	radius: number;
	author?: string;
	sourceType?: string;
	format?: string;
	extractType?: string;
	theme?: string;
	category?: string;
}

export interface GraphLink {
	source: string;
	target: string;
	type: string;
}

/** Graph export data from KuzuDB */
export interface GraphExportNode {
	id: string;
	label: string;
	text?: string;
	type: string;
	author?: string;
	sourceType?: string;
	format?: string;
	extractType?: string;
	theme?: string;
	category?: string;
}

export interface GraphExportEdge {
	source: string;
	target: string;
	type: string;
}

export interface GraphExportData {
	topic: string;
	generated: string;
	nodes: GraphExportNode[];
	edges: GraphExportEdge[];
	extract_formats: string[];
}
