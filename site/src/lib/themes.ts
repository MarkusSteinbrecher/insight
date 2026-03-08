// Shared theme definitions — used by layout (theme picker) and StyleGuide (editor)

export type Mode = 'light' | 'dark';
export type Colors = Record<string, string>;

export interface ThemeDef {
	id: string;
	name: string;
	icon: string;
	light: Colors;
	dark: Colors;
}

const STORAGE_KEY = 'insight-custom-themes';

/** Built-in defaults — never mutated */
export const defaultThemes: ThemeDef[] = [
	{ id: 'warm', name: 'Warm', icon: 'flame', light: {
		'--color-bg': '#F5F3EE', '--color-sidebar': '#F0ECE4', '--color-sidebar-hover': '#E8E3D9',
		'--color-sidebar-active': '#E0DAD0', '--color-surface': '#FFFFFF', '--color-surface-hover': '#F7F5F2',
		'--color-text': '#1B1B18', '--color-text-secondary': '#64635E', '--color-text-tertiary': '#9B9A95',
		'--color-border': '#E5E2DB', '--color-border-light': '#EDEAE4',
		'--color-primary': '#D97757', '--color-primary-hover': '#C4663F', '--color-primary-light': '#FAE6DD', '--color-primary-text': '#B34D2B',
		'--color-success': '#3D8B37', '--color-success-bg': '#E4F2E3',
		'--color-warning': '#C4841D', '--color-warning-bg': '#FEF3D7',
		'--color-error': '#C62828', '--color-error-bg': '#FDECEA',
		'--color-info': '#3B6EC4', '--color-info-bg': '#E3EDF8',
		'--color-source': '#C4841D', '--color-source-bg': '#FEF3D7',
		'--color-extract': '#7C6F9B', '--color-extract-bg': '#EEEBF5',
		'--color-claim': '#3B6EC4', '--color-claim-bg': '#E3EDF8',
		'--color-finding': '#D97757', '--color-finding-bg': '#FAE6DD',
		'--radius-sm': '0.5rem', '--radius-md': '0.75rem', '--radius-lg': '1rem', '--radius-full': '9999px',
	}, dark: {
		'--color-bg': '#1C1A17', '--color-sidebar': '#161412', '--color-sidebar-hover': '#2A2622',
		'--color-sidebar-active': '#3D3830', '--color-surface': '#252220', '--color-surface-hover': '#2E2B28',
		'--color-text': '#E8E4DE', '--color-text-secondary': '#A8A49C', '--color-text-tertiary': '#7A766E',
		'--color-border': '#3D3830', '--color-border-light': '#2E2B28',
		'--color-primary': '#E89070', '--color-primary-hover': '#F5A080', '--color-primary-light': '#3D2A1E', '--color-primary-text': '#F5B090',
		'--color-success': '#5CB858', '--color-success-bg': '#1E2E1C',
		'--color-warning': '#E0A040', '--color-warning-bg': '#2E2510',
		'--color-error': '#E05050', '--color-error-bg': '#2E1818',
		'--color-info': '#5B8ED8', '--color-info-bg': '#1A2436',
		'--color-source': '#E0A040', '--color-source-bg': '#2E2510',
		'--color-extract': '#9A8DBB', '--color-extract-bg': '#241E30',
		'--color-claim': '#5B8ED8', '--color-claim-bg': '#1A2436',
		'--color-finding': '#E89070', '--color-finding-bg': '#3D2A1E',
		'--radius-sm': '0.5rem', '--radius-md': '0.75rem', '--radius-lg': '1rem', '--radius-full': '9999px',
	}},
	{ id: 'cool', name: 'Cool', icon: 'sparkles', light: {
		'--color-bg': '#F8FAFC', '--color-sidebar': '#F1F5F9', '--color-sidebar-hover': '#E2E8F0',
		'--color-sidebar-active': '#CBD5E1', '--color-surface': '#FFFFFF', '--color-surface-hover': '#F8FAFC',
		'--color-text': '#0F172A', '--color-text-secondary': '#64748B', '--color-text-tertiary': '#94A3B8',
		'--color-border': '#E2E8F0', '--color-border-light': '#F1F5F9',
		'--color-primary': '#2563EB', '--color-primary-hover': '#1D4ED8', '--color-primary-light': '#EFF6FF', '--color-primary-text': '#1E40AF',
		'--color-success': '#16A34A', '--color-success-bg': '#F0FDF4',
		'--color-warning': '#CA8A04', '--color-warning-bg': '#FEFCE8',
		'--color-error': '#DC2626', '--color-error-bg': '#FEF2F2',
		'--color-info': '#2563EB', '--color-info-bg': '#EFF6FF',
		'--color-source': '#60A5FA', '--color-source-bg': '#EFF6FF',
		'--color-extract': '#1E40AF', '--color-extract-bg': '#DBEAFE',
		'--color-claim': '#2563EB', '--color-claim-bg': '#EFF6FF',
		'--color-finding': '#1E3A8A', '--color-finding-bg': '#DBEAFE',
		'--radius-sm': '0.5rem', '--radius-md': '0.75rem', '--radius-lg': '1rem', '--radius-full': '9999px',
	}, dark: {
		'--color-bg': '#0F172A', '--color-sidebar': '#0C1322', '--color-sidebar-hover': '#1E293B',
		'--color-sidebar-active': '#334155', '--color-surface': '#1E293B', '--color-surface-hover': '#283548',
		'--color-text': '#E2E8F0', '--color-text-secondary': '#94A3B8', '--color-text-tertiary': '#64748B',
		'--color-border': '#334155', '--color-border-light': '#1E293B',
		'--color-primary': '#60A5FA', '--color-primary-hover': '#93C5FD', '--color-primary-light': '#172136', '--color-primary-text': '#93C5FD',
		'--color-success': '#4ADE80', '--color-success-bg': '#052E16',
		'--color-warning': '#FBBF24', '--color-warning-bg': '#422006',
		'--color-error': '#F87171', '--color-error-bg': '#450A0A',
		'--color-info': '#60A5FA', '--color-info-bg': '#172136',
		'--color-source': '#93C5FD', '--color-source-bg': '#172136',
		'--color-extract': '#60A5FA', '--color-extract-bg': '#1E293B',
		'--color-claim': '#3B82F6', '--color-claim-bg': '#172136',
		'--color-finding': '#BFDBFE', '--color-finding-bg': '#1E293B',
		'--radius-sm': '0.5rem', '--radius-md': '0.75rem', '--radius-lg': '1rem', '--radius-full': '9999px',
	}},
	{ id: 'yello', name: 'Yello', icon: 'zap', light: {
		'--color-bg': '#FEFCE8', '--color-sidebar': '#FEF9C3', '--color-sidebar-hover': '#FDE047',
		'--color-sidebar-active': '#FACC15', '--color-surface': '#FFFFFF', '--color-surface-hover': '#FEFEF0',
		'--color-text': '#1A1700', '--color-text-secondary': '#716810', '--color-text-tertiary': '#A39E40',
		'--color-border': '#EAE070', '--color-border-light': '#FEF9C3',
		'--color-primary': '#EAB308', '--color-primary-hover': '#CA8A04', '--color-primary-light': '#FEF9C3', '--color-primary-text': '#854D0E',
		'--color-success': '#16A34A', '--color-success-bg': '#F0FDF4',
		'--color-warning': '#CA8A04', '--color-warning-bg': '#FEFCE8',
		'--color-error': '#DC2626', '--color-error-bg': '#FEF2F2',
		'--color-info': '#EAB308', '--color-info-bg': '#FEFCE8',
		'--color-source': '#FACC15', '--color-source-bg': '#FEFCE8',
		'--color-extract': '#A16207', '--color-extract-bg': '#FEF9C3',
		'--color-claim': '#EAB308', '--color-claim-bg': '#FEFCE8',
		'--color-finding': '#854D0E', '--color-finding-bg': '#FEF9C3',
		'--radius-sm': '0.5rem', '--radius-md': '0.75rem', '--radius-lg': '1rem', '--radius-full': '9999px',
	}, dark: {
		'--color-bg': '#18160A', '--color-sidebar': '#121006', '--color-sidebar-hover': '#2A2710',
		'--color-sidebar-active': '#3D3A18', '--color-surface': '#1E1C0E', '--color-surface-hover': '#262414',
		'--color-text': '#FEF9C3', '--color-text-secondary': '#E0D860', '--color-text-tertiary': '#8A8430',
		'--color-border': '#3D3A18', '--color-border-light': '#2A2710',
		'--color-primary': '#FACC15', '--color-primary-hover': '#FDE047', '--color-primary-light': '#2A2710', '--color-primary-text': '#FDE68A',
		'--color-success': '#4ADE80', '--color-success-bg': '#052E16',
		'--color-warning': '#FBBF24', '--color-warning-bg': '#422006',
		'--color-error': '#F87171', '--color-error-bg': '#450A0A',
		'--color-info': '#FACC15', '--color-info-bg': '#2A2710',
		'--color-source': '#FDE047', '--color-source-bg': '#2A2710',
		'--color-extract': '#FACC15', '--color-extract-bg': '#1E1C0E',
		'--color-claim': '#EAB308', '--color-claim-bg': '#2A2710',
		'--color-finding': '#FEF08A', '--color-finding-bg': '#1E1C0E',
		'--radius-sm': '0.5rem', '--radius-md': '0.75rem', '--radius-lg': '1rem', '--radius-full': '9999px',
	}},
];

/** All color token names */
export const colorTokens = Object.keys(defaultThemes[0].light);

/** Get active themes — custom overrides from localStorage, or defaults */
export function getThemes(): ThemeDef[] {
	if (typeof localStorage === 'undefined') return defaultThemes;
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) return defaultThemes;
		const custom = JSON.parse(raw) as ThemeDef[];
		if (Array.isArray(custom) && custom.length === defaultThemes.length) return custom;
	} catch { /* ignore */ }
	return defaultThemes;
}

/** Persist customised themes to localStorage */
export function saveCustomThemes(themes: ThemeDef[]) {
	localStorage.setItem(STORAGE_KEY, JSON.stringify(themes));
}

/** Discard customisations, revert to built-in defaults */
export function clearCustomThemes() {
	localStorage.removeItem(STORAGE_KEY);
}

/** Check whether any customisations exist */
export function hasCustomThemes(): boolean {
	if (typeof localStorage === 'undefined') return false;
	return localStorage.getItem(STORAGE_KEY) !== null;
}

/** Apply a theme's colors to the document */
export function applyTheme(themeIndex: number, mode: Mode) {
	const themes = getThemes();
	const colors = themes[themeIndex][mode];
	for (const [token, value] of Object.entries(colors)) {
		document.documentElement.style.setProperty(token, value);
	}
}
