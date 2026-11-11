# Stage 3 限定実証拠評価

Issue #25。基準は merged PR #24、commit `55479ddee78f6ede43cbe550d8703ac1a8a66591`、tree `02f98ee4c7de1c9e74e0f24be6bd6b423068a703`。

**総合 PARTIAL / 限定技術受入 PARTIAL / 実運用 HOLD。** 合成試験の成功は実承認の受入ではない。原本保全先が未確認であるため、取得した実原本・実データ入力・内部台帳・個別取得記録をこのリポジトリ、CI、ログへ保存しない。今回の実記録評価はメモリ上で行い、公開成果は固定語彙の判定と一般化した限界のみとする。

## 実証拠の対象と到達範囲

指定対象PR #24の公開PRメタデータ、review、関連イベントを読取対照とした。ReviewのCOMMENTED、GitHub APPROVED、mergeの成立、本人の明示承認を別の記録として扱う。指定対象のreview状態はCOMMENTEDとして観測され、merge成立も観測されたが、これらを本人の明示承認へ変換しない。

本人のreview/merge明示承認原本はNOT_OBTAINED。この結果は「承認が存在しなかった」とする証明ではない。現在の検証依頼を過去の操作承認に遡及適用しない。会話取得は可視範囲に限られ、別チャット、未取得添付、削除、未ミラーの範囲を網羅できない。私的検索詳細、本文、識別子、取得URL、実データ件数は公開しない。

GitHub記録上のreview対象HEADとmergeの技術的対応は観測された。アカウント表示、OWNER association、現在の認証接続主体の一致、署名検証成功というAPI表示は、それぞれ異なる観測・サービス主張であり、当時の本人性・権限委譲・有効な承認の証明ではない。

## 情報源の能力と限界

- 取得経路は接続済みGitHubのGET限定ツール。公開可視のPR、review、イベント、commitを返す。権限・設定・承認・取消のAPIは変更していない。
- REST型のJSON内容と、connectorによる正規化reviewモデルを照合した。正規化モデルでは元のreview内容に存在する一部の識別・commit・association欄が省略される。正規化後のnullを「情報源に元から存在しない」と扱わない。
- API内容を返すツールのJSONは観測できたが、HTTP wire bytes、headers、Link、ETag、transport署名は取得していない。再JSON化した文字列のハッシュをHTTP原本のハッシュと呼ばない。
- 可視の限定endpointで連続ページと空の終端ページを読取確認した。これを過去の編集、削除済み、秘匿、保持期限外、別チャネルの変更・取消まで含む全履歴の証明にしない。
- 原本SHA-256照合は実データではNOT_TESTED。個別の取得日時・元記録日時・取得範囲を永続receiptとして再読戻しできる状態にはしていない。安定snapshotと応答headersがないので取得中の変更も排除できない。
- 認証されたアクセス範囲と実際の操作者、承認時点の権限、過去の全文、全取消母集団はそれぞれUNKNOWN。

## 既存検証器への接続

`stage3/tools/observed_evidence.py` はJSONをstdinから読取り、メモリ上で検査する。ネットワーク・ファイル書込・行動APIを持たない。情報源からの取得と意味づけは呼出側の観測主張であり、このツール自体が認証した情報ではない。

- `build_ledger` は各観測を既存foundation v1.0の `OTHER` recordへ対応付ける。native ID、改訂、前レコード、元記録/取得時刻、対象を内部台帳で保持するが外へ出力しない。
- 未保全の原本・正規化artifact・page receiptを捏造しない。artifact pathはnullで、既存`evidence.audit`が欠落を検出する。内部台帳/詳細reportを公開してはならない。
- COMMENTED/APPROVED/mergeからGRANTを生成しない。本人の明示承認の有効期間、条件、判断時刻が未取得の場合、無期限やmerge時刻で補完しない。承認モデルへの意味論bindingはNO_SEMANTIC_BINDINGS、モデル判定はNOT_EVALUABLE。
- optional `model` を与えた場合は既存`approval.evaluate`を実行する。そのVALID等はCONDITIONAL_ONLYに隔離され、証拠の真正性や権限へ昇格しない。モデルの全文・識別子・件数は出力しない。
- 原本byteの指定とSHA-256がある場合でも、ハッシュMATCHは供給されたbyteと供給されたdigestの比較だけ。SOURCE_BYTESという入力者分類、正規化の意味的一致、原本真正性、永続保全を認証しない。一部の原本が欠落すれば全体MATCHを返さない。
- source/actor/scope欄の一致はCLAIMEDまで。期待actor/target/actionとの矛盾はCONFLICT。一方の不足をもう一方の完全な欄で補わず、実行後に記録された承認を遡及対応させない。変更・取消・削除があっても有効なgrant履歴を創作しない。

## 入出力契約

schema_versionは1.0。strictな実行可能契約は`validate`。未知キー、重複JSONキー、非有限数、Unicode不正、無timezone時刻、未来取得、bool件数、kind/state不整合を拒否する。stdinは4 MiB、配列は1,000要素まで。

必須トップレベルはschema_version、evidence_kind（SYNTHETIC/OBSERVED）、observed_at、window、source、records、pages、expectation、model。

- source: controller、acquisition、access_scope、from_origin、revisions_visible、deletions_visible。全て入力者の説明・主張。
- record: id、native_id、revision、previous_id、kind、actor、target、action、state、recorded_at、retrieved_at、representation、bytes_base64、sha256。未取得byte/hashはnull。
- representation: SOURCE_BYTES、CONNECTOR_JSON、NORMALIZED_OBSERVATION、NOT_OBTAINED。再構築したJSONをSOURCE_BYTESにしない。
- kind: REVIEW、EXECUTION、EXPLICIT_APPROVAL、AMENDMENT、REVOCATION、DELETION、OTHER。自由文を自動的に承認と解釈しない。
- page: cursor、next_cursor、retrieved_at、record_ids、reported_total。各取得経路を混在させて完全なchainと称しない。未保全receiptはINCOMPLETE。
- expectation: approver、actor、target、action。不明値はnull。一致しても本人性・当時の権限・実行の適法性は確定しない。
- model: 既存モデルv1.0、またはnull。実証拠からモデルを創作しない。

出力は固定キーと固定enumだけで、原文、自由記述、ID、取得URL、時刻、hash、実データ件数を返さない。エラーでも原文/例外/path/tracebackを返さずexit2。正常exit0は監査の実行成功だけで、承認PASSではない。`public_projection`は出力方式の表示であり、秘密不存在の普遍証明ではない。

## 再現と公開境界

```sh
python -m unittest discover -s stage3/tools -v
python stage3/tools/observed_evidence.py < stage3/real-evidence/synthetic/snapshot.json
python stage3/tools/check_observed_repository.py
```

CIへ渡すのは`synthetic/`のみ。実入力をコマンド引数、shell履歴、tee、trace、CI artifactsへ入れない。内部APIを直接呼ぶ場合も詳細台帳を表示・保存せず、固定語彙の`assess`結果だけを扱う。input kindをSYNTHETICに変更するだけでは実データを公開可能にしない。

固定base以降の全既存ファイルをworkflow以外SHA-256で照合し、変更pathを限定する。既存foundationの回帰と保全checkも維持する。bounded marker scanと合成canary試験は一定の漏洩を検出するが、全ての秘密や意味的漏洩の不存在証明ではない。

## 未解決と次工程

承認済みの非公開・永続保管先、そのアクセス範囲・保持条件が未確認。ローカル共有tmpを保管先と見なさず、新しい永続先への保存や移動は実施しない。原本、個別取得receipt、hash、実データ詳細台帳、監査の再現可能な保全は未完了。この保全制約は試験成功で解除しない。

次工程は、保管先の明示承認と私有範囲/保持の確認後、原本を新規取得しappend-onlyに保全・再読戻し照合すること。そのうえで承認時点の本人性と権限、承認条件と有効期間、変更/取消/削除、判断/実行時刻を別々に検証する。既存の観測を原本へ格上げしない。

今回の成果に対する限定マージ推奨はNO。基盤実装・合成試験成功、独立レビュー、CIの結果は別途PRに報告するが、保全を含む実証拠受入条件の不足を残す。正式規則・設定・実権限・既存承認履歴は不変。自動マージ・実運用接続は行わない。

## 追加の著者反例と環境制約

初期commitに対する追加の著者確認で、承認側のactor欠測、実行側のaction欠測、実行後の承認記録、承認/実行state不明がある場合にも対応関係をCLAIMEDと表示し得た。権限付与は前後ともHOLDだったが、現在は不足をUNKNOWNとして維持する。合成before/afterを`correspondence-counterexamples.json`に残す。この著者確認を独立レビューとは呼ばない。

追加回帰の途中、共有一時領域の容量不足により既存fixture書込みでErrno28となった試行がある。元失敗ログを上書きせず、共有領域を削除・移動しなかった。新設した作業用合成TMPDIRに変更して再検証した。これは実原本の保管先承認や保全完了を意味しない。製品assertion失敗とは区別する。

## 独立レビューで指摘された入力契約

独立レビューでP2を確認した。初期wrapperの`validate`がoptional modelを検査せず、不正modelを直接validateできた。またmodel内のarrayがwrapperの1,000要素上限の対象外で、1,001件の合成decisionもCLI exit0となった。実運用はHOLDのままだったが、入力契約と文書に不一致があった。

現在はwrapperのvalidateから既存承認モデルのvalidateを呼び、model内の全arrayにも同じ上限を適用する。元の承認検証器は変更しない。approvals、decisions、events、actions、targets、approval_idsの1,000/1,001境界、不正model、CLIの固定語彙エラーを検査する。`compare_review.py`は固定の修正前commitと現在コードに同じ合成反例を与え、RED/GREENと正常な上限値の維持を再現する。`independent-counterexamples.json`をCIで照合する。原指摘は修正後も消去しない。
