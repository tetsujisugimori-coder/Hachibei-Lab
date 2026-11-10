# Stage 3: 承認と判断時点の読取専用検証

## 範囲と原則

Stage 1 #3、Stage 2 #14 を含む main `8cf43cfa5d53cda13178ed7cf02dd5a747a40dc9` を基準にした研究基盤。Stage 2 の六つの事例は全て DESIGN_ONLY であり、六件の実運用成功ではない。正式規則、実承認、設定、権限、原本には変更しない。本ツールは実際の行動を発火せず、承認・取消・延長も発行しない。自律性や意識の証明ではない。

## 再現

Python 3.12以上。検証器は標準ライブラリのみ。

```
python -m unittest discover -s stage3/tools -v
python stage3/tools/approval.py stage3/synthetic.json
python stage3/tools/approval.py stage3/synthetic.json --explain
python stage3/tools/check_repository.py
```

Stage 1/2回帰には既存と同じ jsonschema==4.26.0 を使用する。正式CIは `.github/workflows/stage3-approvals.yml`。入力不正は構造化した不足結果とexit2、妥当な入力の非VALIDは通常の判定結果。成功したプロセス終了コードを有効な承認とは解釈しない。

## モデル仕様 v1.0

`synthetic.json` が完全な入力例。`approval.py:validate` が未知フィールドを拒否する実行可能な構造契約。

- 文書: schema_version、evidence_kind（SYNTHETIC/OBSERVED/DESIGN_ONLY）、observed_at、history_complete_through（不明ならnull）、approvals、decisions。
- 承認: 安定id、issuer、authority.statusとevidence、source、version、retrieved_at、events。VERIFIEDは調査者が提示した証拠主張であって本エンジンの本人認証ではない。実運用への許可判定に接続しない。
- 履歴: id、連続sequence、kind（GRANT/AMEND/REVOKE/CORRECT）、recorded_at、effective_at、expires_at、actions、targets、conditions、evidence。AMENDは範囲・条件・期限の完全置換。取消後の復活は新承認IDを必要とする研究上の保守的制約。
- 行動: id、action、target、approval_ids、proposed_at、decided_at、execution_at、completed_at、observed_choice、conditions、evidence。提案、判断、実行、完了を分離し、未観測はnullまたはUNKNOWN。
- 出典の文字列だけで真正性・権限・網羅性を確定しない。原本の確認、権限根拠、取得版を別途調査する必要がある。

## 時刻と履歴の契約

TZ必須ISO8601、秒と最大6桁小数。UTCへ正規化。開始は包含、終了は除外（[start,end)）。期限未設定nullと証拠欠測は異なる。入力順序を勝手に並べ替えず、連番欠落・重複・記録順/効力順逆転はCONFLICT。範囲は完全一致IDでありワイルドカードやURL接頭辞の推論はしない。条件値の型も一致必須。

記録時刻と効力時刻を別保存。遡及する効力、CORRECTはINSUFFICIENT_EVIDENCEとし、正式な遡及意味を創作しない。後日の訂正を過去の判断へ黙って反映せず保留理由を返す。履歴網羅性の宣言が判定時点に届かなければ不足。後日の履歴を含む監査は当時の可視性を完全再現したものではない。

判断時点と実行時点を別評価する。判断後取消なら判断VALID／実行REVOKEDになり得る。複数承認を自動OR結合しない。異なる結果は優先関係未確定としてCONFLICT。単一の不明・矛盾を別のVALIDで隠さない。これは研究用保守モデルであり、プラットフォーム規則の再実装や優先関係の新設ではない。

六事例それぞれの合成対応は `synthetic-case-scenarios.json`。実装依頼・不具合修正は対象内VALID、規則衝突はCONFLICT、曖昧指示はNO_RECORD、余暇は期限切れ、提案から実験への拡張はOUT_OF_SCOPEを固定期待値にする。元事例の実測と呼ばない。

## 出力

VALID / OUT_OF_SCOPE / NOT_YET_EFFECTIVE / EXPIRED / REVOKED / NO_RECORD / INSUFFICIENT_EVIDENCE / CONFLICT。各参照・根拠・時刻をJSONに残し、--explainで読める文章を出す。観測した選択は評価結果と別欄。consistencyのNO_MISMATCH_IN_RECORDED_FIELDSは記録された欄で不整合が見えないだけで、実運用の適法性PASSではない。

## 実際の記録の調査

公開Stage 1/2のPR・Issue本文・CI記録を読取照合した。Stage 2最終HEAD `7b2f7aad5b91bd2d1f867a43a5d27d7eec633808` の成果treeは現在mainと同一。PR #14 は2026-11-10T01:26:21Zにmerge済み。作成・更新・mergeやCI実行の事実は確認できるが、非公開の認証済み承認本文、判断瞬間、全取消履歴が公開原票にない。GitHubの実行時刻を判断時刻の代用にしない。実行できた事実を承認の根拠としない。

[実記録到達範囲](observed-assessment.json)は公開出典に限定。実運用の有効性はUNKNOWN、研究全体PARTIAL。私有資料の固有名・本文・識別子・内部URL・集計は本成果へ転記していない。全承認母集団や網羅率はUNKNOWN。安全な追加確認には判断・実行時刻、承認対象、認証根拠、完全な変更履歴を本人限定領域で照合する別工程が必要。

## 安全・検証限界

実サービス書込みを試験しない。合成データのみCIへ渡す。境界試験の成功は任意の入力で誤VALIDゼロを数学的証明しない。自由記述の意味理解、権限真正性、隠れた履歴、全実運用記録、全秘密不存在は証明しない。既存全ファイルSHA照合と変更パス制限を行う。マージ・正式ルール改訂・権限変更・実運用導入は対象外。

## Issue #17 境界補強（2026-11-11 JST）

入力schemaは1.0を保全。出力schemaを1.1とし、input_schema_versionを併記する。厳密な出力消費側は1.1対応が必要。既存decision/consistencyの意味は維持し、実行を主張し日時がnullの場合だけexecutionを不足オブジェクトとする（未実行のHOLD等は従来のnull）。

- decisionとexecutionを個別評価。実行日時欠落は `INSUFFICIENT_EVIDENCE` / `MISSING_EXECUTION_AT` であり、判断VALIDから代用しない。
- `consistency` は記録欄の矛盾だけ。`evidence_completeness` はモデル評価に必要な欄の不足一覧。`history_authenticity` は常にUNKNOWN。`history_coverage` は入力者の主張であり独立認証ではない。
- `overall` はPARTIALを維持する。全履歴・実承認の真正性や運用受入を認定しない。実行許可は一切発行しない。
- AMENDは直前の適用イベントの期限より**前**に効力を持つ場合だけ継続変更として評価する。期限と同時または後の場合は `AMEND_AT_OR_AFTER_EXPIRY` / INSUFFICIENT_EVIDENCE。後続AMENDでこの欠落を消さない。新規承認は別IDのGRANTで表す。
- 遡及的変更・CORRECTは引き続き不足、取消後変更はCONFLICT。期限nullはschema1.0の明示的無期限を維持し、キー欠落とは区別する。承認versionは出典版のラベルでありイベント版の真正性を認定しない。
- 将来の非遡及AMENDは適用前の評価を遡って変えない。これは研究上の保守モデルであり法的な変更・延長の一般解ではない。

`python stage3/tools/compare_boundaries.py` は固定main 3733a7e7に対する3反例の旧結果と新結果を保存する。既存CASE-001、既知実行、期限の前/同時/後、別ID再承認、時差、欠測、取消後等を検査する。Stage4・実運用接続は本修正に含めない。

独立監査でUTC正規化が表現範囲を越える年端（0001年/9999年）を追加確認。従来のOverflowErrorによる非構造化終了をValueErrorへ正規化し、CLIはINSUFFICIENT_EVIDENCE・exit2を返す。元の反例と修正後結果は `evidence/issue17/utc-overflow-review.json` に保全。誤VALIDの発生ではなく入力エラー契約のP3修正。
