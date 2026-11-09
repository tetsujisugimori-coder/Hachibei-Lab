# 履歴・解消済み事項・現在の残件

確認日：2026-11-10 JST。過去の障害を現在も継続中と誤認させないため、状態と証拠を分ける。

## RESOLVED：初期 base がなかった提出阻害（旧項目1）

| 項目 | 記録 |
| --- | --- |
| 発生日時 | UNKNOWN。初回観測の実時刻は未確定 |
| 記録済み時点 | Issue #2 作成 2026-11-07T23:38:27Z。障害発生時刻とは区別 |
| 解消証拠の時刻 | README 初期化 commit の記録時刻 2026-11-08T00:39:33Z。少なくともこの時点で base commit が存在 |
| 解消証拠 | [6a3088a329df5384a3091c8f1e7338c4d855648f](https://github.com/tetsujisugimori-coder/Hachibei-Lab/commit/6a3088a329df5384a3091c8f1e7338c4d855648f) |
| 追加の確認証拠 | [PR #3](https://github.com/tetsujisugimori-coder/Hachibei-Lab/pull/3) 作成 2026-11-08T00:43:16Z |
| 再確認 | main と前回 PR HEAD の README blob は ce416436b7acb6ec2158ae7675e0bfbf765d8c26 と一致。固定値は [baseline.json](evidence/baseline.json) |
| 現在状態 | RESOLVED。現在の資料棚卸し不足とは別件 |

Issue #2 は 2026-11-09T22:48:49Z に履歴見出しと追記を修正し、再取得で一致を確認した。初回の段落は削除していない。[公開 Issue の前後スナップショット](evidence/public-issues.json) を参照。

## 現在の残件と境界

| ID | 旧項目 | 現在状態 | 次に必要な証拠 |
| --- | --- | --- | --- |
| SCOPE-01 | 2 | BOUNDARY_DEFINED | Issue #1 の能力評価は今回の対象外。能力実験を開始しない |
| OPEN-01 | 3 | OPEN | 各原本の本文版・改訂日・サービス revision と適用期間の照合 |
| OPEN-02 | 4 | OPEN | 同名資料の原本・複製関係、必要なハッシュや内容比較。未比較は NOT_TESTED |
| OPEN-03 | 5 | OPEN | 承認・失効・置換の証拠。資料存在と現行規則を混同しない |
| OPEN-04 | 6 | OPEN / PUBLICATION_WITHHELD | 非公開資料の公開許可は UNKNOWN。公開側へ本文・名称・内部 URL・識別子を載せない |
| OPEN-05 | P2 | 再受入で評価 | 重要資料と本人用台帳の原証拠照合、母集団の確認可否を記録。全参考原典の精読を自動的な完了条件にしない。構造追加だけでも完了にしない |

## 旧記録の保全

[修正前 conflicts.md の全内容](evidence/conflicts-before.md) を前回レビュー HEAD 3e2576a0129b4949971535efbbb96166cff32b07 からそのまま保存した。末尾の「これらは未解決事項」という旧記述は当時の誤った一括表示であり、現在状態は上表を使用する。旧記録自体は削除・改変していない。

これらは資料の削除、正式規則の修正、設定変更、公開範囲拡大の指示ではない。
