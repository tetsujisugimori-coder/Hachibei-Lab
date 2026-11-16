# H04-A/C v1: 経路研究基盤・形式検証

Issue #41。H03/PR #40はマージ済み。開始main `3df3fd732cfc927c6c4c1c1ba206d5a80ca4e83e`、tree `4eb3282fb40666f0f9e1cc5ae4552c4ad9190f89`。

対象は研究用のオフライン形式検査と合成対照のみ。H04-Bの実スレッド実験、H04-Dの実験結果監査、Memory/Spaceの設定変更、接続追加、予定登録は対象外。コードは通信・設定変更能力を持たない。

## 判定の分離
`format/content/revision`は合成入力の契約充足。`acquisition_route/automatic_sharing`は常にUNKNOWN、`real_experiment`はNOT_TESTED。これらを一つのPASSへ集約しない。取得経路の自己申告、任意に入力された証拠hash、ツール禁止の文章では実際の制御適用や因果経路を証明できない。H04/1では適用YES・経路PASSを拒否し、実測を受け入れる際は将来別版で認可された証拠の取得・出所検証を設計する。

## ファイル
- `verify.py`: 1MiB以下のUTF-8/LF JSONを検査、構造化失敗理由。
- `test_verify.py`: 再現可能な完全合成入力・正常/異常対照。
- `ROUTES.json`: 7経路の調査台帳。実設定と自己申告を分離。
- `CONTRACT.md`: H03互換境界・新形式。
- `B-DESIGN.md`: 将来B0/B1の事前設計。実験開始の許可ではない。
- `VERIFICATION.md`: 既存原物保護・検証結果・限界。

実行: `python -m unittest discover -s research/dot-capabilities/h04-20261116 -v`。
CLI: `python research/dot-capabilities/h04-20261116/verify.py synthetic.json`。

## 既存研究との比較
PR34は能力・制約の整理、PR36/C05/C06は明示担当引継ぎ、PR38は本人の自然な追加指示を待つ準備。H03は同じBの明示前後1事例であり独立2試行ではない。H04は新しい実観測件数を追加せず、形式的誤受理と根拠なき経路推定を防ぐ研究用基盤。H03の原票・判定・検証器を上書きしない。
