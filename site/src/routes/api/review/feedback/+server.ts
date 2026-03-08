export const prerender = false;

import { dev } from '$app/environment';
import { json, error } from '@sveltejs/kit';
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from 'fs';
import { resolve, join } from 'path';
import type { RequestHandler } from './$types';

function feedbackDir(topic: string): string {
	return resolve(`static/data/${topic}/review/feedback`);
}

function feedbackPath(topic: string, sourceShort: string): string {
	return join(feedbackDir(topic), `${sourceShort}.json`);
}

/**
 * GET /api/review/feedback?topic=ea-for-ai
 * Optional: &source=source-001 for a single source
 * Returns all feedback for a topic, or a single source's feedback.
 */
export const GET: RequestHandler = async ({ url }) => {
	if (!dev) throw error(403, 'Only available in dev mode');

	const topic = url.searchParams.get('topic');
	if (!topic) throw error(400, 'Missing topic parameter');

	const source = url.searchParams.get('source');

	if (source) {
		const path = feedbackPath(topic, source);
		if (!existsSync(path)) return json(null);
		return json(JSON.parse(readFileSync(path, 'utf-8')));
	}

	// Return all feedback files for the topic
	const dir = feedbackDir(topic);
	if (!existsSync(dir)) return json({});

	const result: Record<string, any> = {};
	for (const file of readdirSync(dir)) {
		if (!file.endsWith('.json')) continue;
		const key = file.replace('.json', '');
		result[key] = JSON.parse(readFileSync(join(dir, file), 'utf-8'));
	}
	return json(result);
};

/**
 * POST /api/review/feedback
 * Body: { topic, sourceId, source: { status, comment, blocks: { [blockId]: { status, comment } } } }
 * Status mapping: frontend ok/nok → stored as ok/rework
 */
export const POST: RequestHandler = async ({ request }) => {
	if (!dev) throw error(403, 'Only available in dev mode');

	const body = await request.json();
	const { topic, sourceId, source } = body as {
		topic: string;
		sourceId: string;
		source: {
			status: string;
			comment: string;
			blocks: Record<string, { status: string; comment: string; content_hash?: string }>;
			extracts: Record<string, { status: string; comment: string; retype?: string; content_hash?: string }>;
		};
	};

	if (!topic || !sourceId || !source) {
		throw error(400, 'Missing required fields: topic, sourceId, source');
	}

	const sourceShort = sourceId.split(':').pop();
	if (!sourceShort) throw error(400, 'Invalid sourceId');

	function mapEntries(entries: Record<string, any>) {
		return Object.fromEntries(
			Object.entries(entries)
				.filter(([, v]) => v.status || v.comment || v.retype)
				.map(([id, v]) => [
					id,
					{
						status: v.status === 'nok' ? 'rework' : v.status,
						comment: v.comment,
						...(v.retype ? { retype: v.retype } : {}),
						...(v.content_hash ? { content_hash: v.content_hash } : {})
					}
				])
		);
	}

	// Map frontend statuses to backend format
	const mapped = {
		status: source.status,
		comment: source.comment,
		blocks: mapEntries(source.blocks ?? {}),
		extracts: mapEntries(source.extracts ?? {}),
		updated: new Date().toISOString()
	};

	const dir = feedbackDir(topic);
	mkdirSync(dir, { recursive: true });
	writeFileSync(feedbackPath(topic, sourceShort), JSON.stringify(mapped, null, 2), 'utf-8');

	return json({ ok: true, source: sourceShort });
};
