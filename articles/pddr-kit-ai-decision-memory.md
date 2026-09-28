---
title: "PDDR Kit爆誕 ― AIと開発していたら「なぜこうした？」が消えた"
emoji: "🎋"
type: "tech"
topics: ["ai", "github", "oss", "adr", "開発プロセス"]
published: false
---

AIと開発すると、コードは速く増える。でも、判断の理由まで同じ速さで残るわけではない。

Issueはある。PRもある。チャット履歴もある。それなのに数日後、実装を見返してこうなる。

> 「……なんでこれ、こうしたんだっけ？」

この問題を何度か踏んだ結果、判断そのものだけでなく、その前後までつなげて残すための **PDDR Kit** を作った。

https://github.com/serevy/pddr-kit

## コードは残るのに、理由は散らばる

Gitを使っていれば、コードの変更履歴はかなり正確に残る。Issueには作業の背景があり、PRには実装時の議論がある。AIと相談した内容はチャットにも残っている。

困ったのは、それぞれが別の場所にあることだった。

たとえば、ある機能を見送った理由を知りたいとする。Issueには最初の案、チャットには比較した選択肢、PRには最終的な実装、CIには検証結果が残っているかもしれない。全部読めば分かるとしても、数週間後の自分や別のAI Agentが毎回その発掘作業をするのはつらい。

欲しかったのはログの追加ではなく、**「何を見て、何を選び、実装後に何を確かめたか」をたどれる索引**だった。

## 最終決定だけでは足りなかった

最初に参考にしたのは、ADR（Architecture Decision Record）やDDR（Design Decision Record）だった。

ADRは「なぜこのアーキテクチャを選んだか」を残す方法としてよく知られている。DDRも、設計上の判断とその背景を記録する考え方だ。

ただ、自分が後から困った判断はArchitectureだけではなかった。

公開範囲をなぜ分けたのか。ある実験をなぜ止めたのか。レビュー方法をなぜ変えたのか。AI Agentへどこまで任せるのか。こうした判断は、Project、Product、Processのどこでも発生する。

そこでPDDRでは対象を次の3つに広げた。

- **Project**: 目的、範囲、優先順位、公開方針
- **Product**: 要件、ユーザー体験、機能、品質基準
- **Process**: 開発手順、レビュー、AI活用、検証方法

PDDRはADRやDDRを置き換えるものではない。既存のDecision Recordがあるなら、それを参照しながら、判断前の観測と判断後の実装・検証までをつなぐ。

正式名称は **Project Design Decision Record**。少し長いので、普段はPDDRと呼んでいる。

## 「決めた」と「できた」を分ける

PDDRを作っていて、意外と効いたのが状態を二つに分けたことだった。

ひとつは、その判断を採用したのかどうかを表す `decision_status`。もうひとつは、実装や検証がどこまで進んだかを表す `delivery_status` だ。

たとえば方針としては採用済みでも、まだコードには入っていないことがある。実装済みでも、期待した結果になったかは検証していないこともある。

```text
decision_status: accepted
delivery_status: in-progress
```

この二つを一緒にしてしまうと、「決めたから実装済みだろう」「コードがあるから検証済みだろう」という飛躍が起きる。

PDDR Kitでは、そこをわざと分けている。

## AIには、分からないことを分からないまま書かせる

PDDR KitにはAI向けのRecorder Skillもある。ただし、AIに判断記録を任せるなら、便利さより先に決めておきたいことがあった。

**会話にない理由を補完しない。**

AIは文脈から自然な理由を作れてしまう。「たぶん性能のためにこの方式を選んだのだろう」と書けば文章としてはきれいだが、それが当時の理由とは限らない。

そのため、分からない経緯は `unknown`、人の合意を確認できない判断は `needs-confirmation` として残す。

同じ理由で、AIが「この案がよさそうです」と提案しただけの状態を、人間が採用した判断へ勝手に変換しない。

記録をそれらしく完成させるより、**不確かな部分を不確かなまま残す方が価値がある**と考えた。

## 何でもPDDRにすると、今度はPDDRがノイズになる

PDDRは作業日誌ではない。

誤字修正、通常の依存更新、小さなリファクタリングまで全部PDDRにすると、重要な判断が埋もれてしまう。

記録する基準は、「将来の担当者が理由を知らないと、同じ議論や事故を繰り返しそうか」。

Issueは仮説や途中経過、生の結果を残す。PDDRは、その結果を受けて採用・不採用・保留した、長く参照する価値のある判断を残す。役割を分けると、記録量はかなり抑えられる。

v0.2系では、Agent Skillが見ていない変更経路を補うためにoptional checkpoint CIも追加した。high-signalな変更があったときに「PDDRが必要」と自動判定するのではなく、「一度棚卸しした方がよい」というsignalだけを残す。

現在の安定版は **v0.2.1**。checkpoint CIでは、PR headを読む処理とPRへmarkerを書き込む処理を分離し、write権限を持つjobがPR側のコードを実行しないようにしている。

https://github.com/serevy/pddr-kit/blob/v0.2.1/docs/releases/v0.2.1.md

## PDDR Kit自身でもPDDRを使う

この仕組みは、PDDR Kit自身とサンプルプロジェクトでdogfoodingしている。

最小例として公開している `pddr-greenfield-example` では、PDDRの導入から更新、checkpoint CIまで実際に試している。

https://github.com/serevy/pddr-greenfield-example

v0.2.1のcheckpoint CIも、このconsumer側でend-to-end確認した。つまり「意思決定記録の仕組みを改善した理由」も、意思決定記録とGitHub上のEvidenceへ戻っていく。

少し再帰的だが、作っている本人としてはここがかなり面白い。

そして、このZenn記事を管理している `tech-content` リポジトリにもPDDR Kitを導入した。

記事の言い回しを変えるたびにPDDRを作るわけではない。「なぜZenn専用repoではなく日英共通の原稿repoにしたのか」「AIによる文章編集をどこまで許すのか」といった、今後も参照する運用判断だけを残す。

記事を書き始めただけなのに、またdogfooding先が一つ増えた。

## 導入はMarkdownとPythonだけ

PDDR Kitの基本運用に特定のAIやSaaSは必要ない。Python 3.10以降があれば、取得したPDDR Kitから対象プロジェクトへ初期化できる。

```bash
python scripts/pddr.py init --target /path/to/your-project
```

新しい記録はテンプレートから作る。

```bash
cp .pddr/template.md docs/records/PDDR-0001-short-title.md
python .pddr/pddr.py validate
```

導入済みプロジェクトを更新するときは、先に差分だけ確認できる。

```bash
python scripts/pddr.py upgrade --target /path/to/your-project --dry-run
python scripts/pddr.py upgrade --target /path/to/your-project
```

Kitが管理するファイルと、導入先が書いたPDDRや独自設定は分けてある。更新のために既存記録を上書きしないことも、最初から必要な条件だった。

## AI向けの記憶を作ったら、自分にも効いた

PDDRを考え始めたときは、AI Agentが過去の判断を引き継ぎやすくする意識が強かった。

でも実際に使うと、助かるのは人間も同じだった。

数週間前の自分は、かなり他人に近い。Issue、PR、チャットを全部読み返さなくても、PDDRから判断とEvidenceへたどれるだけで復帰が速くなる。

コードはGitが覚えてくれる。判断の理由は、意識して残さないと消える。

PDDR Kitは、その理由もプロジェクトの資産として扱えるかを試しているOSSだ。まだ若い仕組みなので、実際に使ったときの「ここは重い」「この判断は拾えなかった」といったフィードバックがあれば、[GitHubのIssue](https://github.com/serevy/pddr-kit/issues)で教えてもらえるとうれしい。

## 参考

- [窪内 彩佳「AIとの対話履歴を資産にする。DDR（Design Decision Record）自動記録の仕組み」](https://zenn.dev/softbank/articles/ee93e87a9d5dac)
- [Michael Nygard, "Documenting Architecture Decisions"](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [Markdown Architectural Decision Records (MADR)](https://adr.github.io/madr/)

---

※ 本記事では、構成・執筆・推敲の補助に生成AIを利用しています。内容は筆者が確認・編集しています。
