---
id: PDDR-0001
title: GitHub-backed multilingual publishing workflow
decision_date: 2026-09-29
recorded_date: 2026-09-29
decision_status: accepted
delivery_status: in-progress
scope:
  - project
  - process
owners:
  - serevy
evidence:
  - README.md
  - AGENTS.md
  - articles/pddr-kit-ai-decision-memory.md
related: []
supersedes: []
superseded_by: null
---

# PDDR-0001: GitHub-backed multilingual publishing workflow

## Summary

技術記事と研究解説の原稿は、特定の投稿サービス専用リポジトリではなく `serevy/tech-content` を正本として管理する。日本語記事は `articles/` からZennへ連携し、英語版は `articles_en/` で英語圏向けにローカライズする。英語版の最終配信先と自動公開フローは、実運用前に別途決定する。

日本語の執筆・推敲では `natural-japanese` を編集支援として利用できるが、技術的事実、Evidence、引用、コードを変更する根拠としては扱わない。

## Context and observations

当初はZenn専用の `zenn-content` リポジトリ案を検討した。しかし、PDDR KitのようなOSS解説だけでなく、将来は研究寄りのプロジェクトや英語圏向けの解説も継続して公開する想定がある。

投稿先ごとに原稿リポジトリを分けると、同じテーマの日英版や画像、更新履歴が分散する。一方、GitHubを正本にすると、記事の変更履歴とレビューを残したまま媒体ごとの公開形式へ変換できる。

2026-09-29時点で `serevy/tech-content` は作成済みで、Zenn側では `main` ブランチをデプロイ対象としてGitHub連携が設定されている。PRからのZenn下書きデプロイはこの判断時点では有効化されていない。

## Options considered

### Zenn専用リポジトリ

- Description: `zenn-content` のようなZennだけを対象にしたリポジトリを作る。
- Benefits: Zenn CLIやディレクトリ構成と1対1で対応し、目的が明確。
- Costs / constraints: 英語版や別媒体の原稿管理が分散する。
- Status: rejected

### 媒体中立の共通リポジトリ

- Description: `tech-content` を原稿の正本とし、日本語・英語・画像・公開方針を同じGit履歴で管理する。
- Benefits: 日英の記事と根拠をまとめて管理でき、将来の媒体追加にも対応しやすい。
- Costs / constraints: 媒体固有のfront matterや公開処理は分けて管理する必要がある。
- Status: accepted

### 媒体ごとに別リポジトリ

- Description: Zenn、英語媒体、研究ノートなどをそれぞれ独立したリポジトリで管理する。
- Benefits: 各媒体の構成を単純化できる。
- Costs / constraints: 同じテーマの更新や画像が重複し、原稿の正本が分かりにくくなる。
- Status: rejected

## Decision

`serevy/tech-content` を公開向け技術コンテンツの正本とする。

日本語Zenn記事は `articles/`、英語ローカライズ版は `articles_en/`、共有画像は `images/` で管理する。新規Zenn記事は `published: false` を既定とし、明示的な公開承認なしに `published: true` へ変更しない。

日本語記事では、利用可能な場合に `coji/natural-japanese` を執筆・推敲支援として使う。ただし、文章編集と事実判断を分離し、Evidenceにない理由や技術的主張を追加しない。

英語版の最終配信先はこのPDDRでは固定しない。候補の比較と公開自動化は、実際に英語記事を配信する段階で判断する。

## Delivery and validation

GitHubリポジトリとZennの `main` ブランチ連携は設定済み。

この初期セットアップPRでPDDR Kit v0.2.1、執筆ルール、PDDR validation workflow、最初のZenn記事draftを追加する。英語記事の配信先と自動公開処理は未実装のため、全体の `delivery_status` は `in-progress` とする。

## Consequences

記事、画像、日英版、公開方針を同じGit履歴で追跡できる。記事そのものの細かな推敲はGit履歴へ任せ、PDDRは将来も理由を参照する公開・執筆プロセスの判断だけに限定する。

一方で、Zennと英語圏の媒体ではfront matterやMarkdown拡張、読者の前提が異なる。英語版を単純な機械翻訳として同期せず、主張とEvidenceを保ったまま媒体ごとにローカライズする作業が必要になる。

## Revisit when

- 英語版を実際に公開する媒体を決めるとき。
- Zenn以外の媒体がGitHub上のディレクトリ構成へ強い制約を要求するとき。
- 記事のライセンス方針を決めるとき。
- natural-japaneseの利用が技術表現や筆者の文体を損なうケースが継続して発生したとき。
- 公開承認フローを自動化するとき。

## Evidence

- `README.md`: リポジトリの対象コンテンツとディレクトリ方針。
- `AGENTS.md`: 公開安全策、日英執筆ルール、PDDR運用条件。
- `articles/pddr-kit-ai-decision-memory.md`: 最初のZenn向けdraft。
- ZennのGitHub連携設定: `serevy/tech-content` の `main` がデプロイ対象。設定はリポジトリ外のため、公開PDDRには認証情報や非公開設定値を含めない。

## Related records

現時点ではなし。
