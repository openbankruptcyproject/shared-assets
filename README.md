# BTN Shared Assets

Shared components and CI/CD automation for the Bankruptcy Transparency Network.

## Components
- `btn-engage.js` -- GA4 engagement tracking
- `favicon.svg` -- shared favicon
- `snippets/ga4-head.html` -- Google Analytics tags
- `snippets/footer.html` -- shared footer with BTN links
- `snippets/faq-schema.html` -- FAQ structured data template

## Workflows
- **propagate.yml** -- Push component updates to all 172 repos
- Manual trigger: Actions tab -> Propagate Shared Components -> Run workflow

## Setup
1. Run `scripts/inject_markers.py` to add markers to all sites (one-time)
2. Set `BTN_DEPLOY_TOKEN` secret (PAT with `contents:write` for all org repos)
3. Push changes to this repo -> auto-propagates to all sites
