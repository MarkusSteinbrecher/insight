Build the site, update documentation, commit all changes, and push to GitHub Pages.

Steps:

1. **Update documentation** — Review what changed this session and update:
   - `README.md` — if new features, pages, or architectural changes were made
   - `site/backlog.md` — mark completed items as `[x]`, add any new issues or improvements discovered, remove stale entries
   - `site/STYLEGUIDE.md` — if design tokens, components, or conventions changed
   - Only update files where the content is actually outdated; don't touch docs that are already current

2. **Build the site** — Run `cd /Users/markus/Code/Insight/site && npx vite build` to generate static output into `../docs`

3. **Check git status** — Review all staged and unstaged changes (source + docs + documentation)

4. **Stage relevant files**:
   - `site/src/` — component and logic changes
   - `site/static/data/` — updated data files
   - `docs/` — build output for GitHub Pages
   - `README.md`, `site/backlog.md`, `site/STYLEGUIDE.md` — documentation updates
   - `.claude/commands/` — if commands were added or changed
   - Do NOT stage `.env`, `node_modules/`, `site/test-results/`, or files matched by `.gitignore`

5. **Commit** with a concise message summarizing both code and documentation changes

6. **Push** to `origin main`

7. **Report** the commit hash and confirm the push succeeded
