---
name: llm-wiki
description: Build and maintain a persistent, interlinked markdown wiki (LLM Wiki pattern by nashsu/Karpathy) from raw sources. Use when asked to ingest a document/source into the wiki, query the knowledge base, lint/health-check the wiki, or set up a wiki for this workspace.
---

# LLM Wiki

Pattern source: https://github.com/nashsu/llm_wiki (full idea in `references/llm-wiki.md`, MIT license).

## Layout (default, create on first use)
```
wiki-vault/
  raw/        # immutable sources (never edit)
    assets/   # downloaded images
  wiki/       # LLM-owned markdown pages (entities, concepts, sources, synthesis)
    index.md  # catalog: link + one-line summary per page, by category
    log.md    # append-only: "## [YYYY-MM-DD] ingest|query|lint | Title"
  AGENTS.md   # schema: conventions + workflows for this vault
```
Open `wiki-vault/` as an Obsidian vault (see the `obsidian` skill). Ask the user before choosing a different location.

## Operations
- **Ingest**: read the source in `raw/`, discuss key takeaways, write a summary page in `wiki/`, update/create entity & concept pages, update `index.md`, append to `log.md`. A source may touch 10-15 pages. Flag contradictions with older claims.
- **Query**: read `index.md` first, drill into relevant pages, answer with `[[wikilink]]` citations. File valuable answers back as new pages.
- **Lint**: look for contradictions, stale claims, orphan pages, concepts without pages, missing cross-links, data gaps. Report, then fix with user approval.

## Page conventions
- YAML frontmatter: `title`, `type` (entity|concept|source|synthesis), `tags`, `sources`, `updated`.
- Use `[[wikilinks]]`; one topic per page; never modify `raw/`.
- Keep `index.md` and `log.md` updated on every operation.
