# AGENTS.md — Carbone Notes

## Purpose
Maintain a lightweight static editorial website with accurate metadata and verifiable publication sources.

## Truth and content
- Do not invent sources, author identities, publication dates, quotes, or article facts.
- Keep the editorial identity **Carbone Notes** distinct from the technical maintainer **Sudomarc**.
- Mark template-only content as noindex; do not add templates or redirects to the sitemap.
- All canonical URLs must match the public base URL used by `generate.py` and `scripts/validate_site.py`.

## Workflow
- Work on a task branch and use a pull request; do not push directly to `main`.
- Preserve article metadata in `CARBONE_META` comments and keep RSS, archive, index, and sitemap consistent.
- Before merging, run `python -m py_compile generate.py scripts/validate_site.py` and `python scripts/validate_site.py`.
- The publishing workflow requires provider secrets. Never expose or fabricate them.
- Report test results, deployment state, and unverified public HTTP behavior explicitly.
