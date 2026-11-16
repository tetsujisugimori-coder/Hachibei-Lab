# H04-B3: 非破壊の経路監査と方式比較

基準main `303ff502124681a519b6da8cb64a0232c9a73968`、tree `9e6db21ed526688259f72588b894fe0aec080637`。PR48は取込み済み、元HEAD `b9e7153610c44d5e2ca3b11051c83a8dfd6d716f`。Issue45/47に関連する独立準備工程。既存B2検査器/READINESS/原票は不変。

## 結論境界
総合PARTIAL、実験開始BLOCKED、経路排他性UNKNOWN。実A/B0/B1、新規秘密正解、実験通信、設定変更、定期監視、自動開始は0。実用のツール読取りと実験通信を区別する。今回の監査表は対象実験での実適用についての判断で、一般的機能の一覧ではない。

## Evidence register
公開可能な根拠のみ。観測日時・主体・環境・根拠・理由をAUDIT.jsonの各セルに独立記載。そこにある日時は**資料に基づく審査日時**であり、実B0で観測した日時ではない。

|資料|確認範囲|限界|
|---|---|---|
|[PR48](https://github.com/tetsujisugimori-coder/Hachibei-Lab/pull/48)|GitHub実物のmerge/main/head/tree、独立審査COMMENT|mergeは実験承認ではない|
|[CI43863302198](https://github.com/tetsujisugimori-coder/Hachibei-Lab/actions/runs/43863302198)|成功、artifact14223843266の11,650bytes/digestメタデータ|合成12+42。実経路測定ではない|
|PR48独立レビュー5919689703|原ZIP保存後全byte/CRC10/manifest9/source5照合の記録|今回のB3で旧原票を再照合したとの主張なし|
|`../h04-issue45-20261116/ACCESS-AUDIT.md`|当時2Space一覧/ルートmeta/共有snapshotの限定観測|現時点ACL、子Page、Memory/索引/取得済コピー、B0遮断は未証明|
|`../h04b-20261116/READINESS.json` と `../h04b2-20261116/PLAN.md`|旧全開始条件・非通信境界・事前登録案|実適用ログではない|
|今回の本人依頼|非破壊の調査・合成・準備のみ許可、開始禁止|開始承認や設定変更の許可ではない|

公開仕様は一般機能の記述としてのみ扱う。2026-11-16に以下の公式現文を読取り、対象製品/plan/時点を限定した。新たなサービス内部仕様の確証・非秘密metadata追加観測は行っていない。過去のアクセス成功を現在の全経路の利用可能PASSへ外挿しない。実秘密・私有URL・所有者限定識別子は格納しない。

## 7経路×8次元
機械可読の原票はAUDIT.json。U=UNKNOWN、B=BLOCKED。

|経路|available|authorized|requested|accepted|applied|verified|measured|alternative_excluded|
|---|---|---|---|---|---|---|---|---|
|history|U|B|B|U|U|U|U|U|
|transfer|U|B|B|U|U|U|U|U|
|memory|U|B|B|U|U|U|U|U|
|shared|U|B|B|U|U|U|U|U|
|search|U|B|B|U|U|U|U|U|
|handoff|U|B|B|U|U|U|U|U|
|unidentified|U|B|B|U|U|U|U|U|

availableは実験で許された利用/遮断機能が存在するか。authorized/requestedは今回は禁止・未発行ゆえB。acceptedは拒否を実測したのではなく未発行ゆえU。applied/verified/measuredは実験未実施ゆえU。alternative_excludedは内部未知経路・候補網羅性未証明ゆえU。全セルに独立根拠欄を持つが、同じ根拠を複数の独立観測として数えない。

## 独立性のリスク
- history: 新規スレッドでも持込要約/初期文脈の監査が必要。
- transfer: 送信ログと受付、適用、再述の一致を別証拠にする。受付だけで受信者が利用したとは言えない。
- memory: 設定名や「使わない」という指示で技術遮断を認定しない。
- shared: 本人限定ACLは当該利用者の検索・内部転送・既存コピーの不存在を証明しない。
- search: 検索を指示しないことと、利用不可能・索引非収録・取得なしは別。
- handoff: 別担当・別スレッドでも引継ぎの有無と内容を監査する必要。
- unidentified: 観測不能な経路を排除したと主張できない。有限チェック集合を全内部経路へ一般化しない。

B0/B1は別の新規スレッドを要するが、それだけで独立性PASSではない。B0に正解の本文・hash・場所・要約を事前提供しない制御が必要。本人の禁止文と技術的制御を分離する。実B0入力/応答/時刻/版を本人限定原票として先行固定・保存後照合してからB1への明示送信。送信→受付→実適用→再述は別々の状態。再述成功だけでは取得経路や原因は確定しない。

## 方式A/B比較（両方とも未採用・開始禁止）
|観点|A:厳格経路排他比較|B:限定観測|
|---|---|---|
|研究価値|実際に排除できれば経路を限定した比較候補|観測できる明示提供前後の応答差を記録|
|必要証拠|全7経路の技術的制御/適用/独立検証、未知経路排除、新規性、正解隔離、先行固定、採点、保全|承認済明示提供内容・順序・別thread・固定採点・応答原票/欠測、汚染リスクの記述|
|不確実性|現在は制御/未知経路排除を確認不能、開始BLOCKED|未明示取得が残り得る。排他性・因果・自動共有不存在を主張不可|
|停止|欠測、未知経路、隔離違反、hash/順序不一致、制御喪失|同じ原票不整合/漏出/権限逸脱に加え、因果/排他性の主張が必要になったら停止|
|本人操作/判断|全技術条件の実証方法と権限、非公開正解管理者、開始を別承認|別研究計画の採否、限定結論・採点・対象・私有保管・明示提供を別承認|
|今回の提案|条件が揃うまでHOLD|最小次工程として**計画審査候補**を推奨、採用・開始ではない|

Bは「無情報B0」でなく「明示提供前」と呼び、成功を記憶/共有の因果証明にしない。AからBへ自動変更しない。両方式とも本人の別開始承認なしではBLOCKED。先にBの計画審査を選ぶか、Aの技術条件の解明を続けるかを本人が決める。

## 合成検査と受入
`audit.py`は全56セルの状態・日時/主体/環境/根拠/理由の形式と欠測を検査する。証拠参照の内容や真偽を認証せず、全セルPASSを入力してもevidence_authenticity/route_exclusivity UNKNOWN、experiment_start BLOCKED、method_adopted null。実測状態を合成で補完しない。新規機能の旧REDはNOT_IMPLEMENTED。正常/欠測/不正型/参照欠落/時差なし/方式自動採用を負対照とする。B2検証器は変更せず回帰する。

技術PASS、独立レビューPASS、最終HEAD正式CI成功、原証拠の保存後実再取得・独立照合PASSなら準備成果のみマージ推奨YES。実験開始判定とは別。CI/保全未完ならHOLD。実験は全未証明条件と別本人承認が残るためBLOCKED。

## CI・容量・保全
AGENTS/common-development-policy確認。事前空き23GB、inode約404万、専用作業領域、追加予算20MB/推定最大10MB/余裕1GB。削除・移動・上書きなし、共有tmp大量出力なし。既存11workflow不変。新規専用workflowはPR paths限定の標準Python1job/5分、B3/B2/B回帰と原ZIPのみ。browser/native/依存導入/実験通信なし。formalCI原ZIPを本人限定Libraryへ保存し、保存先から別ファイルに実再取得、別担当が全byte/SHA/size/CRC/manifest/事前期待集合/source HEAD/treeを照合。保全受付だけはPENDING。将来保持/ACL永続保証UNKNOWN。旧Space PENDINGと旧Library PASSは履歴として保持。

## 公開仕様の読取り（実適用証拠ではない）
- [Temporary chat in ChatGPT](https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt): Personalized/Unpersonalized選択を区別し、前者は既存memory等を使用し得る。限定的な安全・セキュリティ用途の過去文脈利用は別扱い。Temporaryという名称だけで無文脈としない。
- [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt): project-onlyでも同project内の別会話を参照可能。設定反映に数時間を要し得る、Work非対応の記述。Enterprise/Edu節のtemporary既定説明を他planやdotへ流用しない。
- [Memory in ChatGPT](https://help.openai.com/en/articles/8590148-memory-in-chatgpt): plan/地域/設定差、検索queryへのmemory利用、Sources表示の非網羅性を明記。表示がないことを経路不存在の証明にしない。
いずれもChatGPT一般機能の公開説明で、現在のdot・対象アカウントへの実適用・経路遮断を独立実測した証拠ではない。仕様の差・更新はUNKNOWNの解消とは別に追跡する。設定操作は行っていない。
