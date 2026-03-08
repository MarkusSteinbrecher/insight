Build the site, commit all changes, and push to GitHub Pages.

Steps:
1. Run `cd /Users/markus/Code/Insight/site && npx vite build` to build the static site into `../docs`
2. Check `git status` for any changes (both site source and docs build output)
3. If there are changes, stage all relevant files:
   - `site/` — source changes
   - `docs/` — build output for GitHub Pages
   - `README.md`, `site/backlog.md`, `site/STYLEGUIDE.md` — if modified
   - Do NOT stage `.env`, `node_modules/`, `site/test-results/`, or files in `.gitignore`
4. Create a commit with a concise message summarizing the changes
5. Push to `origin main`
6. Report the commit hash and confirm the push succeeded
