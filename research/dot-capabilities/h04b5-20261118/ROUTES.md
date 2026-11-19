# H04-B5 7経路アクセス条件・観測可能性台帳

正本: H04-B3 `research/dot-capabilities/h04b3-20261116/PLAN.md` / `AUDIT.json` とH04-B4。名称・集合は以下7件のまま。今回の読取調査は実験用経路遮断試験ではない。全経路の取得排他性はUNKNOWN。

B3でavailable/authorized/requested/accepted/applied/verified/measured/alternative_excludedを分離した契約を継承する。過去のUNKNOWNまたは未実験BLOCKEDを新しいアクセス実測PASSへ変更しない。下表の「可能」は候補・リスクであり現在アカウントで実証した動作ではない。

|正本経路|読取／書込|自動／明示参照|制御できる候補範囲|遮断の検証方法と限界|取得可能な証拠候補／取得不能|B0への混入リスク|B1への混入リスク|
|---|---|---|---|---|---|---|---|
|history|可視会話読取機能候補あり。対象履歴の読取・編集・削除は未実施|過去会話参照は製品・設定依存。明示読取と自動参照を分離|新規thread、履歴継承なしの明示設定、対応UIのUnpersonalized候補|新規ID・設定画面・公開仕様を確認。非表示の全context不在は証明不能|可視メッセージ、設定、作成receipt／省略された内容・内部入力全量UNKNOWN|A0/A1や識別ヒントを既存履歴から継承する可能性|B0結果を継承すれば独立条件違反。B1内予定改訂は違反でない|
|transfer|明示入力・添付の読取候補。送信は今回未実施|手動転載・添付と自動引継ぎを分離|入力allowlistと全文固定、clipboard等の混入を確認|送信前原稿と送信raw byteの比較。未記録引継ぎはUNKNOWN|送信全文・添付hash・受付記録／隠れた変換・省略UNKNOWN|原文・hash・locator・正解ヒントの転送禁止|明示A1だけ許容。B0履歴の無断転送は禁止|
|memory|対象製品のMemory読取・書込権限はUNKNOWN。今回変更なし|自動personalization、明示参照双方が候補|対応UI設定の記録。OFFは削除／安全文脈の排除を意味しない|設定ON/OFFの表示、対象版公式仕様。Sourcesにないことは不存在証明でない|設定キャプチャ／全内部Memory使用・漏れのabsenceはUNKNOWN|A0/A1または対象特定情報の自動参照|B0由来のMemory共有。B1内容を以後再利用するリスク|
|shared|Space/project/files/接続アプリの読取・編集は個別権限依存|自動contextと明示file取得を別記|共有資産を使わない設計、対象外project。ACL変更は行わない|選択project・添付・接続一覧の可視証拠。複製・index・広域ACLはUNKNOWN|asset list/取得receipt/可視ACL／未列挙コピー・全index UNKNOWN|非公開照合原文が共有資産から流入|同じprojectやSpaceのB0結果が流入|
|search|検索toolが存在することと対象実験の利用可否を分離。index書込未調査|明示検索と自動検索の両方を区別|tool不使用、利用可能なら対象設定のOFF。秘密ヒントをqueryへ含めない|tool call/query/resultログ。ログなしで未使用を断定しない|公開検索応答・query・時刻／隠れたquery rewriting・全参照UNKNOWN|原文や識別ヒントを検索取得。検索queryの外部送信もリスク|A1以外の本文やB0記録を検索取得|
|handoff|委任の指示と戻り値読取候補。今回実験委任なし|自動delegationと明示task委任を別記|委任なしを条件化、必要なら新規独立executionと入力allowlist|委任ID・入力全文・継承設定・戻り全文。ambient contextのabsenceはUNKNOWN|可視handoffログ／委任先隠れたcontext・共有基盤 UNKNOWN|採点担当が持つA0/A1を実行側へ渡すことは禁止|B0からB1への履歴継承、別taskを別環境と誤認する危険|
|unidentified|読取／書込UNKNOWN|自動／明示UNKNOWN|未知経路を遮断済みとしない。異常時停止|予期しない再現・設定差・欠測を監視。未観測は不存在ではない|異常原票・欠測理由／完全な経路列挙・因果同定UNKNOWN|原文再現の原因を既知経路へ決め付けない|通常の明示再述と未知混入を区別。未知要因は残す|

## 状態と操作制限

- 現在設定の実査: NOT_TESTED。接続一覧の機能表示は各経路の実験用認可・適用・遮断PASSではない。
- 技術遮断／排他性: UNKNOWN。UI_OFF、操作上NOT_USED、技術的遮断、排他性証明を別fieldに記録する。
- B0/B1実行: NOT_TESTED、実験開始BLOCKED。今回秘密本文を生成・送信していない。
- B0回答は対象不特定応答であり特定原文理解の証拠でない。A0/A1のいずれかの一致候補は停止審査。B1へ正当に提供した本文の再述はB0の秘密再現と同じ理由で停止させない。
- B0/B1を同じ原文の厳密な前後比較とせず、7経路の排他性・因果を主張しない。

B3の旧Space限定ACL観測、過去接続状態、旧UI確認を現在状態や全コピー不存在の証拠へ流用しない。各実験直前と直後の設定差分を取得し、差分あり・取得不能・中断は停止審査へ送る。
