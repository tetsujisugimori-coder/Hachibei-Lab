# 証拠保全と独立監査

適用正本はAGENTSとdocs/common-development-policy.md。今回の本人依頼は公開可能なB5計画・合成記録についてLibrary等承認済み経路を優先した保全を求める。本人限定領域へ新規証拠束を保存する。旧原ZIPの再生成・置換なし。公開Gitには秘密・私有locator・認証情報・将来A0/A1のhashを入れない。

1. 必要集合と原票/派生資料/検査結果を区別し、全path/size/SHA-256をmanifestに固定。
2. ZIPを安全に列挙し重複・危険path・CRC・manifest集合/size/SHAを保存前に別担当確認。
3. 保存receipt（対象/版/日時/結果）を私有台帳へ。receiptはbyte検証の代替ではない。
4. 別担当がLibrary保存物を別領域へ実取得し、原物全byte/size/SHA、全entry CRC、manifest集合/size/SHAを再計算。
5. 取得失敗BLOCKED、欠落/不一致FAIL、未実施NOT_TESTED。保存成功と再取得成功、監査担当の分離、ACL/長期保持を別欄に記録。

別AI担当・別領域でも同一基盤/account/履歴継承/共有workspaceの限界を記録し、第三者人的独立監査と呼ばない。ACL全体・将来保持を推測せずUNKNOWN。Windows二重保存は必須でない。保全PASSは削除/移動/実験/マージの許可ではない。

実験原票の将来保存では秘密分類と具体的な正解/取得/監査権限の別承認を要する。今回の公開合成束の保存実績を実験原物保全へ流用しない。原ZIP作成後のreceipt/読戻し票は別追補として保持し循環manifestを作らない。
