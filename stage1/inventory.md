# Stage 1 公開用索引と資料台帳

確認日：2026-11-10 JST。総合 **PARTIAL**。この公開索引だけで5領域の棚卸し完了とはしない。

## 資料単位の記録

機械可読な公開索引は [public-index.json](public-index.json)。既存 ID は変更せず、[共通スキーマ](ledger.schema.json) の必須欄を資料ごとに持つ。

| ID | 原本 | 分類 | 本文確認 | 文書版 | 保存サービス revision | 適用状態 |
| --- | --- | --- | --- | --- | --- | --- |
| PUB-001 | [Issue #1](https://github.com/tetsujisugimori-coder/Hachibei-Lab/issues/1) | 研究計画 | VERIFIED_BODY | UNKNOWN | UNKNOWN | NOT_A_RULE |
| PUB-002 | [Issue #2](https://github.com/tetsujisugimori-coder/Hachibei-Lab/issues/2) | 今回の棚卸し計画 | VERIFIED_BODY | UNKNOWN | UNKNOWN | NOT_A_RULE |

2件は計画資料であり、江戸弁等の研究原本を2件確認したという意味ではない。[日付付き公開スナップショット](evidence/public-issues.json) と本文 SHA-256 で確認対象を固定する。GitHub の updated_at は保存サービスの revision ではない。更新後の原本とスナップショットが異なる可能性は、別の版として再検証する。

## 公開索引と本人用台帳の分離

- 公開用：公開済みと確認できる資料の書誌情報、公開証拠、構造、集計方法、残件のみ。
- 本人用：アクセス制御を確認した保存先に、資料名・原本所在・サービス識別子・本文版・採用証拠・確認結果を記録する。原本本文は転記しない。
- 本人用台帳の内部 URL、資料 ID、非公開資料名、本文・内容要約は GitHub に含めない。公開索引へ匿名 ID で流し込むこともしない。
- 安全な保存先を確認できないときは非公開情報を書き出さず、[空の構造例](private-ledger-template.json) と不足事項までにとどめる。
- 本人用台帳の取得・再照合結果は PRIVATE_EVIDENCE_ONLY。公開データの検査結果を、その中身の検証済み判定へ転用しない。

## 5領域と計数

対象は江戸弁・哲学・行動研究・憲法・規則運用のみ。領域別の到達点と数値は [domain-summary.json](domain-summary.json) に分離する。

計数単位は「確認対象に登録した資料」であり、語彙数、ページ数、検索ヒット数ではない。同じ資料を複数領域に割り当てた場合、領域別件数は合計しない。原本と複製は関係を記録して別資料として扱い、同一性確認前に統合しない。

- VERIFIED_BODY：取得した原本本文を全件読取したもの。採用・全履歴・引用原典の読了を保証しない。
- PARTIAL_BODY / SEARCH_ONLY / NOT_TESTED：未確認に数える。検索結果だけでは本文確認に数えない。
- 重複候補・矛盾候補：具体的な対応関係を登録した件数。未調査は NOT_TESTED、総数不明は UNKNOWN。0 と記録しない。
- 対象全体数が UNKNOWN なので網羅率を計算しない。取得不能を不存在としない。

## 完了条件

[受入条件と検証限界](verification.md) を満たした場合だけ Stage 1 完了を検討する。P2 は台帳構造の整備と実資料の完成を分けて判定する。網羅性・承認履歴・適用状態・非公開証拠の独立照合の不足を PASS としない。
