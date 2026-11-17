# tech-content

[![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/serevy/tech-content?utm_source=oss&utm_medium=github&utm_campaign=serevy%2Ftech-content&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)](https://coderabbit.ai)

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

For Japanese articles, use the repository-pinned [yomiyasu](.agents/skills/yomiyasu/SKILL.md) v3.1.0 editorial skill, without stacking a second rewriting skill. It must not be used to invent or alter technical facts, evidence, quotations, code, URLs, or version numbers.

The bundled skill is from [nanaism/yomiyasu](https://github.com/nanaism/yomiyasu/tree/v3.1.0/skills/yomiyasu). Update the pinned copy and its version references together in a separate reviewed PR.

## PDDR

This repository uses [PDDR Kit](https://github.com/serevy/pddr-kit) for durable Project / Product / Process decisions.

Validate records with:

```bash
python .pddr/pddr.py validate
```
