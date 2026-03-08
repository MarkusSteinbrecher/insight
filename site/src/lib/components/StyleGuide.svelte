<script lang="ts">
	import { onMount } from 'svelte';
	import Icon from '$lib/components/Icon.svelte';
	import { defaultThemes, getThemes, saveCustomThemes, clearCustomThemes, colorTokens, applyTheme, type Mode, type Colors, type ThemeDef } from '$lib/themes';

	// Token group labels for the editor UI
	const tokenGroups = [
		{ label: 'Base', tokens: [
			{ token: '--color-bg', label: 'Background' },
			{ token: '--color-sidebar', label: 'Sidebar' },
			{ token: '--color-sidebar-hover', label: 'Sidebar Hover' },
			{ token: '--color-sidebar-active', label: 'Sidebar Active' },
			{ token: '--color-surface', label: 'Surface' },
			{ token: '--color-surface-hover', label: 'Surface Hover' },
			{ token: '--color-text', label: 'Text' },
			{ token: '--color-text-secondary', label: 'Text 2nd' },
			{ token: '--color-text-tertiary', label: 'Text 3rd' },
			{ token: '--color-border', label: 'Border' },
			{ token: '--color-border-light', label: 'Border Light' },
			{ token: '--color-primary', label: 'Primary' },
			{ token: '--color-primary-hover', label: 'Primary Hover' },
			{ token: '--color-primary-light', label: 'Primary Light' },
			{ token: '--color-primary-text', label: 'Primary Text' },
		]},
		{ label: 'Entities', tokens: [
			{ token: '--color-source', label: 'Source' },
			{ token: '--color-source-bg', label: 'Source BG' },
			{ token: '--color-extract', label: 'Extract' },
			{ token: '--color-extract-bg', label: 'Extract BG' },
			{ token: '--color-claim', label: 'Claim' },
			{ token: '--color-claim-bg', label: 'Claim BG' },
			{ token: '--color-finding', label: 'Finding' },
			{ token: '--color-finding-bg', label: 'Finding BG' },
		]},
		{ label: 'Semantic', tokens: [
			{ token: '--color-success', label: 'Success' },
			{ token: '--color-success-bg', label: 'Success BG' },
			{ token: '--color-warning', label: 'Warning' },
			{ token: '--color-warning-bg', label: 'Warning BG' },
			{ token: '--color-error', label: 'Error' },
			{ token: '--color-error-bg', label: 'Error BG' },
			{ token: '--color-info', label: 'Info' },
			{ token: '--color-info-bg', label: 'Info BG' },
		]},
	];

	const layoutTokens = [
		{ token: '--radius-sm', label: 'Small', desc: 'Buttons, inputs, stat cards, tags' },
		{ token: '--radius-md', label: 'Medium', desc: 'Tables, panels, cards, finding cards' },
		{ token: '--radius-lg', label: 'Large', desc: 'Modals, large containers' },
		{ token: '--radius-full', label: 'Circle', desc: 'Pills, badges, avatars' },
	];

	const allTokens = [...tokenGroups.flatMap(g => g.tokens), ...layoutTokens];

	// Load persisted custom themes, or fall back to defaults
	function loadThemes(): ThemeDef[] {
		return getThemes().map(t => ({ ...t, light: { ...t.light }, dark: { ...t.dark } }));
	}

	let themes = $state<ThemeDef[]>(loadThemes());

	let activeTheme = $state(0);
	let activeMode = $state<Mode>('light');
	// Which mode each column is showing (independent of active)
	let viewModes = $state<Mode[]>(['light', 'light', 'light']);
	let saveStatus = $state('');

	onMount(() => {
		// Restore from shared localStorage (same keys as layout)
		const savedPalette = localStorage.getItem('insight-palette');
		const savedMode = localStorage.getItem('insight-mode') as Mode | null;
		if (savedPalette !== null) {
			const idx = parseInt(savedPalette);
			if (idx >= 0 && idx < themes.length) activeTheme = idx;
		}
		if (savedMode === 'light' || savedMode === 'dark') activeMode = savedMode;
		viewModes[activeTheme] = activeMode;
	});

	function rgbToHex(val: string): string {
		if (val.startsWith('#')) return val.length === 4
			? '#' + val[1]+val[1]+val[2]+val[2]+val[3]+val[3]
			: val.toUpperCase();
		const m = val.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
		if (!m) return val;
		return '#' + [m[1], m[2], m[3]].map(n => parseInt(n).toString(16).padStart(2, '0')).join('').toUpperCase();
	}

	function getColors(themeIndex: number, mode: Mode): Colors {
		return themes[themeIndex][mode];
	}

	function activateTheme(themeIndex: number, mode: Mode) {
		activeTheme = themeIndex;
		activeMode = mode;
		localStorage.setItem('insight-palette', String(themeIndex));
		localStorage.setItem('insight-mode', mode);
		const colors = getColors(themeIndex, mode);
		for (const [token, value] of Object.entries(colors)) {
			document.documentElement.style.setProperty(token, value);
		}
	}

	function updateColor(themeIndex: number, mode: Mode, token: string, value: string) {
		themes[themeIndex][mode][token] = token.startsWith('--color') ? value.toUpperCase() : value;
		themes = [...themes];
		// Persist all themes to localStorage
		saveCustomThemes(themes);
		// Apply live if this is the active theme+mode
		if (themeIndex === activeTheme && mode === activeMode) {
			document.documentElement.style.setProperty(token, value);
		}
	}

	function resetAll() {
		// Clear custom themes, revert to built-in defaults
		clearCustomThemes();
		themes = defaultThemes.map(t => ({ ...t, light: { ...t.light }, dark: { ...t.dark } }));
		activeTheme = 0;
		activeMode = 'light';
		viewModes = ['light', 'light', 'light'];
		localStorage.setItem('insight-palette', '0');
		localStorage.setItem('insight-mode', 'light');
		applyTheme(0, 'light');
		saveStatus = 'Restored to defaults';
	}

	async function saveActiveTheme() {
		const colors = getColors(activeTheme, activeMode);
		saveStatus = 'Saving...';
		try {
			const res = await fetch('/api/tokens', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ tokens: colors }),
			});
			const data = await res.json();
			if (data.ok) {
				localStorage.setItem('insight-palette', String(activeTheme));
				localStorage.setItem('insight-mode', activeMode);
				saveStatus = `Saved "${themes[activeTheme].name} ${activeMode}" to tokens.css`;
			} else {
				saveStatus = 'Save failed';
			}
		} catch {
			saveStatus = 'Save failed';
		}
	}

	// Reference data
	const sections = [
		{ id: 'sg-themes', label: 'Themes' },
		{ id: 'sg-preview', label: 'Preview' },
		{ id: 'sg-icons', label: 'Icons' },
		{ id: 'sg-components', label: 'Components' },
	];

	const iconNames = [
		'dashboard', 'sources', 'findings', 'graph', 'visuals', 'conclusions',
		'deep-dive', 'search', 'sidebar', 'chevron-down', 'chevron-right',
		'external', 'filter', 'x', 'arrow-up', 'arrow-down', 'info',
		'extract', 'claim', 'source', 'contradiction',
		'zap', 'flame', 'rocket', 'sparkles', 'sun', 'moon',
	];

	const badgeVariants = [
		{ cls: 'badge-primary', label: 'Primary' },
		{ cls: 'badge-success', label: 'Success' },
		{ cls: 'badge-warning', label: 'Warning' },
		{ cls: 'badge-info', label: 'Info' },
		{ cls: 'badge-source', label: 'Source' },
		{ cls: 'badge-extract', label: 'Extract' },
		{ cls: 'badge-claim', label: 'Claim' },
		{ cls: 'badge-finding', label: 'Finding' },
	];
</script>

<div class="sg">
	<!-- Sticky toolbar -->
	<div class="sg-nav-wrap">
		<nav class="sg-nav">
			{#each sections as s}
				<a href="#{s.id}" class="sg-nav-link">{s.label}</a>
			{/each}
			<span class="sg-nav-spacer"></span>
			<span class="sg-active-label">{themes[activeTheme].name} / {activeMode}</span>
			<button class="sg-action-btn sg-save-btn" onclick={saveActiveTheme}>Save</button>
			<button class="sg-action-btn sg-reset-btn" onclick={resetAll}>Reset</button>
			{#if saveStatus}
				<span class="sg-save-status">{saveStatus}</span>
			{/if}
		</nav>
	</div>

	<!-- Three theme columns -->
	<section id="sg-themes" class="sg-section">
		<h2 class="sg-title">Color Themes</h2>

		<div class="sg-themes-grid">
			{#each themes as theme, ti}
				{@const mode = viewModes[ti]}
				{@const isActive = ti === activeTheme && mode === activeMode}
				{@const colors = getColors(ti, mode)}
				<div class="sg-theme-col" class:active={isActive}>
					<!-- Theme header -->
					<div class="sg-theme-header">
						<input
							class="sg-theme-name"
							type="text"
							value={theme.name}
							onchange={(e) => { themes[ti].name = e.currentTarget.value; themes = [...themes]; }}
						/>
						{#if isActive}
							<span class="sg-active-badge">Active</span>
						{:else}
							<button class="sg-activate-btn" onclick={() => activateTheme(ti, mode)}>Activate</button>
						{/if}
					</div>

					<!-- Light / Dark toggle -->
					<div class="sg-mode-toggle">
						<button
							class="sg-mode-btn"
							class:selected={mode === 'light'}
							onclick={() => { viewModes[ti] = 'light'; viewModes = [...viewModes]; }}
						>
							<Icon name="visuals" size={14} />
							Light
						</button>
						<button
							class="sg-mode-btn"
							class:selected={mode === 'dark'}
							onclick={() => { viewModes[ti] = 'dark'; viewModes = [...viewModes]; }}
						>
							<Icon name="deep-dive" size={14} />
							Dark
						</button>
					</div>

					<!-- Mini preview -->
					<div class="sg-theme-preview" style="background: {colors['--color-bg']}">
						<div class="sg-pv-sidebar" style="background: {colors['--color-sidebar']}">
							<div class="sg-pv-dot" style="background: {colors['--color-primary']}"></div>
							<div class="sg-pv-dot" style="background: {colors['--color-text-tertiary']}"></div>
							<div class="sg-pv-dot" style="background: {colors['--color-text-tertiary']}"></div>
						</div>
						<div class="sg-pv-main">
							<div class="sg-pv-topbar" style="border-color: {colors['--color-border-light']}">
								<div class="sg-pv-text" style="background: {colors['--color-text']}"></div>
							</div>
							<div class="sg-pv-body">
								<div class="sg-pv-card" style="background: {colors['--color-surface']}; border-color: {colors['--color-border-light']}">
									<div class="sg-pv-line" style="background: {colors['--color-text-secondary']}"></div>
									<div class="sg-pv-line short" style="background: {colors['--color-text-tertiary']}"></div>
								</div>
								<div class="sg-pv-card" style="background: {colors['--color-surface']}; border-color: {colors['--color-border-light']}">
									<div class="sg-pv-line" style="background: {colors['--color-text-secondary']}"></div>
									<div class="sg-pv-line short" style="background: {colors['--color-text-tertiary']}"></div>
								</div>
							</div>
						</div>
					</div>

					<!-- Entity color bar -->
					<div class="sg-entity-bar">
						{#each ['--color-source', '--color-extract', '--color-claim', '--color-finding'] as tok}
							<div class="sg-entity-dot" style="background: {colors[tok]}" title={tok}></div>
						{/each}
						<div class="sg-entity-dot" style="background: {colors['--color-primary']}" title="primary"></div>
						<div class="sg-entity-dot" style="background: {colors['--color-success']}" title="success"></div>
						<div class="sg-entity-dot" style="background: {colors['--color-warning']}" title="warning"></div>
						<div class="sg-entity-dot" style="background: {colors['--color-error']}" title="error"></div>
					</div>

					<!-- Color groups -->
					{#each tokenGroups as group}
						<div class="sg-group-label">{group.label}</div>
						<div class="sg-swatch-grid">
							{#each group.tokens as t}
								<div class="sg-swatch-row">
									<label class="sg-swatch" style="background: {colors[t.token]}" title="{t.label}: {colors[t.token]}">
										<input
											type="color"
											value={colors[t.token]}
											oninput={(e) => updateColor(ti, mode, t.token, e.currentTarget.value)}
										/>
									</label>
									<div class="sg-swatch-info">
										<span class="sg-swatch-label">{t.label}</span>
										<input
											class="sg-swatch-hex"
											type="text"
											value={colors[t.token]}
											onchange={(e) => { const v = e.currentTarget.value; if (/^#[0-9a-fA-F]{6}$/i.test(v)) updateColor(ti, mode, t.token, v); }}
										/>
									</div>
								</div>
							{/each}
						</div>
					{/each}
					<div class="sg-group-label">Corners</div>
					<div class="sg-layout-grid">
						{#each layoutTokens as t}
							{@const val = colors[t.token] ?? '0'}
							{@const num = parseFloat(val)}
							{@const isFull = val === '9999px'}
							<div class="sg-layout-row">
								<span class="sg-layout-label">{t.label}</span>
								{#if t.token === '--radius-full'}
									<span class="sg-layout-value">circle</span>
								{:else}
									<input
										class="sg-layout-range"
										type="range"
										min="0"
										max="2"
										step="0.125"
										value={num}
										oninput={(e) => updateColor(ti, mode, t.token, e.currentTarget.value + 'rem')}
									/>
									<span class="sg-layout-value">{num}rem</span>
								{/if}
								<div class="sg-layout-preview" style="border-radius: {isFull ? '50%' : colors[t.token]};"></div>
							</div>
							<div class="sg-layout-desc">{t.desc}</div>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	</section>

	<!-- Live preview -->
	<section id="sg-preview" class="sg-section">
		<h2 class="sg-title">Preview</h2>

		<h3 class="sg-subtitle">Typography</h3>
		<div class="sg-type-specimen">Inter — The quick brown fox jumps over the lazy dog</div>
		<div class="sg-type-conventions">
			<div><span class="sg-conv-label">Page title</span> <span style="font-size: var(--font-size-xl); font-weight: var(--font-weight-semibold)">Enterprise Architecture for AI</span></div>
			<div><span class="sg-conv-label">Section</span> <span style="font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold)">Key Findings</span></div>
			<div><span class="sg-conv-label">Header</span> <span style="font-size: var(--font-size-xs); font-weight: var(--font-weight-semibold); text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-tertiary)">COLUMN HEADER</span></div>
			<div><span class="sg-conv-label">Body</span> <span style="font-size: var(--font-size-sm); color: var(--color-text-secondary)">Multiple sources converge on a fundamental shift in enterprise architecture.</span></div>
			<div><span class="sg-conv-label">Caption</span> <span style="font-size: var(--font-size-xs); color: var(--color-text-tertiary)">61 sources &middot; Updated 2026-03-08</span></div>
		</div>

		<h3 class="sg-subtitle">Shadows</h3>
		<div class="sg-shadow-grid">
			<div class="sg-shadow-card" style="box-shadow: var(--shadow-sm)"><strong>Small</strong><code>--shadow-sm</code></div>
			<div class="sg-shadow-card" style="box-shadow: var(--shadow-md)"><strong>Medium</strong><code>--shadow-md</code></div>
			<div class="sg-shadow-card" style="box-shadow: var(--shadow-lg)"><strong>Large</strong><code>--shadow-lg</code></div>
		</div>
	</section>

	<!-- Icons -->
	<section id="sg-icons" class="sg-section">
		<h2 class="sg-title">Icons</h2>
		<div class="sg-icon-grid">
			{#each iconNames as name}
				<div class="sg-icon-cell">
					<Icon {name} size={24} />
					<span>{name}</span>
				</div>
			{/each}
		</div>
	</section>

	<!-- Components -->
	<section id="sg-components" class="sg-section">
		<h2 class="sg-title">Components</h2>

		<h3 class="sg-subtitle">Badges</h3>
		<div class="sg-row">
			{#each badgeVariants as b}
				<span class="badge {b.cls}">{b.label}</span>
			{/each}
		</div>

		<h3 class="sg-subtitle">Category Pills</h3>
		<div class="sg-row">
			<button class="cat-pill active">All <span class="cat-count">15</span></button>
			<button class="cat-pill">Architecture <span class="cat-count">4</span></button>
			<button class="cat-pill">Governance <span class="cat-count">3</span></button>
		</div>

		<h3 class="sg-subtitle">Table</h3>
		<div class="table-wrap">
			<table>
				<thead><tr><th>ID</th><th>Title</th><th>Type</th><th style="text-align:center">Extracts</th></tr></thead>
				<tbody>
					<tr>
						<td style="color: var(--color-text-secondary)">S-001</td>
						<td><a href="#sg-components">Example Source <Icon name="external" size={11} /></a></td>
						<td><span class="badge badge-info">web</span></td>
						<td style="text-align:center">276</td>
					</tr>
					<tr>
						<td style="color: var(--color-text-secondary)">S-002</td>
						<td>Another Source</td>
						<td><span class="badge badge-warning">pdf</span></td>
						<td style="text-align:center">58</td>
					</tr>
				</tbody>
			</table>
		</div>

		<h3 class="sg-subtitle">Form Elements</h3>
		<div class="sg-row" style="gap: var(--space-6)">
			<div class="sg-form-item">
				<label>Text Input</label>
				<input type="text" placeholder="Search..." />
			</div>
			<div class="sg-form-item">
				<label>Select</label>
				<select><option>All types (61)</option><option>web</option><option>pdf</option></select>
			</div>
		</div>
	</section>
</div>

<style>
	.sg { max-width: 100%; }

	/* Sticky nav */
	.sg-nav-wrap {
		position: sticky;
		top: 0;
		z-index: 10;
		background: var(--color-bg);
		padding: var(--space-3) 0;
		margin-bottom: var(--space-6);
		border-bottom: 1px solid var(--color-border-light);
	}
	.sg-nav {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-1) var(--space-2);
		align-items: center;
	}
	.sg-nav-link {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		padding: var(--space-1) var(--space-3);
		border-radius: var(--radius-full);
		border: 1px solid var(--color-border-light);
		color: var(--color-text-secondary);
		text-decoration: none;
		transition: all 0.15s;
	}
	.sg-nav-link:hover { border-color: var(--color-border); color: var(--color-text); text-decoration: none; }
	.sg-nav-spacer { flex: 1; }
	.sg-active-label {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		font-weight: var(--font-weight-medium);
	}
	.sg-action-btn {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		font-family: var(--font-family);
		padding: var(--space-1) var(--space-3);
		border-radius: var(--radius-full);
		border: 1px solid var(--color-border);
		background: var(--color-surface);
		color: var(--color-text-secondary);
		cursor: pointer;
	}
	.sg-action-btn:hover { border-color: var(--color-text-tertiary); color: var(--color-text); }
	.sg-save-btn { background: var(--color-text); border-color: var(--color-text); color: var(--color-surface); }
	.sg-save-btn:hover { opacity: 0.85; background: var(--color-text); color: var(--color-surface); }
	.sg-reset-btn { border-color: var(--color-border); background: var(--color-surface); color: var(--color-text-secondary); }
	.sg-reset-btn:hover { background: var(--color-error-bg); border-color: var(--color-error); color: var(--color-error); }
	.sg-save-status { font-size: var(--font-size-xs); color: var(--color-success); }

	/* Sections */
	.sg-section { margin-bottom: var(--space-12); scroll-margin-top: 80px; }
	.sg-title {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-semibold);
		margin-bottom: var(--space-5);
		padding-bottom: var(--space-3);
		border-bottom: 1px solid var(--color-border-light);
	}
	.sg-subtitle {
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-top: var(--space-6);
		margin-bottom: var(--space-3);
	}
	.sg-row { display: flex; flex-wrap: wrap; gap: var(--space-3); align-items: center; }

	/* === Three-column theme grid === */
	.sg-themes-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--space-4);
	}
	.sg-theme-col {
		border: 2px solid var(--color-border-light);
		border-radius: var(--radius-md);
		padding: var(--space-4);
		background: var(--color-surface);
		transition: border-color 0.2s;
	}
	.sg-theme-col.active {
		border-color: var(--color-primary);
		box-shadow: 0 0 0 1px var(--color-primary);
	}

	/* Theme header */
	.sg-theme-header {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		margin-bottom: var(--space-3);
	}
	.sg-theme-name {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		font-family: var(--font-family);
		border: none;
		background: none;
		color: var(--color-text);
		padding: 0;
		flex: 1;
		min-width: 0;
		outline: none;
		border-bottom: 1px solid transparent;
	}
	.sg-theme-name:hover { border-bottom-color: var(--color-border); }
	.sg-theme-name:focus { border-bottom-color: var(--color-primary); }
	.sg-active-badge {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-semibold);
		padding: 2px var(--space-2);
		border-radius: var(--radius-full);
		background: var(--color-primary);
		color: white;
		white-space: nowrap;
	}
	.sg-activate-btn {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		font-family: var(--font-family);
		padding: 2px var(--space-2);
		border-radius: var(--radius-full);
		border: 1px solid var(--color-border);
		background: none;
		color: var(--color-text-secondary);
		cursor: pointer;
		white-space: nowrap;
	}
	.sg-activate-btn:hover { border-color: var(--color-primary); color: var(--color-primary); }

	/* Light/Dark toggle */
	.sg-mode-toggle {
		display: flex;
		gap: 1px;
		background: var(--color-border-light);
		border-radius: var(--radius-sm);
		overflow: hidden;
		margin-bottom: var(--space-3);
	}
	.sg-mode-btn {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-1);
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		font-family: var(--font-family);
		padding: var(--space-1) var(--space-2);
		border: none;
		background: var(--color-surface);
		color: var(--color-text-tertiary);
		cursor: pointer;
		transition: all 0.15s;
	}
	.sg-mode-btn:hover { color: var(--color-text-secondary); }
	.sg-mode-btn.selected {
		background: var(--color-text);
		color: var(--color-surface);
	}

	/* Mini preview */
	.sg-theme-preview {
		display: flex;
		height: 72px;
		border-radius: var(--radius-sm);
		overflow: hidden;
		border: 1px solid var(--color-border-light);
		margin-bottom: var(--space-3);
	}
	.sg-pv-sidebar {
		width: 24px;
		padding: 6px 4px;
		display: flex;
		flex-direction: column;
		gap: 3px;
		flex-shrink: 0;
	}
	.sg-pv-dot {
		width: 16px;
		height: 3px;
		border-radius: 1px;
	}
	.sg-pv-main { flex: 1; display: flex; flex-direction: column; }
	.sg-pv-topbar {
		height: 12px;
		border-bottom: 1px solid;
		padding: 3px 6px;
		display: flex;
		align-items: center;
	}
	.sg-pv-text { width: 30px; height: 3px; border-radius: 1px; }
	.sg-pv-body {
		flex: 1;
		padding: 4px 6px;
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.sg-pv-card {
		flex: 1;
		border-radius: 2px;
		border: 1px solid;
		padding: 3px 5px;
		display: flex;
		flex-direction: column;
		gap: 2px;
		justify-content: center;
	}
	.sg-pv-line { height: 2px; border-radius: 1px; width: 75%; }
	.sg-pv-line.short { width: 45%; }

	/* Entity color bar */
	.sg-entity-bar {
		display: flex;
		gap: 4px;
		margin-bottom: var(--space-3);
		padding: var(--space-1) 0;
	}
	.sg-entity-dot {
		flex: 1;
		height: 6px;
		border-radius: 3px;
	}

	/* Color group label */
	.sg-group-label {
		font-size: 10px;
		font-weight: var(--font-weight-semibold);
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--color-text-tertiary);
		margin-top: var(--space-3);
		margin-bottom: var(--space-1);
	}

	/* Swatch rows */
	.sg-swatch-grid {
		display: flex;
		flex-direction: column;
		gap: 1px;
		background: var(--color-border-light);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-sm);
		overflow: hidden;
	}
	.sg-swatch-row {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: 3px var(--space-2);
		background: var(--color-bg);
	}
	.sg-swatch {
		width: 20px;
		height: 20px;
		border-radius: 4px;
		border: 1px solid rgba(0,0,0,0.08);
		cursor: pointer;
		flex-shrink: 0;
		position: relative;
		overflow: hidden;
	}
	.sg-swatch input[type="color"] {
		position: absolute;
		inset: -4px;
		width: calc(100% + 8px);
		height: calc(100% + 8px);
		opacity: 0;
		cursor: pointer;
		border: none;
		padding: 0;
	}
	.sg-swatch-info {
		flex: 1;
		display: flex;
		align-items: center;
		gap: var(--space-1);
		min-width: 0;
	}
	.sg-swatch-label {
		font-size: 11px;
		color: var(--color-text-secondary);
		flex: 1;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.sg-swatch-hex {
		width: 62px;
		font-family: 'SF Mono', 'Fira Code', monospace;
		font-size: 10px;
		text-align: center;
		padding: 1px 3px;
		border: 1px solid transparent;
		border-radius: 3px;
		background: none;
		color: var(--color-text-tertiary);
		flex-shrink: 0;
	}
	.sg-swatch-hex:hover { border-color: var(--color-border); }
	.sg-swatch-hex:focus { border-color: var(--color-primary); color: var(--color-text); outline: none; }

	/* Layout tokens */
	.sg-layout-grid {
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}
	.sg-layout-row {
		display: flex;
		align-items: center;
		gap: var(--space-2);
	}
	.sg-layout-label {
		font-size: var(--font-size-xs);
		color: var(--color-text-secondary);
		width: 72px;
		flex-shrink: 0;
	}
	.sg-layout-range {
		flex: 1;
		height: 4px;
		accent-color: var(--color-primary);
		cursor: pointer;
	}
	.sg-layout-value {
		font-size: var(--font-size-xs);
		color: var(--color-text-tertiary);
		min-width: 44px;
		text-align: right;
	}
	.sg-layout-preview {
		width: 28px;
		height: 28px;
		background: var(--color-primary);
		flex-shrink: 0;
		transition: border-radius 0.15s ease;
	}
	.sg-layout-desc {
		font-size: 10px;
		color: var(--color-text-tertiary);
		padding-left: 74px;
		margin-top: -2px;
		margin-bottom: var(--space-1);
	}

	/* === Preview section === */
	.sg-type-specimen {
		padding: var(--space-5);
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		margin-bottom: var(--space-5);
		font-size: var(--font-size-lg);
	}
	.sg-type-conventions {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
		padding: var(--space-5);
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
	}
	.sg-type-conventions > div { display: flex; align-items: baseline; gap: var(--space-4); }
	.sg-conv-label {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-tertiary);
		min-width: 80px;
		flex-shrink: 0;
	}

	/* Shadows */
	.sg-shadow-grid { display: flex; gap: var(--space-6); flex-wrap: wrap; }
	.sg-shadow-card {
		width: 180px;
		padding: var(--space-5);
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md);
		display: flex;
		flex-direction: column;
		gap: var(--space-1);
	}
	.sg-shadow-card strong { font-size: var(--font-size-sm); }
	.sg-shadow-card code { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

	/* Icons */
	.sg-icon-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); gap: var(--space-3); }
	.sg-icon-cell {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-3);
		background: var(--color-surface);
		border: 1px solid var(--color-border-light);
		border-radius: var(--radius-sm);
		transition: box-shadow 0.15s;
	}
	.sg-icon-cell:hover { box-shadow: var(--shadow-md); }
	.sg-icon-cell span { font-size: 10px; color: var(--color-text-tertiary); text-align: center; }

	/* Pills */
	.cat-pill {
		display: inline-flex; align-items: center; gap: var(--space-1);
		padding: var(--space-1) var(--space-3); border-radius: var(--radius-full, 9999px);
		border: 1px solid var(--color-border-light); background: var(--color-surface);
		font-size: var(--font-size-sm); font-family: var(--font-family);
		color: var(--color-text-secondary); cursor: pointer; transition: all 0.15s;
	}
	.cat-pill:hover { border-color: var(--color-border); color: var(--color-text); }
	.cat-pill.active { background: var(--color-text); border-color: var(--color-text); color: var(--color-surface); font-weight: var(--font-weight-medium); }
	.cat-count { font-size: var(--font-size-xs); opacity: 0.7; }

	/* Tables */
	.table-wrap {
		background: var(--color-surface); border: 1px solid var(--color-border-light);
		border-radius: var(--radius-md); box-shadow: var(--shadow-sm); overflow-x: auto;
	}

	/* Forms */
	.sg-form-item { display: flex; flex-direction: column; gap: var(--space-2); }
	.sg-form-item label {
		font-size: var(--font-size-xs); font-weight: var(--font-weight-semibold);
		text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-tertiary);
	}
</style>
