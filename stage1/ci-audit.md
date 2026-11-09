# Stage 1 CI 未実行の原因と検証経路

## 開始時の事実（2026-11-10 JST）

- 開始 HEAD: 48f5fe96aa6df48de64272f2eabd0bad66d92a5a。tree に workflow はない。
- main: 384ba3b3629111c96800d5c57dfb7c8a63a3f140。別案件の2 workflow がある。どちらも pull_request の path filter はその案件のディレクトリと当該workflow自身。Stage 1 の差分は一致しない。
- 一方は main の push も対象だが、今回の PR branch への push とは異なる。Stage 1 を検査する有効なイベント/パス組合せはなかった。
- 開始 HEAD に対応する workflow runs・check-runs・statuses は0件。pending という集約表示を「実行中」や「CI成功」と解釈しない。
- 同リポジトリの別案件には実際の [成功 run](https://github.com/tetsujisugimori-coder/Hachibei-Lab/actions/runs/42699923598) がある。実行基盤が過去に機能していた証拠であり、Stage 1 の成功証拠ではない。

このため、開始 HEAD で CI が0件だった説明として「対象workflowなし/別案件path filter外」を確認できる。実行基盤の全設定の正常性を推測で認定しない。

## 取得できない管理設定

workflow 一覧の有効状態と Actions 実行権限を専用 GET で照会したが、利用可能な接続ツールは該当 endpoint をサポートせず INVALID_ARGUMENT を返した。管理設定の現在値は UNKNOWN。設定変更・権限拡大・別経路による制限回避は行わない。

設定の未取得と、公開 workflow の内容/実行履歴から確認できる事項は分ける。専用 CI の実起動・ログ・commit 一致が得られた場合も、実行に必要な機能がその実行で働いた証拠に限る。

## 最小専用 CI

[stage1-inventory.yml](../.github/workflows/stage1-inventory.yml) を新規追加。既存workflowは取り込まず、変更しない。

- pull_request: opened / synchronize / reopened。Draft を除外する条件は設けない。
- 対象パス: stage1/** と専用workflow自身。別案件の条件を緩めない。
- contents: read。checkout は PR HEAD 固定・fetch-depth 0・persist-credentials false。
- 公開 JSON スキーマ、資料台帳整合性、正常系/負対照、git diff --check、文書/コード/workflowの混入検査、README/固定公開証拠の不変を実行。
- 本人用の名前・ID・URL・具体集計・本文を CI の入力、環境変数、ログ、artifact に渡さない。
- artifact に実行 HEAD、tree、run ID、attempt、workflow hash、検査 outcome、各ログの SHA-256 を保存。未実行・失敗は evidence_complete=false。

## 最終結果の読取り

CI を追加しただけでは PASS にしない。最後に push した commit と run の head_sha、checkout HEAD、check conclusion、job 原ログ、artifact の identity とログハッシュを照合する。最終 PR 本文と同一 HEAD の正式レビューに結果と run URL を記録する。未起動の場合は UNKNOWN/BLOCKED を維持し、ローカル成功で代用しない。
