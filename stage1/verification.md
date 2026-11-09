# Stage 1 再受入の検証計画と結果

対象：既存 Draft PR #3、docs/stage1-source-inventory。前回レビュー HEAD と main の取得値は [baseline.json](evidence/baseline.json)。PR ブランチは前回レビューから変更なしだった。main の別案件追加は Stage 1 の実績として数えず、このブランチに取り込まない。

## 自動検査の対象と合格基準

Python 3 と jsonschema 4.x を使用する。今回のローカル環境は Python 3.12.14 / jsonschema 4.26.0。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s stage1/tools -v
PYTHONDONTWRITEBYTECODE=1 python3 stage1/tools/validate_inventory.py
git diff --check
```

- スキーマと必須項目、ID 一意性、既存 ID 維持。
- 公開2資料のタイトル・原本 URL・本文 SHA-256・サービス更新時刻と公開スナップショットの一致。
- 規則でない計画を CURRENT に昇格させない。サービス更新時刻を revision にしない。
- Issue #2 の旧阻害本文を保持し、新見出しと RESOLVED を確認。
- 5領域の公開計画参照件数を資料の domains から再計算。計画を研究原本件数に数えない。
- 不明な全体数から網羅率を作らない。私有件数は公開スクリプトで検証したと主張しない。
- 本人用構造例は空、旧 conflicts.md は元 commit と同一、README blob 不変、変更が stage1/ 内だけ。
- 公開データ/文書の URL ホスト、クエリ、代表的鍵形式、メール形式、ローカルパスを限定走査。コード中の検出パターンは自分自身を検出しないよう対象外とし、コードは目視確認する。

14ケース（正常1、負対照13）を実行。重複 ID、必須欄欠落、私有行、原本不一致、ハッシュ改変、根拠のない CURRENT、更新日時の revision 化、架空版、計画の原本への混入、架空網羅率、誤った件数、領域欠落、公開側の私有件数への格上げを検出した。[unit.log](evidence/unit.log) と [validation.json](evidence/validation.json) を参照。

## 手動・独立検査

公開成果物は既存公開 Issue と新規の構造・検証コードだけから作成する。非公開原本の本文・名称・内部 URL・ID を持ち込まない。限定パターン検査の PASS は全種類の秘密不存在証明ではなく、目視レビューと来歴確認を併用する。

本人用台帳の ACL、資料本文、承認・適用証拠は非公開側で確認し、公開ログへ原情報を転記しない。独立担当が確認できた範囲と未確認を正式レビューに分けて記録する。元資料は読取のみで、新規台帳の作成と原本編集は区別する。

最終コミット後に remote HEAD を再取得し、差分・ファイル一覧・README・正式 review の commit_id と一致することを確認する。版内のローカル検査ログには最終 commit の自己参照を作らない。最終 HEAD への結び付けは [PR #3 の正式レビュー](https://github.com/tetsujisugimori-coder/Hachibei-Lab/pull/3) と再取得記録で行う。

## CI と実施していない試験

Stage 1 のブランチには CI workflow はない。観測した main には別案件用の2 workflow があるが、対象パスが今回の stage1/ と異なる。今回 workflow や運用設定を追加・変更しない。最終 HEAD の workflow runs / check-runs / statuses を別途取得し、未実行を CI PASS としない。

ブラウザ試験・能力評価・実機試験・行動実験は今回の対象外で NOT_TESTED。原本全体や外部サービス全体への非変更を、Git 差分だけで完全監査したとは主張しない。

## 受入ゲート

| 条件 | 必要な根拠 | 未達時 |
| --- | --- | --- |
| P2 構造 | 資料ごとの全必須欄、安定 ID、追跡可能な原本・検証方法 | PARTIAL |
| P2 実資料 | 本人用を含む対象集合・領域別確認件数・未確認・重複・矛盾の根拠 | PARTIAL |
| 現行規則 | 文書版と承認・適用期間の原証拠。更新の新しさだけでは不可 | UNKNOWN / PARTIAL |
| P3 履歴 | 発生時刻の不明を保持、解消時点の証拠、Issue #2 と conflicts の状態整合 | FAIL または PARTIAL |
| 公開安全性 | 公開資料の来歴、差分検査、独立レビュー。未知の私有内容を公開して埋めない | NO MERGE |
| 完了 | P2/P3 解消、公開安全性、資料単位台帳と検証根拠、独立照合 | Stage 1 完了 NO |

現時点では網羅性と現行規則の採用証拠は未確定なので、Stage 1 完了は NO。構造・履歴だけの限定マージは独立レビューと残存リスクを踏まえて別に判断し、今回自動マージしない。
