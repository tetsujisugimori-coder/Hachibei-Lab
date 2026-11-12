# 子プロセス専用 Temp 限定検証

Issue #27 / #20。PR #28 (merged) の読取診断を置換せず、別の opt-in 実験を追加。
新規依存、既存CI変更、システム設定、共有領域清掃なし。

## 再現条件
Linux、Python 3.11+、既存Node・PlaywrightとChromium実行ファイル。
事前に容量/inode/mount、利用中process（見える範囲）、書込認可を確認。
Windowsへこの手順を無検証で適用しない。個別実行を承認した案件だけに使用する。

```sh
python3 -B research/isolated-temp/tools/runner.py --root /YOUR/APPROVED/PROJECT/fresh-run --chromium /YOUR/EXISTING/chromium
python3 -B -m unittest discover -s research/isolated-temp/tests -v
```

rootは絶対パス・新規directory、/tmp内禁止、最低1GiB available。
TMPDIR/TMP/TEMP、Node compile cache、XDG cacheは子環境のみ。
既存binaryを明示し、downloadも別binaryへの自動fallbackもしない。
Chromium sandboxを有効のまま起動し、ローカル固定HTMLを読み取る。
新規profileを明示、ページ要求はabort。ブラウザ内部の通信全遮断を保証するものではない。
独自の削除処理はない。ただしPlaywright自身は自身の一時directoryを終了時にcleanupする。
一試行で失敗なら停止。成功した場合だけ別の新規rootで最大計3回まで。

原stdout/stderrとresultは指定rootに残り、非公開情報を含むため自動公開禁止。
出力のPASSは限定probeの完遂のみ。全ファイル追跡、永続性、quota、製品受入ではない。
manifestは256files、各8MiB、総32MiB上限。上限到達はBLOCKED。
process観測は見えるPID namespaceだけで、全host/残存子孫の不存在は証明しない。
後続修正版は所有process groupにTERM/KILLを送信し終了・残存を記録する。逃避した子孫やホスト全体はUNKNOWN。45秒、各出力1MiB、走査時間5秒・深さ8・項目256・各8MiB/総32MiBを上限とする。走査は別helperを期限で停止する。kernel D状態など停止不能は非PASSとし、全ホスト保証はしない。
保存失敗時は非ゼロ終了し、result欠落を成功と扱わない。

## 証拠と版
[報告](REPORT.md)、[原証拠hash台帳](evidence/private-source-manifest.json)。
今回の実ブラウザ試行は初版スクリプトで1回のみ、BLOCKED。
独立レビュー修正後の最終版はmock/unitでのみ検証し、実ブラウザは再実行していない。
公開ログはマスク加工物。非公開原票とはhashを区別する。

後続の修正・保存状況は [FOLLOWUP.md](FOLLOWUP.md) を参照。上記初回の実行結果は履歴として維持する。

保存result.jsonは常にPENDINGの暫定票。completion.json公開後、runner.read_completion(root)で3原票のSHA一致とcandidate結果を照合する。result単独やcompletion.candidate.jsonを成功として扱わない。
