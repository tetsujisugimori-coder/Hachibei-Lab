# H04-B5 実施環境・証拠取得の具体化 v1

Issue #53、関連 #45/#47/#51。2026-11-18。基準main/PR52 merge `3136fc51a6f22b7f57144c94c08a11d0b28c9a7c`、tree `6900832d20fd5c3ead3816d75829d68d408ecff9`。PR52最終HEAD `dbe21c754d5af274c322819f0146f65bb536333c`。PR52 review5945712185の計画限定受入、comment6946260120の保全報告とCI0件を区別して継承。旧ZIPを今回再監査したとはしない。

今回は計画と非通信の無害な合成検査。方式B未採用、実験開始BLOCKED、実験NOT_TESTED、経路排他性UNKNOWN。全checkerのpermit=false。新規実験thread、秘密作成、A/B0/B1実験、設定変更なし。GitHub読取・提出、合成証拠保存は研究対象製品の試験ではない。

## B4の維持
B0は非特定の問いとA0/A1両方の再現監視。原文・要約・hash・所在・識別手掛かりを入力側へ渡さない。B1は独立した新規threadで明示提供したA1の再述と改訂。A1はB4新提案でB3継承としない。B1内の改訂は許容、独立2試行ではない。B0/B1は同一対象前後比較ではなく、因果・経路排他・自動共有の不存在を結論にしない。

正本は[旧PLAN](../h04b4-20261117/PLAN.md)と[RUBRIC](../h04b4-20261117/RUBRIC.md)。旧READINESS・原票・検査器は不変。本書は実物開始ゲートが未成立でも計画成果を限定審査できるが、未成立をPASSへしない。

## 成果物
ENVIRONMENTS / ROUTES / PROCEDURE / EVIDENCE / SCORING / CUSTODY / GATES / HANDOFF / RESULTS / INDEPENDENT-REVIEW、cases・check・sequence・archiveと試験記録。

## 容量・実行境界
案件専用作業領域。実装前空き34GiB、上限100MiB（checkoutと再取得・ZIP含む）、推定最大50MiB、余裕1GiB。小規模テキストのみ、共有tmp・既存原物を変更しない。子processのtimeout5秒、retry0。最大同時使用量の連続測定は未実施。合成試験の原文は公開された無害fixtureで、将来の秘密正解の代用品ではない。
