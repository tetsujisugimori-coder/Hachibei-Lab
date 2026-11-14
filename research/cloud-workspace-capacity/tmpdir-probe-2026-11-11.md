# プロセス単位 TMPDIR / cache の最小実測（Issue #20）

## 結果: PARTIAL

2026-11-11 UTC に、この変更専用の合成 fixture だけを実行した。既存案件のソースや過去の16条件テストは使っていない。

- **PASS**: Node 起動、npm 起動、npm cache 設定読取、`npm run build --offline` による最小 Node ビルド。Node の `os.tmpdir()` が専用ディレクトリと一致し、そこへ22 bytesの証明ファイルを書いた。
- **FAILED**: Chromium。Playwright は専用 TMPDIR に profile を作ろうとしたが、起動時に `socket() failed: Operation not permitted (1)` で終了。ページ検証・スクリーンショットは未実行。
- **FAILED**: WebKit。既存 binary の `libwoff2dec.so.1.0.2` が見つからず exit 127。ページ検証・スクリーンショットは未実行。
- **観測**: 選択した共有 browser cache、既定 npm cache、共有 Node compile cache の前後 metadata fingerprint は全て一致。全キャッシュの完全隔離や、内容 hash の一致を証明したものではない。
- `/tmp` は前後とも空き0 bytes。workspace側でNode/npmの小規模処理を継続できても、環境全体の操作可能性は保証できない。実際、この測定後に別の shell 起動が `/tmp/.git` の sandbox 準備で ENOSPC となった。保存済み証拠のコピー・本文作成だけは許可された実行経路で行った。ブラウザの再実行や共有領域の変更は行っていない。

## 実行物・再現手順

- `probe/run_probe.py`: 新規の run root を要求し、プロセスの環境変数を設定して6コマンドを順に実行。失敗もJSONへ保存し、どれかが失敗すれば終了コード1。
- `probe/smoke.cjs`: 最小HTML生成、TMPDIR一致確認、各engineで1ページの文字列確認とスクリーンショット。実ブラウザが起動できなければ成功扱いにしない。
- `evidence/tmpdir-run-01.json`: 実測値・コマンド・サニタイズ済みログ・生成物hash。
- `evidence/tmpdir-sha256.json`: probeソースと実測JSONのSHA-256。

実際の呼出し（repositoryルートから）:

```sh
python3 research/cloud-workspace-capacity/probe/run_probe.py \
  --run-root /workspace/scratch/e622c1e9421e/hachibei-capacity-controls-run/probe/run-01 \
  --playwright-module /opt/codex/cua_node/lib/node_modules/playwright \
  --chromium /tmp/castle2d-browsers/chromium-1194/chrome-linux/chrome \
  --webkit /tmp/castle2d-browsers/webkit-2215/pw_run.sh \
  --browser-cache /tmp/castle2d-browsers
```

再実行には**未使用**のrun rootと、その環境で確認した既存binary/moduleを指定する。例示したパスの存在や互換性を他環境で仮定しない。ダウンロード・install・sudo・共有ファイル削除はスクリプトに含まれない。既存パッケージやbrowser cacheは実行・参照のみ。

設定は子プロセスに限定: `TMPDIR/TMP/TEMP`, `npm_config_cache`, `NODE_COMPILE_CACHE`, `XDG_CACHE_HOME`, `XDG_CONFIG_HOME`, `HOME` をrun root配下に設定。`PLAYWRIGHT_BROWSERS_PATH` は既存browser cache、`PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`。shellのexportやユーザー/global設定は変更しない。npmは `RUN_ROOT/npm-cache` を返した。npm package取得・install cache経路の検証ではない。

バージョン: Node **v24.22.1**、npm **11.9.0**、Playwright **1.57.0**。選択した既存browserのrevisionはChromium **1194**、WebKit **2215**。ブラウザAPIからのversion取得は起動失敗により未確認。Playwright 1.57.0の標準revision（1200 / 2227）とは異なるため、明示executablePathの互換性も未証明。今回の直接エラーはそれぞれsocket権限・動的library不足であり、互換性問題がないとの結論ではない。追加取得による是正は今回の測定範囲外。

## 容量・inode実測

| 対象 | 前 available bytes | 後 available bytes | 前 free inode | 後 free inode |
| --- | ---: | ---: | ---: | ---: |
| workspace overlay | 14,410,805,248 | 14,406,004,736 | 3,634,796 | 3,634,064 |
| shared `/tmp` tmpfs | 0 | 0 | 1,238,467 | 1,238,467 |

- workspace総量: 67,586,535,424 bytes / 4,194,304 inode。
- `/tmp`総量: 5,225,709,568 bytes / 1,275,808 inode。容量枯渇であってinode枯渇ではない。
- 所有run root集計（結果JSONを書き込む直前）: 740 entries、logical 3,271,289 bytes、allocated 4,833,280 bytes。ディレクトリ自身のsize/blockも含む。filesystem差分は他の同時処理を含み得るため、このタスク単独の使用量とは見なさない。
- 実行後の別読取: Node cache配下712 entries、regular-file合計3,182,564 bytes。npm cache配下4 entries、regular-file合計2,596 bytes。TMPDIRの証明ファイルは22 bytes。Node compile cacheの専用領域への実書込を確認した。

共有cache fingerprint対象（entryの相対名・mode・size・mtime_ns・ctime_nsをソートしてSHA-256化、atimeと内容は対象外）:

| 対象 | entries | allocated bytes | 前後一致 |
| --- | ---: | ---: | --- |
| 選択browser cache | 551 | 1,231,667,200 | true |
| 既定npm cache | 1,586 | 298,921,984 | true |
| `/tmp/node-compile-cache` | 18,979 | 157,745,152 | true |

これは限定対象の前後観測であり、途中の一過性変更や別の未観測cache、内容の同一性を保証しない。共有cacheの個別ファイル名や中身は証拠へ出力していない。

## 保存と削除の境界

実行ディレクトリは `hachibei-capacity-controls-run/probe/run-01`。この試験だけが所有し、他案件のディレクトリとは分離。ローカルのログ、結果JSON、HTML、Node/npm cache、profileの残存情報は保持した。browser launch失敗後にPlaywright自身が**自身の作成した**一時ディレクトリを通常終了処理として片付けたことはログに記録される。

独自のcleanup機能・自動削除・共有領域削除は一切実装または実行していない。後日の手動整理は所有範囲と証拠保存を確認し、承認された場合だけ行う。保存先がworkspaceであることは再起動耐性の証拠ではない。GitHub提出拒否の原因解明、他案件の完成判定、本番アプリのbuild/ブラウザQAとは無関係。

## 測定後のhardening（run-01とは別検証）

run-01の証拠と実行ディレクトリは変更せず、測定後にrunnerを修正した。

- run rootの全既存path componentを解決前に確認し、symlink（danglingを含む）を拒否。`..`正規化後の実体pathが `/tmp` 配下なら拒否する。検査と作成の間に悪意ある別プロセスが親ディレクトリを置き換える競合までは防がないため、管理下のworkspace親を前提とする。
- 各commandを独立session/process groupで開始。timeoutだけでなく正常終了後も、そのgroupに残った子孫processだけを停止する。外部のprocessを名前検索して停止しない。別sessionに自ら離脱する子孫は保証対象外で、出力pipe待ちにも上限を置く。
- `probe/test_probe.py` のsynthetic検査3件がPASS: 通常終了時の残存child停止、timeout時のchild停止、symlink・`..`・既存root拒否。別sessionのsentinelが動作継続することを両process検査で確認した。共有 `/tmp` への書込み・browser起動は行っていない。検査用ファイルも保持した。
- 実行: `PROBE_TEST_ROOT=/workspace/scratch/e622c1e9421e/hachibei-capacity-controls-run/probe/hardening-01 PYTHONDONTWRITEBYTECODE=1 python3 research/cloud-workspace-capacity/probe/test_probe.py`。結果は `evidence/tmpdir-hardening-tests.txt`。
- **変更後runnerでNode/npm/browser smoke全体は再実行していない。** 上記run-01のPASS/FAILEDは変更前runnerの測定結果である。特にブラウザの再実行は未了。
- `tmpdir-sha256.json` は `measured_run_01`（測定時のhash）と `current`（hardening後）の2系統。測定時runnerのhashを現在のrunnerのhashと取り違えない。次の実行から結果JSONにもrunner自身のhashを記録する。
