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
- 本人用構造例は空、旧 conflicts.md は元 commit と同一、README blob 不変、変更が stage1/ と新規の専用 CI workflow だけ。
- 公開文書・コード・専用 workflow の URL ホスト、クエリ、代表的鍵形式、メール形式、内部ID形式、ローカルパスを限定走査。コードを検査対象から除外しない。加えて目視で来歴と固有情報の不在を確認する。
- 前回 HEAD に固定した README と5つの既存証拠ファイルのバイト不変を確認。CI が接続しない非公開原本については、本人用台帳に読取範囲と再確認を記録する。

前回の14ケースと12限定検査は履歴として [unit.log](evidence/unit.log)・[validation.json](evidence/validation.json) に保存し、上書きしない。今回27ケースに拡張し、コード/専用workflowの混入検出、非公開URL・内部ID・メール・ローカルパス、専用以外のworkflow変更、README等の範囲外変更、固定証拠の改変を負対照で検査する。新しいローカル結果は [ci-preparation/](evidence/ci-preparation/) に分離。CI結果は run ID・attempt・HEAD・tree・workflow hash を結び付けた artifact で別に確認する。

## 手動・独立検査

公開成果物は既存公開 Issue と新規の構造・検証コードだけから作成する。非公開原本の本文・名称・内部 URL・ID を持ち込まない。限定パターン検査の PASS は全種類の秘密不存在証明ではなく、目視レビューと来歴確認を併用する。

本人用台帳の ACL、資料本文、承認・適用証拠は非公開側で確認し、公開ログへ原情報を転記しない。独立担当が確認できた範囲と未確認を正式レビューに分けて記録する。元資料は読取のみで、新規台帳の作成と原本編集は区別する。

最終コミット後に remote HEAD を再取得し、差分・ファイル一覧・README・正式 review の commit_id と一致することを確認する。版内のローカル検査ログには最終 commit の自己参照を作らない。最終 HEAD への結び付けは [PR #3 の正式レビュー](https://github.com/tetsujisugimori-coder/Hachibei-Lab/pull/3) と再取得記録で行う。

## CI と実施していない試験

開始 HEAD 48f5fe96aa6df48de64272f2eabd0bad66d92a5a には workflow がなく、main の2 workflow は別案件の path filter に限定されていた。既存条件・権限を変えず、[専用 workflow](../.github/workflows/stage1-inventory.yml) を追加する。原因調査・取得不能な設定と証拠は [ci-audit.md](ci-audit.md)。

専用 CI は pull_request の opened/synchronize/reopened と stage1/・専用workflow自身のパスに限定し、contents: read、checkoutの認証情報非保持、PR HEAD固定、全履歴取得を使用する。公開JSON・合成負対照・Git履歴だけを読み、本人用台帳・非公開サービスへ接続しない。ローカル成功を CI 成功に置き換えず、実行後に最終 HEAD の run/check/log/artifact を再取得する。

ブラウザ試験・能力評価・実機試験・行動実験は今回の対象外で NOT_TESTED。原本全体や外部サービス全体への非変更を、Git 差分だけで完全監査したとは主張しない。

## 今回の棚卸し受入ゲート

Stage 1 の目的は所在と適用関係を根拠から追跡できること。全研究原典の完全読解ではない。次の基準を個別に確認する。

1. 5領域の調査範囲、経路、時点、取得条件、取得不能範囲が明確。
2. 候補を安定 ID で追跡でき、原本/複製/異版と確認状態を記録。
3. 重要資料の本文照合があり、採用の明示的証拠・採用者・日時・範囲・期間・置換と、資料の存在を区別。
4. 母集団・網羅率を確認できるかと残件が説明され、未確認を検証済みとしない。
5. 公開/本人用の境界、原本・既存規則・README・過去記録の保全を確認。
6. 最終 HEAD と CI の実行状況、独立レビューを結び付ける。

未知母集団や未読参考資料が残るだけで自動的に失敗とはしない。各未知事項の所在・理由・影響が台帳で追跡可能かを評価する。正式採用そのものの認定、全資料の完全調査、限定的な技術受入は別の判定とし、独立レビュー前に総合 PASS や完了を先取りしない。

前回の Stage 1 完了 NO・限定マージ NO の判断は旧正式レビューに保持する。今回の判定は新しい原証拠と CI に基づいて再実施し、マージの最終判断はユーザーに委ねる。Stage 2、規則変更、能力評価、実験を開始しない。
