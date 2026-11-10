# 台帳の項目と意味

Stage 1の登録を作り直さずsource_idを再利用する。Stage 2のsourcesは元台帳への参照と照合時点の必要メタデータで、別の資料実体の登録ではない。改名で採番し直さない。rule_idは条項を追跡する研究用の参照IDで、番号を付けたことによる正式制定はない。

| 項目 | JSON欄 | 記入と検査の境界 |
| --- | --- | --- |
| 資料ID・名称・著者 | sources.source_id/title/author | Stage 1 IDと照合。著者不明はUNKNOWN |
| 原典・版・所在 | edition/location/stage1_ref | 保存更新日時を本文版に変換しない |
| 確認状態と範囲 | body_check/check_scope | 全取得・部分点検・検索だけ・未読を区別 |
| 原文と引用位置 | citation.quote/start_line/end_line/snapshot_id/body_sha256 | 固定snapshotの実行位置・hashと照合。引用は選択した範囲だけ |
| 研究上の主張 | source_claim | 引用された資料の記述。解釈を足さない |
| 独自解釈 | interpretation | 記述からどこまで読み取るかを明記 |
| 対応する規則 | rule_id、rules.citation | 原文・所在・版を固定。公開計画の条項はPLAN-、正式規則ではない |
| 制定・権限 | set_by/set_at/authority_basis/approval_evidence | 記録者と制定者、作成日時と制定日時、本文自己申告と本人承認を分離 |
| 地位と適用 | authority_category/document_status/application_state | 草案、過去の試験、研究推論、提案、承認済み限定範囲、UNKNOWNを混同しない |
| 期間・範囲 | effective_from/effective_until/scope | 一部分の承認を文書全体へ、過去の期間を現在へ延長しない |
| 実際の運用 | runtime_verification | 保存・読解と実適用を別評価。今回の公開行動モデルはDESIGN_ONLY |
| 関係・強さ | kind/strength | 対応と採用の独立。直接対応でも正式効力を生まない |
| 限界と注意 | limitations/cautions | 反例、対象違い、原典未実見、解釈依存など |
| 残件 | next_questions/proposal_id | 証拠不足と採用判断を別の次作業として追跡 |

## 六つの関係分類

1. DIRECT：限られた命題が本文同士で直接対応する。全体一致・因果・規則効力ではない。
2. INDIRECT：比較材料、方法、部分的示唆となる。適用条件を解釈に記す。
3. BACKGROUND：成立背景を説明しうる。由来の断定には明示的参照等が必要。
4. POSSIBLE_CONFLICT：範囲や解釈によって両立しない可能性。未比較は対立確定にしない。
5. PROPOSAL：新しい規則等の候補。UNAPPROVEDの提案IDを必須とする。
6. UNKNOWN：本文・関係が未確認、または証拠が不十分。根拠の強さはINSUFFICIENT。

全6分類を資料へ無理に割り振らない。公開実データはDIRECT 2件、INDIRECT 2件。分類を試す合成負対照は実照合件数に含めない。本人限定照合の集計は別記録に保つ。

## 公開と非公開

publication_statusと台帳visibilityは独立検査する。公開集合はPUB-001/PUB-002だけを許し、同じSchemaに適合しても非公開データを公開入力として受理しない。公開CIは私有台帳を検査しない。スキーマ適合や短い秘密パターン検査は、公開許可や全秘密不存在の証明ではない。

本人限定台帳は同じ意味の項目をJSONまたは個票で管理できるが、実際の形式・検査方法・未検査欄を別に記録する。引用位置、現行版、承認原発言、出典リンクの実読は人の内容照合を要する。
