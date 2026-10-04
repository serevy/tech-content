# Project guidance

このリポジトリは、技術記事・研究ノート・公開向け解説の原稿をGitHubで管理するためのリポジトリです。
GitHubを原稿の正本とし、日本語記事は主にZenn向け、英語記事は海外向け媒体へローカライズして配信することを想定します。

## Directory conventions

- `articles/`: 日本語記事。ZennのGitHub連携対象。
- `articles_en/`: 英語向け原稿・ローカライズ版。配信先と自動公開方法は別途決定する。
- `images/`: 記事で利用する画像。
- `docs/records/`: このリポジトリ自身のPDDR。

## Publishing safety

- 新規Zenn記事は必ず `published: false` で作成する。
- ユーザーが公開を明示的に依頼するまで `published: true` に変更しない。
- 英語記事も、配信先と公開フローが承認されるまで自動公開しない。
- 外部サービスの設定状態を、確認できていないのに「設定済み」と記録しない。
- 非公開会話、個人情報、認証情報、秘密情報を公開記事や公開PDDRへ転記しない。

## Japanese writing

日本語記事の執筆・推敲では、利用可能な場合は
[coji/natural-japanese](https://github.com/coji/natural-japanese)
を編集支援として使用します。

ローカルの対応エージェントでは、例えば次の方法で導入できます。

```bash
npx openskills install coji/natural-japanese
npx openskills sync
```

natural-japaneseは「何が事実か」を決める情報源ではなく、「どう自然に伝えるか」を改善する編集レイヤーとして扱います。

- 技術的な事実、バージョン番号、コード、コマンド、引用、URL、固有名詞を文章上の都合で改変しない。
- Evidenceにない理由や効果を補完しない。
- 筆者自身の実感や軽いユーモアは、記事の読みやすさを損なわない範囲で残す。
- 箇条書きを増やすより、因果や経緯は地の文でつなぐ。
- 見出しは必要に応じて内容が分かる形にするが、すべてを同じ型へ揃えない。
- 事実と意見を区別し、外部の事実には可能な範囲で一次情報へのリンクを付ける。

## AI assistance disclosure

公開記事で生成AIを構成・執筆・推敲・翻訳・画像生成などに利用した場合は、記事末尾に短い注記を置き、利用範囲を具体的に示します。

- 「AIで書いた」と一括りにせず、構成、下書き、推敲、翻訳、画像生成など実際に使った範囲を書く。
- 筆者の実体験、判断、検証、最終的な内容確認が人間側にある場合は、その責任範囲も明記する。
- 利用していない工程までAI利用として書かない。
- 特定のモデル名やサービス名は、再現性や読者理解に必要な場合だけ記載する。単なる宣伝目的では並べない。
- AI利用の注記は本文の主張やEvidenceを補強する根拠として扱わない。

日本語記事の既定例:

> ※ 本記事では、構成・執筆・推敲の補助に生成AIを利用しています。内容は筆者が確認・編集しています。

研究・実験寄りの記事では、実験結果、データ、引用、解釈の責任範囲を必要に応じてより明確にします。

## English writing

英語版は日本語版の逐語訳ではなく、英語圏の読者向けに導入・見出し・例を再構成します。
ただし、主張の強さ、技術的事実、Evidenceの範囲は日本語版から勝手に拡張しません。

## PDDRを作成・更新する条件

- Project / Product / Processに関する重要な判断が、明示的に採用、不採用、保留、または置換されたとき
- 公開媒体、原稿の正本、公開承認、AI執筆支援など、今後も理由を参照する運用方針を決めたとき
- 実装や検証によって既存判断の `delivery_status` または前提が変わったとき
- 将来の担当者が理由を知らないと、同じ議論や事故を繰り返しそうなとき

記事ごとの言い回し、誤字修正、通常の推敲、画像差し替えなどはGit履歴で管理し、それだけを理由にPDDRを作成しません。

## PDDR checkpoints

大きな公開フロー変更、媒体追加、シリーズ方針変更、運用ルールの棚卸し時には、最近のIssue、PR、既存PDDR、Evidenceを通常のPDDR thresholdで再点検します。

checkpointを実施したこと自体はPDDR作成理由にしません。durableなProject / Product / Process判断がなければ、追加記録なしを正常な結果とします。

## PDDR record rules

- `.pddr/template.md`から `docs/records/PDDR-NNNN-short-title.md` を作成する。
- 会話やEvidenceにない理由を補完しない。
- 人の承認が確認できない提案を `accepted` にしない。
- `decision_status` と `delivery_status` を別々に判断する。
- `validated` には確認内容が分かるEvidenceを付ける。
- PDDRを無条件のPolicyや実行命令として扱わない。
- 変更後に `python .pddr/pddr.py validate` を実行する。

## GitHub Actions

CIを作成・変更するときは、次の点を確認する。

- 必要な検証に合わせてtrigger、path、job、matrixを選ぶ。実行条件の変更やジョブ統合では、required checkの名前と失敗検知を維持する。
- 実測に基づく明示的なjob timeoutを設定する。PDDR検証は5分とする。古いread-only検証の取消しは同一workflow・同一PRに限定し、PR以外はrefとrun IDでgroupを分けてmainや手動実行を独立させる。
- jobの権限は必要最小限にし、信頼されていないPRの検証とリポジトリへ書き込むjobを分離する。
- 依存関係、cache、artifactは効果を確認して追加する。cache keyとartifact保持期間を明示的に検討する。標準ライブラリだけで動くPDDR検証には追加の依存関係やcacheを導入しない。
- PRには期待する効果、workflow/job数、検証結果、観測したjob実行時間を記録する。実行時間の観測と課金上の使用量を区別する。

PDDRのworkflowは任意の導入設定であり、Kitのmanaged file更新には含まれない。[PDDR Kit導入ガイド](https://github.com/serevy/pddr-kit/blob/main/docs/adoption.md#github-actions)を参照して、workflowの更新を明示的に採用する。このリポジトリでは[PDDR Kit #47](https://github.com/serevy/pddr-kit/issues/47)のCI実行上限・取消し範囲の設定を採用する。
