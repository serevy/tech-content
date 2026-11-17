---
title: "AIに日記を1件書いてもらうまで、2〜3日かかった話：GitHub AppとGatewayの備忘録"
emoji: "🛠️"
type: "tech"
topics: ["AIエージェント", "GitHubApp", "Cloudflare", "GitHubActions", "Muse"]
published: false
---

やりたかったのは、AIエージェントが重要な出来事を短い日記にして、GitHubへ残すこと。それだけだった。

ところが、実際に最初の1件が保存されるまで、2〜3日ほどかかってしまった。GitHub Appの権限を確認し、Cloudflareへのログインで詰まり、ようやくつながったと思ったらHTTP 403が返ってくる。日記を書くための準備が日記の題材になりそうな状況だった。

前の記事では、Metaの「Muse」を観察しながら、記憶や自己改善の積み重ねをどう確かめるかを書いた。

https://zenn.dev/daydream/articles/muse-observation-01-memory-and-boundaries

今回はその観察日記を残す仕組みと、初回接続で実際に詰まった点の備忘録だ。サービスの内部仕様を解明した記事ではなく、個人環境で試した構成と結果の記録である。日記本文や認証情報、非公開リポジトリの識別情報は載せない。

## 日記を外に残す理由

Museには記憶を整理したり、過去の行動を振り返ったりする仕組みがある。ただ、その記録を本人が更新するなら、後から「本当に変わったのか」を調べるための比較対象も欲しい。

そこで、観察用の非公開GitHubリポジトリを用意した。会話全文を保存する場所ではなく、重要な出来事、判断、その結果を短く残すための場所だ。

記録は大きく4種類に分けた。

| 記録 | 残すもの |
| --- | --- |
| 日記 | その日に起きた出来事、判断、結果、未確認事項 |
| ベースライン | 観察を始めた時点の状態と、確認できていない点 |
| 変更記録 | 記憶・Skill・運用ルールなどの意味ある変更 |
| 定期レビュー | 繰り返す失敗、役立った先回り、改善の提案 |

「実際に観測したこと」「Muse自身の報告」「推測」「未確認」は分ける。記録に書かれていることが正しいか、何かが改善したかは、別途確かめなければならない。

## MuseにGitHubの秘密鍵を渡さない

最初に考えたのは、エージェントが自分でGitHubへ日記を投稿できる経路だった。ただ、GitHubへ書き込める権限を持たせるなら、使える範囲を先に決めておきたい。

採用した構成は次の流れだ。

1. Museが日記1件の投稿を要求する。
2. Cloudflare Workerで作ったGatewayが、呼出元と許可された操作を確認する。
3. Gatewayの内部で専用GitHub Appの短命トークンを使い、日記の新規ファイルを追加するDraft PRを作る。
4. Gatewayが変更内容を確認してPRをReadyにする。
5. 日記リポジトリ側のGitHub Actionsが検証し、条件を満たす新規記録だけを自動マージする。

GitHub Appは観察用の1リポジトリだけにインストールし、必要なContentsとPull requestsの権限に絞った。Gatewayも任意のGitHub APIを代理実行する構成にはしていない。MuseへGitHub Appの秘密鍵やInstallation Tokenを返さず、許可する操作と対象をサーバー側で固定している。

ここで改めて気づいたことがある。**私が別のAIツールにGitHubの広い権限を与えていても、Muse専用GitHub Appの権限が増えるわけではない。** GitHub Appの登録権限、インストール対象、発行するトークンの権限は別々に確認する必要があった。

GitHub公式ドキュメントでも、Installation TokenはAppに許されたリポジトリと権限を超えて発行できないと説明されている。

https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation

## CloudflareのログインとHTTP 403で詰まった

Gatewayをデプロイする段階では、ChatGPTのクラウドブラウザからCloudflare Dashboardへのログインが進まなかった。原因は特定できていないので、Cloudflareが常にクラウドブラウザを拒否するという話ではない。

今回はWrangler CLIのデバイス認証を使った。

```bash
npx wrangler login --device --browser=false
npx wrangler whoami
```

CLIに表示される案内に従い、本人が別端末で承認する。遠隔環境でブラウザのコールバックが扱いにくい場合にも使える方法で、[Cloudflareの公式ドキュメント](https://developers.cloudflare.com/workers/wrangler/commands/general/)に載っている。認証コードやトークンはチャットやリポジトリに残さない。

次に詰まったのは、Museの送信ヘルパーからGatewayへ送ったHTTPリクエストだった。Museからの報告では、最初は403。応答情報を追加して再確認すると、Cloudflareの `error code: 1010`、`text/plain`、Gatewayの監査IDなし、という結果になった。

これはGateway自身が返すJSONの認証エラーとは様子が違う。[Cloudflareの公式説明](https://developers.cloudflare.com/workers/configuration/routing/workers-dev/)によれば、`workers.dev` ではBrowser Integrity Checkが働き、Pythonの一部の標準User-Agentを持つ自動クライアントが**Workerの実行前に**1010で拒否される場合がある。Workerのログに出ないこともある。

Muse側が送信時にアプリを識別できるUser-Agentへ変更したところ、今度はGateway形式のJSONで `503 journal_writes_disabled` が返ったと報告された。当時は認証試験用に日記の書き込みを無効にしていたため、これはWorkerへ到達し、認証経路を通って書込禁止の判定まで進んだことと整合する。

ただし、この通信の細部はMuse自身の報告に基づいており、私が全パケットを独立に確認したわけではない。User-Agentだけが唯一の原因だったとも断定しない。少なくとも、**HTTP 403を見ただけで「GitHub Appの認証に失敗した」と決めつけるのは早かった。**

## 初回の日記PRは成功した

その後、書き込みの有効化を進め、2026年11月17日にMuseからの初回日記投稿がGitHub App名義のPR作成、CI検証、自動マージまで進んだことを確認できた。

ここで確認できたのは、日記1件を安全にGitHubへ届ける経路が動いたということ。日記を保存しただけでMuseが自動学習したり、次回必ずその記録を参照したりするわけではない。

また、**GitHub上のコードをマージすることと、実際に動いているWorkerを更新することは別**だ。日記以外の変更記録や定期レビューにも投稿経路を広げる作業は進めているが、追加機能はレビュー・マージとデプロイの確認がそろうまでは稼働済みと扱わない。

## 制限を増やしすぎた反省

最後に残しておきたいのは、技術的なエラーよりも運用上の失敗だ。

初期の目的は「重要な日記を1件残す」だった。それなのに、日付、投稿件数、書式、承認手順などの制限を各段階で足し続けた結果、私が代わりにコミットしたり、何度も確認したりする場面が増えた。これでは、せっかくのエージェントの自走力を活かせない。

そこで役割を整理した。Gatewayは呼出元の認証、許可された操作、秘密鍵の保護に集中する。日記の書式やPRの変更範囲は、記録を保存するGitHubリポジトリ側のCIで確認する。委任済みの記録作成はエージェントに任せ、権限の拡大、外部公開、課金、運用ポリシーの変更は別の承認を求める。

もちろん、制限を減らせば安全になるわけではない。どの事故を防ぐための制限なのか、既存の仕組みで防げないのか、失敗したときに検知・復旧できるのか。加えて、その制限が日常の運用をどれだけ妨げるかも考える必要があると感じた。

日記のPRがマージされたことは、その記録を保存したという事実にすぎない。記録された改善案を採用したり、新しい操作を許可したりしたことにはならない。この境界だけは残しておきたい。

最初の1件を残すのにずいぶん遠回りした。でも、認証・権限・記録・承認をどう分けるかを見直すきっかけにはなった。これから本当に確かめたいのは、日記を残し続けることで、Museの判断や行動の変化を後から追えるかどうかだ。

---

## 参考資料

- [GitHub Docs：GitHub Appのインストール範囲](https://docs.github.com/en/apps/using-github-apps/installing-a-github-app-from-a-third-party)
- [GitHub Docs：Installation Tokenでの認証](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation)
- [Cloudflare Docs：workers.devのBrowser Integrity Check](https://developers.cloudflare.com/workers/configuration/routing/workers-dev/)
- [Cloudflare Docs：Wranglerのログイン方法](https://developers.cloudflare.com/workers/wrangler/commands/general/)

※ 本記事では、構成・下書き・推敲に生成AIを利用しています。実際の設定・観察結果・公開範囲は筆者が確認するものとし、私的な日記と認証情報は公開しません。
