export const prerender = false;

import { dev } from '$app/environment';
import { json, error } from '@sveltejs/kit';
import { readFileSync, writeFileSync } from 'fs';
import { resolve } from 'path';
import type { RequestHandler } from './$types';

const TOKENS_PATH = resolve('src/lib/css/tokens.css');

export const POST: RequestHandler = async ({ request }) => {
	if (!dev) {
		throw error(403, 'Only available in dev mode');
	}

	const { tokens } = await request.json() as { tokens: Record<string, string> };

	if (!tokens || typeof tokens !== 'object') {
		throw error(400, 'Invalid tokens');
	}

	let css = readFileSync(TOKENS_PATH, 'utf-8');

	for (const [token, value] of Object.entries(tokens)) {
		// Match the token line in :root { ... } and replace its value
		const regex = new RegExp(`(${escapeRegex(token)}:\\s*)([^;]+)(;)`);
		if (regex.test(css)) {
			css = css.replace(regex, `$1${value}$3`);
		}
	}

	writeFileSync(TOKENS_PATH, css, 'utf-8');

	return json({ ok: true, updated: Object.keys(tokens).length });
};

function escapeRegex(s: string): string {
	return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
