# H04-B5 実施環境・観測能力調査

対象正本: H04-B4 PR #52 final `dbe21c754d5af274c322819f0146f65bb536333c`、統合main `3136fc51a6f22b7f57144c94c08a11d0b28c9a7c`。調査日2026-11-18 UTC。これは設計資料でありA/B0/B1の実測記録ではない。方式B未採用、実験開始BLOCKED、経路排他性UNKNOWNを維持する。

## 実際に観測した範囲

11:35:48Zの調査用cloud executorはLinux 6.18.57 x86_64、Python 3.12.14、Git 2.52.0。環境一覧APIはcloudとconnected desktopをconnectedとして返したが、双方の能力discoveryはdeadline_reachedだった。この状態は対象アプリのインストール、ログイン、モデル、設定、実行準備の証明ではない。対象Desktopを操作せず、実験スレッドを作成せず、設定変更も行っていない。

公開文書と既存ソースを読んだ。tool metadataにはthread作成・読取、会話読取、Space等の能力があるが、公開された機能の存在と今回の実行対象のアクセス実証を区別する。会話読取にはページング、省略・切詰めがあり、完全な隠れたcontextの取得ではない。

## 主体の分離

- 実験実行主体: 次工程で選択・固定する製品と実行セッション。今回は未選択。
- 観測主体: 入出力と設定を採取する操作者／記録器。対象への追加context注入を禁止する。
- 採点主体: A0/A1を保有する別領域。B0へ原文・hash・locator・識別可能なヒントを送らない。
- 証拠監査主体: 保存先から直接再取得する別担当。別AI担当は人的第三者独立性を意味しない。

今回の調査担当は別AI枠だが、同一基盤・共有workspace・履歴継承あり。実験の独立性を証明していない。

## 環境別定義

|環境|実行主体・クライアント・モデル|認証／利用可能性|新規スレッドと初期状態固定案|観測ログ／取得不能|再現・保存上の制限|
|---|---|---|---|---|---|
|dot（八兵衛）|dot＋委任先を別記。今回の設計担当cloud executorは対象実験の代替でない。実モデル・版UNKNOWN|接続tool metadataのみ確認。実験用の接続・自動参照状態UNKNOWN|新規隔離threadの作成機能候補はあるが未実行。履歴継承指定だけでambient context遮断を主張しない|可視メッセージ／tool返却候補。隠れたcontext・自動注入全量UNKNOWN|新規IDでも同一dot資産を共有し得る。B0/B1専用化の審査が必要|
|ChatGPT Web|ブラウザ表示を記録、表示モデルと実モデルを別field。実モデルUNKNOWN|今回ログイン画面・設定を実査していない|新規chat、必要ならTemporaryのUnpersonalizedを候補。最初の入力前に設定を撮影・固定|UI入出力、利用可能ならexport。原UTF-8本文byte取得と完全性はNOT_TESTED|検索・Memory・project・plugin等の状態を個別記録。画面だけではbackend排他性UNKNOWN|
|ChatGPT Desktop|Desktopクライアントであり実行場所Localとは限らない。版UNKNOWN|connected desktopはアプリ起動確認ではない|Webと同じ機能を仮定せず、対象版で新規chatと設定表示を確認|UIキャプチャ候補。原byte export・内部動作UNKNOWN|Web手順を無条件流用しない。OS・app版・アカウントを固定|
|ChatGPT Work Web|Web UI、仕事の実行主体、選択executorを別記。実モデルUNKNOWN|本調査で対象Work session未取得|新規task作成とcontext継承／接続状態の記録案。通常ChatGPT Temporary仕様を流用しない|タスク記録・成果物の取得可能性を個別確認。隠れた入力UNKNOWN|cloud/localとブラウザclientを混同しない。可視ログだけで全入力確定不可|
|ChatGPT Work Desktop|Desktop clientと実行executorを別記。実モデル・app版UNKNOWN|同上|既存task再利用禁止、実行環境・継承条件固定案|native／cloud履歴の読取候補はあるが実験対象ログ未取得|Desktopという名称でlocal実行を認定しない|
|Codex Cloud|cloud job／agentとUIを別記。モデル・image・版UNKNOWN|本調査で対象job未作成|新規task、repo/ref、network、instructions、環境snapshotを固定する案|jobログ・成果物候補。完全なbackend promptやmodel実体UNKNOWN|repo内指示や取得資産も流入経路。既存repoを無条件にcleanとしない|
|Codex CLI local|local CLI process、remote model、委任executorを別記。版未取得|Desktop接続だけでCLI存在・認証を確認しない|新規session、cwd、指示、接続tool、許可、環境変数の安全な一覧を固定する案|CLI出力／許可されたsession export候補。非公開領域を探索しない|local process≠local model。別sessionでも共有指示・Memory等の有無UNKNOWN|

全環境でOS/client/version/model表示/実モデル確認根拠/auth状態/接続一覧/時刻・timezone/plan SHA/condition ID/スレッドIDを開始前原票へ保存する。秘密値・tokenは収録しない。確認不能はUNKNOWN、未操作はNOT_TESTED、取得失敗はMISSINGとし、説明文で原証拠を代替しない。

## 公式資料からの限定的根拠

2026-11-18に以下の公式Helpを取得した。対象accountの機能・設定を確認したことにはならず、dot/Work/Codexへは一般化しない。

- [Memory in ChatGPT](https://help.openai.com/en/articles/8590148-memory-in-chatgpt): プラン・地域・workspaceで機能が異なる。過去会話、Memory、指示、files、接続アプリ等が文脈となり得る。Sources表示は全要因を必ず示すものではない。OFFは過去記録削除や全内部context遮断の証明ではない。
- [Temporary Chat](https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt): 初回入力前にPersonalized／Unpersonalizedを選ぶ。後者は通常のMemory・指示・plugin利用を除く候補だが、限定的安全文脈等を含む完全遮断の保証ではない。会話開始後の切替不可。履歴保存で通常chatへ変換され得るため、証拠保存目的での変換は汚染審査が必要。未保存chatの再開不能性も証拠取得上の課題。
- [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt): project内の会話・files・instructionsが文脈となり、移動したchatはproject条件を継承し得る。共有projectのproject-only memoryでも内部の他会話は候補になる。project-onlyはB0/B1独立性の証明ではない。

## 次工程に必要な最小観測

1. 一つの候補環境を所有者が選び、秘密原文なしで利用可能性とraw本文取得方法を確認する。
2. 初期設定・新規ID・接続一覧を取得し、7経路のUNKNOWNを根拠付きで更新する。
3. B0の記録固定、保存先からの再取得照合、停止審査を終えるまでB1を作らない。
4. B1は独立新規threadで明示本文提供後の予定された再述・改訂を許容する。
5. 原byteを取得できない環境ではbyte一致判定を行わず、ゲートを停止する。

現時点で特定環境を実験開始可能と認定しない。UI_OFF、操作NOT_USED、TECHNICALLY_BLOCKED、EXCLUSIVITY_PROVENは別の主張であり相互昇格しない。
