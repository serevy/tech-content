# tech-content

Technical articles, research notes, and public write-ups in Japanese and English.

This repository is the source of truth for public-facing technical content maintained by serevy.

## Content

- `articles/` — Japanese articles, currently connected to Zenn.
- `articles_en/` — English/localized drafts for overseas publishing.
- `images/` — Shared article images.
- `docs/records/` — Project Design Decision Records (PDDR) for durable publishing and editorial decisions.

## Publishing

Zenn is connected to the `main` branch. New Zenn articles start with `published: false`; publication requires an explicit approval before changing the flag to `true`.

The destination and automation for English publishing are intentionally not fixed yet.

## Writing guidance

Repository-specific authoring and review rules live in [AGENTS.md](AGENTS.md).

Japanese writing may use [coji/natural-japanese](https://github.com/coji/natural-japanese) as an editorial aid. It must not be used to invent or alter technical facts, evidence, quotations, code, URLs, or version numbers.

## PDDR

This repository uses [PDDR Kit](https://github.com/serevy/pddr-kit) for durable Project / Product / Process decisions.

Validate records with:

```bash
python .pddr/pddr.py validate
```
