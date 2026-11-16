# Issue #45 読取専用アクセス観測と判定（2026-11-16 JST）

## 対象・方法・許可の境界
- 実施: 認可済み接続からGitHubのIssue・PR・方針・準備台帳の読取、Space一覧API、2件のルートPageのcontent=falseメタデータ読取、共有管理可否API、2件のSpace共有スナップショット読取。GitHub Issue #45への結果コメントを投稿。
- 未実施: 実験A/B0/B1の作成・送受信、秘密文書/識別子の生成、Memory/検索/Space等の設定変更、Space本文/本人限定ファイルの読取り、内部仕様の探索、計画外権限変更、タスク/予定登録。
- 開始時点の根拠: Issue #45、mainの `research/dot-capabilities/h04b-20261116/READINESS.json`。準備基盤の実装と、本番の機能実証は別。外部に公開するのは観測数・結果のみ。Space ID、ルートPage ID、共有相手の識別値、実験用原文/秘密hashを公開しない。

## 実接続で確認したこと
1. 現在のアカウントからSpace一覧取得が成功（2件）。両SpaceのルートPageに対する **本文なしメタデータ取得** 成功（2/2）。一覧の`can_edit`は2/2 true。
2. 同一覧の`can_create_chat`は2/2 false。**当該Space一覧の表示項目のみ**。全UI・別アカウントでのチャット作成権限否定ではない。
3. 現接続で `sharing_management_enabled=true` を観測。2件のSpace共有読取に成功。可視の直接共有に非所有者0件、継承参照は2件とも`complete=true`かつsource0件。**この2件のSpace共有スナップショットに限定**する。子Page個別権限、内容複製・検索索引、Memory、第三者の取得済みコピー、内部取得経路、将来のACL変更まで排除したわけではない。
4. GitHub側でIssue #45及び公開済みH04-Bの契約読取成功。公開リポジトリの可視性と外部からの見え方は同じではない。秘密値を一度も生成していないため、本物の「B0への事前漏出なし」は観測・確定できない。

## 7経路の現時点の根拠境界
| 経路 | 今回の実観測 | B0向け利用/遮断適用 | 代替経路排除 |
|---|---|---|---|
| history | 既存研究文書を読むのみ、新規B0スレッドなし | NOT_TESTED | UNKNOWN |
| transfer | GitHub Issueへの公開レビュー書込み受付。B0明示転送とは別 | NOT_TESTED | UNKNOWN |
| memory | 設定・対象内容のアクセス条件未検証 | UNKNOWN | UNKNOWN |
| shared/Space | 現接続で2 Spaceのlist・ルートmeta・共有状態を読取成功 | NOT_TESTED | UNKNOWN |
| search | 公開GitHubの情報検索は利用可能。実験用内容のインデックス操作なし | NOT_TESTED | UNKNOWN |
| handoff | 対象担当への実引継ぎなし | NOT_TESTED | UNKNOWN |
| unidentified | 全候補を観測できた証拠なし | UNKNOWN | UNKNOWN |

## 保守的な結論
- **アクセス可否の一部限定観測PASS、経路排他性UNKNOWN、実験開始BLOCKED、総合PARTIAL。** Space取得成功はB0秘密を隔離できた証明ではない。
- owner_approval=BLOCKED、他の8開始条件=UNKNOWN、7経路の本番検証=UNKNOWN。READINESS.jsonを変更しない。
- B0本番の混入除外は、承認後の非公開正解原票、実B0の公開/非公開表面を事前に列挙・凍結した監査、機能実適用証拠が必要。不明項目をPASSへ自動昇格させない。
