# Issue #45 検証記録（2026-11-16 JST）

## 実接続の非通信観測
- 現接続でSpace一覧2件取得成功、各SpaceのルートPageメタデータ読取2/2成功、共有管理enabled、Space共有状態読取2/2成功。可視の非所有者直接共有0、継承参照complete=true/source0を両Spaceで確認。SpaceのID・名称・共有識別値は公開しない。
- 現接続の一覧における `can_create_chat=false` 2/2。B0/B1のスレッド新規作成権限や内部アクセス制御一般を否定するものではない。
- Memory/検索/History/引継ぎ/未特定経路の実適用と取得経路排他性UNKNOWN、実A/B0/B1送信0、秘密正解0、設定変更0。実秘密が未生成なので「実情報混入排除PASS」と断定できない。

## 合成契約と正式CI
- 合成漏出検知は8 source、固定fixtureの原文・SHA-256・合成所在の明示的露出を検知し、検知なしでも `isolation=UNKNOWN`、 `execution_allowed=false`。任意の実識別子に置き換えできないよう固定値以外を拒否。
- H04-Bの全7経路×8状態項目×4非PASS（224 subtests相当）、9開始条件×4非PASS（36 subtests相当）を合成で確認するテストを追加。1ケース=独立した実験試行ではない。
- 変更前HEAD `79ea5a8026421ade35c2b0f443074fa2e9dada0a` の正式CI run [43784689208](https://github.com/tetsujisugimori-coder/Hachibei-Lab/actions/runs/43784689208) はsuccess。専用ユニット10件＋既存H04-B回帰42件で失敗0。job #133029579022、公式artifact ID 14188918956、1,334 bytes、SHA-256 `d899944deb9629202411f04753e803627e9e8d8a883d23924e0663ac98b4d9f0`。
- 上記CI後、**原証拠の追跡性を補強するため**workflowへhead/tree identity、ソース収録、各収録ファイルのsize/SHA-256 manifestを追加。最終HEADの正式CI・artifact検査結果はPR最終報告で別に追記し、先行runを最終runと混同しない。

## 保全・制限
- GitHub Actions artifactの生成・公式digestはCIの観測値であり、本人限定Library/Spaceへの**保存後実物再取得・独立照合は未実施**。保全ゲートPENDING。GitHub公式ZIPのhashだけで原票収録網羅性は証明できない。
- 既存PR #42/#44及びREADINESS.json・旧原票は変更しない。GitHubで専用branch/Draft PRへ提出。関連Issue #45はOPENのまま。
- 合成検査と非通信メタデータ読取のみ。Memory/検索/Space等の設定変更、実スレッド新規作成/送信、予定登録なし。大容量処理なし。追加予算20MiB、環境のTemp空き・実測ピークはUNKNOWN。
- **総合PARTIAL・実験開始BLOCKED・本番混入排除UNKNOWN。** 今回の研究準備の確認と、今後の実験開始承認を混同しない。
