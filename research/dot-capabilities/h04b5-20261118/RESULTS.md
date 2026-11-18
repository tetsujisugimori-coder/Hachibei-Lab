# H04-B5 結果

2026-11-18。対象は設計と非通信合成基盤。実A/B0/B1はNOT_TESTED、方式B未採用、開始BLOCKED、経路排他性UNKNOWN。

## 自己検査
事前固定cases.jsonの35件は35/35期待一致（各timeout5秒、retry0）。初回原票はevidence/first-synthetic.json、入力/checker/oracle SHA・時刻・stdout/stderr/exitを含む。sequenceは正常/空/途中/欠落/早期B1/再試行、archiveは正常/manifest欠落/改変/余分/path危険/CRC破損を検査。これは記録検査で、実サービス試験ではない。
既存H03〜B3の108対照とB4文書契約の正常+18除去対照は終了0。各コマンド原票はevidence/regression.json。既存原票・文書・workflowは変更なし。新CI/依存を追加しない。

## 独立審査・提出・保全
独立審査はINDEPENDENT-REVIEW.md。提出固定HEADの全byte照合、対象HEADのActions/checks/status件数、保存後実取得照合は最終PR報告で追補する。記録以前の時点ではNOT_TESTEDであり、合成成功を代用しない。

## 未検証
実clientの新規thread操作、実モデル版、内部取得経路、技術的遮断、秘密原票採点/保存、残余リスクの所有者判断と開始承認は未成立。実験準備と実験開始を分離する。Library ACL全体と長期保持保証はUNKNOWN。

## 独立審査後補訂
P2 2件・P3 1件を修正し同じ反例で再確認。初回不正PASS3件と旧期待は保持。旧追加8件は7/8一致、X08の識別不足による安全側仕様変更を明記、新規5件は5/5。主体/実施識別を明示したv2既存35件は35/35、期待判定不変。合成・文書限定受入YES、保全/提出後読戻しは別記。
