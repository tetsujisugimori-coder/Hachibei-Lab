# 原証拠取得仕様

## 実行前
計画commit/tree/文書SHA、条件ID、run ID、実行/観測/採点/監査主体、client/表示model/version、実行場所、確認日時、設定snapshotと取得元、新規thread確認（初期文脈・持込添付・handoff有無）、認可範囲を私有台帳に記録。不可視model/内部設定はUNKNOWN。表示OFFと適用・検証済遮断を別欄にする。

## 実行中
各イベントにseq、入力全文/出力全文の原文字列と原transport、送信/受付/応答/停止操作、server timestampとobserver timestamp（TZ、精度、時計差UNKNOWNを明示）、error、retry、設定差、route観測・根拠、停止判断を付す。無言のtrim/Unicode正規化/LF変換/コード囲み除去禁止。transport JSONから本文を抽出する処理を版固定し、envelopeと抽出byteの両方を保持。

画面キャプチャは可視表示の証拠で原文字列全byteを保証しない。UIコピーも末尾LF/不可視文字/切捨てを確認できなければ参考のみ。API応答はそのAPI操作の原票で、通常UI/dotへの一般化禁止。エクスポートは対象ID・取得日時・収録範囲を検査し、生成遅延/非収録項目を明示。いずれもバックエンド完全ログと称さない。

現時点、対象UIの構造化assistant原文字列を末尾LFまで取得する方法は実物未点検（NOT_TESTED）、成立可否UNKNOWN。この阻害を説明文・画面転記・別APIで埋めずG6は未成立。

## 実行後
必要集合: plan/conditions/environment/access/new-thread、入力/受付/応答/操作event、A0/A1私有正解、個別採点/人手審査/停止票、欠測一覧、manifest/sha一覧、保存receipt/取得/照合票。3応答枠を台帳で維持しMISSINGを除外しない。
COMPLETE=取得済み必要集合成立、MISSING=試行したが原票欠落、NOT_TESTED=未実施、UNKNOWN=根拠不足、FAIL=矛盾実証。保存PASSは内容照合や真正性PASSではない。

今回の合成票は入力・期待・実結果、input/checker/oracle SHA、開始終了UTC、command stdout/stderr/exit、timeout/retryを保存。実サービスの原証拠ではない。後付け説明は派生監査資料として原票と分ける。

## 補訂 v2
executed=trueと非空actorが確認できない原票をPASSとしない。executed=falseはNOT_TESTED、空outputはMISSING。旧入力はevidence/cases-original.jsonへ保存し、35件の期待判定を変えず合成実行識別だけを追記したv2を別版化。既知の停止兆候は識別不足で隠さない。
