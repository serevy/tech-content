---
id: PDDR-0002
title: Use one pinned Japanese editorial skill
decision_date: 2026-11-17
recorded_date: 2026-11-17
decision_status: accepted
delivery_status: in-progress
scope:
  - process
owners:
  - serevy
evidence:
  - AGENTS.md
  - README.md
  - docs/records/PDDR-0001-multilingual-publishing-workflow.md
  - https://github.com/nanaism/yomiyasu/tree/v3.1.0/skills/yomiyasu
  - https://github.com/serevy/tech-content/pull/8
related:
  - PDDR-0001
supersedes: []
superseded_by: null
---

# PDDR-0002: Use one pinned Japanese editorial skill

## Summary

日本語記事の執筆・推敲支援は `yomiyasu` に一本化する。スキルをリポジトリに固定バージョンで配置し、別の推敲スキルとの併用を避ける。これは PDDR-0001 の日本語推敲スキルの選定だけを更新する判断であり、原稿管理、公開承認、多言語運用、AI利用の明示に関する決定は変更しない。

## Context and observations

PDDR-0001 では `coji/natural-japanese` を編集支援の候補として採用していた。その後、Muse観察編①の推敲では `yomiyasu` v3.1.0 を使用した。筆者は読みやすさを評価したうえで、推敲スキルを同時に使わず一つに絞る判断を 2026-11-17 のプロジェクト会話で明示した。

この判断は、二つのスキルを併用した場合に必ず品質が下がるという実験結果を意味しない。異なる推敲ルールが重なることを避け、同じ手順を再利用できるようにする運用上の選択である。

## Options considered

### natural-japanese を継続する

- Description: PDDR-0001 の編集支援スキルを継続する。
- Benefits: 既存の案内を変更しなくてよい。
- Costs / constraints: 今回記事の推敲で利用した `yomiyasu` の手順とは別になる。
- Status: rejected

### yomiyasu に一本化する

- Description: `yomiyasu` v3.1.0 をリポジトリに保存し、日本語記事の推敲に利用する。
- Benefits: 推敲の手順と検査を、記事を編集するAI間で参照できる。
- Costs / constraints: スキルの更新を別途管理し、検査結果だけで文章の品質を保証しない。
- Status: accepted

### 二つを併用する

- Description: 二種類の推敲スキルを順番に適用する。
- Benefits: 異なる観点から文章を見直せる可能性がある。
- Costs / constraints: ルールが競合した場合の優先順位が不明確になる。
- Status: rejected

## Decision

日本語記事の執筆・推敲では、リポジトリ内 `.agents/skills/yomiyasu/SKILL.md` の手順を用い、その他の文章推敲スキルを重ねない。Claude Code からも同じファイルを参照する。文章の意味、条件、事実、引用、筆者の実感と文体を守り、最終的な内容確認は筆者が行う。

`yomiyasu` の更新は、上流のバージョンと変更点を確認し、スキル本体とバージョン表示を同じPRで更新する。記事の公開承認フローは従来どおりとする。

## Delivery and validation

本判断を反映するPRで `AGENTS.md`、`README.md` の案内を変更し、`yomiyasu` v3.1.0 のスキル一式を追加する。PDDR検証とスキルのファイル・実行確認を行い、マージ後に運用へ反映する。実際の記事への適用結果は記事ごとのレビューで判断する。

## Consequences

記事ごとにどの推敲スキルを使うか迷わず、同じバージョンを再利用できる。一方、文章の自然さや品質はスキルだけでは保証されない。ほかの推敲手法を再導入する場合は、この判断を見直す。

## Revisit when

- `yomiyasu` の新しいバージョンに取り込むべき変更があるとき。
- 推敲で事実関係、語り口、筆者の意図が損なわれる事例が続いたとき。
- ほかのスキルとの比較や併用が必要になったとき。

## Evidence

- 2026-11-17 のプロジェクト会話: 筆者は `yomiyasu` の採用と、推敲スキルの一本化を明示した。
- [Muse観察編①の推敲PR #8](https://github.com/serevy/tech-content/pull/8): `yomiyasu` を使用した記事の変更。
- [nanaism/yomiyasu v3.1.0](https://github.com/nanaism/yomiyasu/tree/v3.1.0/skills/yomiyasu): 取り込むスキルの上流ソース。
- `AGENTS.md` と `.agents/skills/yomiyasu/`: このPRで反映する案内とスキル本体。

## Related records

- [PDDR-0001](PDDR-0001-multilingual-publishing-workflow.md): 公開・多言語運用の決定。日本語推敲スキルの選定だけ本記録で更新する。
