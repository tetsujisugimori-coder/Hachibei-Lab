# 容量管理 guard v0.1

[Issue #20](https://github.com/tetsujisugimori-coder/Hachibei-Lab/issues/20) の継続実装。
[PR #21](https://github.com/tetsujisugimori-coder/Hachibei-Lab/pull/21) の記録から、削除を伴わない検証可能な機能だけを切り出す。

- [共通仕様](specification.md)
- [今回の隔離実測と限界](tmpdir-probe-2026-11-11.md)
- [以前の山中城ケース記録](yamanaka-stage3b-2026-11-11.md)

## 実行

Linux / Python 3.11+ / Git。追加Pythonパッケージ不要。CLIの明示実行だけであり、導入・常駐・自動削除・グローバル設定変更は行わない。

読み取り専用のチェック（例の絶対パスを自分の許可済み領域に置換）:

```sh
python research/cloud-workspace-capacity/tools/capacity_guard.py check \
  --workspace /workspace/my-job --repo /workspace/my-job/repo
```

子プロセスを専用一時領域で実行:

```sh
python research/cloud-workspace-capacity/tools/capacity_guard.py run \
  --workspace /workspace/my-job --repo /workspace/my-job/repo \
  --run-root /workspace/my-job/capacity-runs --task build -- npm run build
```

`--repo` はGitのルート必須。run-rootはworkspace配下の専用ディレクトリ、repo外を推奨。`/tmp`配下やsymlink経由は拒否する。repoとrun-rootが測定workspaceと別deviceの場合も拒否する。実行ごとに新規ディレクトリを作り、上書きしない。

`/tmp` がSTOPなら、TMPDIRをworkspaceへ変更しても通常runは開始しない。TMPDIRを無視するツールや実行基盤の使用を排除できないためである。今回の小規模probeは、明示承認された隔離研究として別スクリプトで実測したもので、guardのSTOPを解除する機能ではない。

親shellの環境、設定ファイル、既存キャッシュの場所は変更しない。子の `TMPDIR/TMP/TEMP`、`NODE_COMPILE_CACHE`、`npm_config_cache` のみ専用化する。PlaywrightブラウザインストールとXDG cacheは継承するため、全ツールの完全隔離は主張しない。

## 未提出成果のチェック

Gitのdirty、cached upstreamとの差を確認。remote-tracking upstreamがありdirty=falseかつahead=0のときのみ `CLEAN_CACHED_UPSTREAM`。**ネットワークを照会しないため、遠隔の現在状態はUNKNOWN**。ローカルbranch upstreamは提出済みの根拠にしない。

それ以外は保全manifestなしではrunを拒否する。自動bundle生成・patch生成・外部転送は行わない。別の許可済み手順で保全し、以下のmanifestを作る:

```json
{
  "head": "CURRENT_FULL_HEAD_SHA",
  "bundle": {"path": "/workspace/safe/snapshot.bundle", "sha256": "SHA256"},
  "staged_patch": {"path": "/workspace/safe/staged.patch", "sha256": "SHA256"},
  "worktree_patch": {"path": "/workspace/safe/worktree.patch", "sha256": "SHA256"},
  "untracked": [{"source": "new.txt", "path": "/workspace/safe/new.txt", "sha256": "SHA256"}]
}
```

`--preservation-manifest /workspace/safe/manifest.json` を付ける。

- bundleは `git bundle verify` と `list-heads` で現在HEADを照合。
- staged patchは `git diff --cached --binary --no-ext-diff --no-textconv HEAD`、worktree patchは `git diff --binary --no-ext-diff --no-textconv` の出力bytesと一致必須。差分なしなら空ファイルのSHA-256。
- Git-visibleな全untracked fileの別コピーを要求。元ファイル・hardlink・repo内のコピーは拒否。名前だけでなく内容hashを照合。
- Submodule、untracked symlink、8MiBを超えるuntracked個別ファイル/Git出力、128MiBを超える保全物はv0.1では自動判定せずUNKNOWN。manifestは1MiBまで。
- ignored file・Git LFS実体・reflogだけのcommit・他branchの全成果はこの判定の保証外。別途保全レビューが必要。
- LOCAL_ARTIFACTS_VERIFIEDはローカル照合だけ。bundleの前提commitは現repo内で検証しただけで、復元試験、遠隔保存、再起動・環境破棄耐性を証明しない。

## 閾値と記録

各volumeの既定: 使用率80%以上WARN、95%以上STOP、空き1GiB以下WARN / 256MiB以下STOP、空きinode10,000以下WARN / 1,000以下STOP。いずれか悪い条件を採用。暫定の保守的運用値であり、普遍的な安全容量の実測値ではない。実際の作業の最大増加量に合わせて開始前に設定する。

```json
{"shared_tmp":{"warn_percent":80,"stop_percent":95},"workspace":{"warn_bytes":2147483648,"stop_bytes":536870912}}
```

`--policy /path/policy.json` でその呼出しにだけ適用。未知キー・bool・負値・NaN・逆転閾値は拒否。

runは `events.jsonl` にUTC時刻、volume別disk/inode、mount、保全判定、起動/終了/停止理由をfsyncして記録。argv全体や環境変数全体、ファイル本文、認証情報は記録しない。ローカルpath/HEADは含まれるため公開前に確認する。ログ8MiB到達または書込失敗時も子を停止する。stdout/stderrのfallbackだけが残る場合は永続記録成功とみなさない。

終了コード: 0正常、20容量STOP、21測定UNKNOWN、22保全不足、23設定/記録/起動エラー。runが実行済みならchildのコードを返すため20-23と重なる場合がある。`events.jsonl` のreason/eventで区別する。signal終了は128+signal。

## 試験

```sh
CAPACITY_TEST_ROOT=/workspace/my-job/test-fixtures PYTHONDONTWRITEBYTECODE=1 \
python -m unittest discover -s research/cloud-workspace-capacity/tests -v
```

テストの容量STOPはsynthetic注入であり、実ディスクを埋めない。プロセス停止はテスト自身の子だけで確認。fixtureも自動削除せず保持する。通常runの稼働中チェックは5秒ごと（0.1〜300秒設定可）。間隔内の急激な増加を防ぐquotaではない。
