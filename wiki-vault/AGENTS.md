# Wiki Schema

Follow the llm-wiki and obsidian skills (.agents/skills).

- raw/ is immutable; wiki/ is LLM-owned.
- Pages use YAML frontmatter (title, type, tags, sources, updated) and [[wikilinks]].
- On every ingest/query/lint: update wiki/index.md and append to wiki/log.md as '## [YYYY-MM-DD] op | Title'.
- Domain: cl-mpm (Material Point Method, Common Lisp) project knowledge.

