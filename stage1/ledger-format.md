# 資料台帳の記入規約

[ledger.schema.json](ledger.schema.json) は公開 JSON 索引用の機械可読構造。本人用台帳は同じ必須項目の意味を個票で管理するが、その独自形式をこの JSON 検査で検証済みとはしない。別の保存先・別のデータ集合として運用し、本人用台帳を Git に入れない。[private-ledger-template.json](private-ledger-template.json) は空の構造例で実資料ではない。

| 必須項目 | フィールド | 記入規約 |
| --- | --- | --- |
| 安定 ID | source_id | 公開は PUB-。本人用は既存の保存サービスの安定 ID を維持してよい。新規に研究用 ID を付ける場合のみ SRC- 等を使う。同じ資料は文書名変更で再採番しない。既存 PUB-001/002 を維持 |
| 資料名・分類・領域 | title, classification, domains | 書誌事実を記録。複数領域の重複計数に注意 |
| 公開可否・証拠 | publication_status, publication_evidence | PUBLIC の積極的証拠がある資料だけ公開用へ |
| 原本の所在 | original_location | 原本または候補の所在。非公開所在は本人用のみ。不明は UNKNOWN |
| 原本と複製 | original_copy_relationship | 候補関係と検証済み同一性を区別。未比較は NOT_TESTED |
| 文書版・改訂日 | document_version, document_revised_at | 本文に明記された版/日。保存サービス更新日時で代替しない |
| サービス revision・更新 | service_revision, service_updated_at | revision が未提供なら UNKNOWN。更新日時を版番号としない |
| 本文確認 | body_check_status, body_evidence, body_sha256 | 全文・部分・検索のみ・未検査を区別。ハッシュ未計測は NOT_TESTED |
| 承認履歴 | approval_history_status, approval_evidence | 本文の採用主張と独立の承認証拠を分離。履歴未検証は NOT_TESTED |
| 適用期間・状態 | effective_from, effective_until, application_state, application_evidence | UNKNOWN を空欄/推定で埋めない。CURRENT は承認証拠と開始日が必要 |
| 重複・矛盾 | duplicate_candidates, conflict_candidates | 対応資料と根拠を記録。未比較を「なし」としない |
| 未確認 | unknowns | 未解決項目と必要な証拠を明記 |
| 最終確認 | last_verified_at, verification_method | 時間帯付き日時、確認対象・取得方法・限界 |

UNKNOWN は値が不明、NOT_TESTED はその検査を実施していないことを示す。NOT_A_RULE は規則制定を目的としない公開計画などの区別。公開側に PRIVATE_EVIDENCE_ONLY とある場合は、詳細を秘匿しただけで検証済みを意味しない。

原本の内容・設定・承認状態はこの台帳を作成しただけでは変わらない。書出し複製を原本と呼び替えず、取得対象を記録する。私有台帳では同じ項目を表や見出しで管理してもよいが、全項目の対応と検査範囲を明示する。

## 本人用形式の対応と検証範囲

本人用個票の ID・資料名・分類・領域・所在・原本/複製・本文版/改訂日・保存 revision・本文確認・承認/適用・重複/矛盾・未確認・最終確認を、上表の同じ意味の項目へ対応させる。本人用のサービス ID は本人用内だけに保持する。公開用スクリプトはその ID、全個票、原証拠、共有設定を検証しない。

本人用の全文読解と公開形式の VERIFIED_BODY は、対象の全行を読めた証拠がある場合だけ対応する。全取得したが部分しか点検していない資料や部分読解は PARTIAL_BODY、検索結果のみは SEARCH_ONLY、未読は NOT_TESTED に対応する。サービスが本文全体を返したことと、実際に全行を読んだことは別である。独立形式への対応に不足がある場合も、構造検査の PASS で補わない。
