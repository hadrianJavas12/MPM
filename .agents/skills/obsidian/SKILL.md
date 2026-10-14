---
name: obsidian
description: Work with Obsidian vaults - create/edit notes in Obsidian-flavored markdown (wikilinks, frontmatter, embeds, callouts, tags), organize a vault, and advise on Obsidian Sync. Use when the user mentions Obsidian, a vault, wikilinks, or syncing notes.
---

# Obsidian

## Vault basics
- A vault is a plain folder of `.md` files; `.obsidian/` holds settings (do not edit unless asked).
- Pair with the `llm-wiki` skill for LLM-maintained knowledge bases.

## Obsidian-flavored markdown
- Links: `[[Note]]`, `[[Note|alias]]`, `[[Note#Heading]]`, `[[Note#^block-id]]`
- Embeds: `![[Note]]`, `![[image.png|400]]`
- Tags: `#tag` or frontmatter `tags: [a, b]`
- Frontmatter (properties) at top of file, YAML between `---`.
- Callouts: `> [!note] Title` (also tip, warning, info, ...)
- Math: `$inline$`, `$$block$$`; Mermaid in ```mermaid fences.

## Rules
- Prefer wikilinks over relative markdown links; filenames unique within the vault.
- Store attachments in a fixed folder (e.g. `raw/assets/`).
- Never delete or rename notes without telling the user (renames break links unless done in Obsidian).

## Obsidian Sync (https://obsidian.md/sync)
Paid first-party service configured **inside the Obsidian app** (Settings > Core plugins > Sync, log in, create/connect remote vault). It cannot be installed or configured from files. End-to-end encrypted, version history 1-12 months by plan. Free alternative: keep the vault in a git repo.
