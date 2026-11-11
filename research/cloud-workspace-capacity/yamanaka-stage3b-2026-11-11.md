# 共有 `/tmp` 容量枯渇の調査記録: 山中城 Stage 3-B

- 記録日: 2026-11-11 JST
- Hachibei-Lab: [Issue #20](https://github.com/tetsujisugimori-coder/Hachibei-Lab/issues/20)
- 観測元: [yamanaka-historical-terrain Issue #41 初回報告](https://github.com/tetsujisugimori-coder/yamanaka-historical-terrain/issues/41#issuecomment-6781514664)、[追補と独立照合](https://github.com/tetsujisugimori-coder/yamanaka-historical-terrain/issues/41#issuecomment-6781554012)
- 判定: **PARTIAL**。容量不足の場所は実測で特定されたが、GitHub提出拒否の原因、成果の環境再起動耐性、Stage 3-B 完成は未証明。
- 本文の証拠区分: 「原報告で実測」「原報告で独立照合」「本研究での提案」を区別する。本リポジトリで元のクラウド環境・ファイル・ログを再測定したわけではない。
- 対象境界: 一般化可能な運用知見のみ。山中城の未提出ソース、Gitオブジェクト、成果物実体、秘密情報は本リポジトリへ移動しない。

## 1. 事象と測定値

山中城 Stage 3-B の作業環境で一時領域枯渇を確認した。原報告によると、OS は Debian GNU/Linux 13、Linux 6.18.57 x86_64 の cloud sandbox。厳密な商用環境名とクォータ内部の由来は UNKNOWN。

| 指標 | `/tmp` (tmpfs) | 作業領域 (overlay) |
| --- | ---: | ---: |
| 総容量 (bytes) | 5,225,709,568 | 67,586,535,424 |
| 使用 (bytes) | 5,225,680,896 | 49,437,401,088 |
| 空き (bytes) | 28,672 | 14,696,386,560 |
| inode 使用率（原報告、概数） | 3% | 14% |

- `/tmp` はほぼ 100% 使用。一方、作業領域には約 13.7 GiB の空きが残っていた。
- inode 枯渇ではない。実際に読取コマンド起動の sandbox 準備段階で `No space left on device (os error 28)` が発生した。
- 容量不足の**場所**は確定したが、複数タスク間の分離境界、商用インフラの割当ポリシー、GitHub拒否の直接原因は確定していない。
- サイズは測定方法によって「割当bytes」「論理bytes」「レイヤー別bytes」が異なる。異なる集計を合算しない。

## 2. `/tmp` 内の容量上位20件（原報告の割当bytes）

| # | 項目 | 割当 bytes |
| ---: | --- | ---: |
| 1 | `castle2d-browsers` | 1,231,667,200 |
| 2 | `stage3a-baseline-I` | 496,304,128 |
| 3 | `stage3a-baseline-I5adb` | 495,095,808 |
| 4 | `stage3a-baseline` | 478,486,528 |
| 5 | `phase7b-ci-review` | 396,144,640 |
| 6 | `stage2d-navigation-full` | 183,099,392 |
| 7 | `stage2d-acceptance` | 172,814,336 |
| 8 | `node-compile-cache` | 157,745,152 |
| 9 | `lc-ci-independent` | 144,076,800 |
| 10 | `stage2d-red-db73547` | 119,300,096 |
| 11 | `hypothesis-red-green-vRKg6H` | 85,680,128 |
| 12 | `playwright-artifacts-eqnnLA` | 82,993,152 |
| 13 | `stage3a-pages-smoke-dist` | 72,949,760 |
| 14 | `stage2d-final-chromium` | 71,540,736 |
| 15 | `stage2d-browser` | 67,969,024 |
| 16 | `playwright-artifacts-xHvXKw` | 56,274,944 |
| 17 | `castle-independent` | 52,678,656 |
| 18 | `stage3b-overview-browser-run3` | 48,103,424 |
| 19 | `castle2d-npm-cache` | 47,452,160 |
| 20 | `castle2d-pw` | 46,514,176 |

過去の Stage 3-A の基準データ3件だけでも約 1.47 GB（10進表記）、共有ブラウザは約 1.23 GB（10進表記）。これは存在・容量の観測であって、古さや名称だけで削除可能とは判定できない。地形・QGISデータが今回の `/tmp` 枯渇の主因だとの証拠はない。

## 3. 成果物と再生成物

原報告にあるリポジトリ内の拡張子別論理bytesには blend 192,290,700、PNG 165,774,614、GLB 141,766,836、JSON 32,477,451、GPKG 21,577,728、gz 4,671,752、TIFF 4,509,923、QGZ 149,199、GeoJSON 114,377 が含まれる。これらは `/tmp` の消費量とは別の集計で、dist等に重複資産がある。

原報告の保全状況:
- ローカル HEAD `d6898549b620cff0610228d646fc73d7acd5f055`、tree `696a96e6d6204b82f8dd33ff845c7ecea357699e`。
- GitHub 側の対象作業branchは `5adb7156acda3968827ff39d5e6f40c4ac837ec5` のまま。最終ローカル HEAD の遠隔取得は `422 No commit found` と報告されている。
- 未提出 commit、bundle、patch、証拠を保全。bundle verify、git fsck、hashを別担当が照合し、missing/corrupt object なし、dangling blob 2件と報告。
- patch SHA-256: `98c310ddccf93c703e43fc0dc4ed77737728935430cbc467b2bdca9ffe8b753f`
- bundle SHA-256: `41d902414a7edccb55ce9be0b509b049d712323c3a2c415dd56f65685a8b30e8`
- 差分bundleはbase `842d5378` が必要。上記の検査は**環境再起動後や環境破棄後にも残る**ことを証明しない。
- 以前の16ブラウザ条件、4故障条件、389単体試験、212原本保全は、今回新規に再実行された試験ではなく**以前の試験報告の確認**。

## 4. 仮説と結論の境界

| 仮説 | 原報告に基づく判定 | 留保 |
| --- | --- | --- |
| H1: 容量不足がGitHub提出拒否の原因 | UNKNOWN | 元の拒否原文未回収 |
| H2: GitHub権限・認証が原因 | UNKNOWN | Issueコメント投稿成功はcreate_tree等の成功を保証しない |
| H3: 通信・実行環境の制限が原因 | UNKNOWN | sandbox準備段階の容量エラーは観測済み |
| H4: Gitオブジェクト破損が原因 | 検査範囲でREJECTED | 全経路の不具合を排除したわけではない |
| H5: 容量枯渇とGitHub審査拒否は別の段階で観測 | SUPPORTED | 完全な因果独立はUNKNOWN |

**容量不足の場所の特定 ≠ GitHub提出拒否の原因確定 ≠ Stage 3-B完成。** 元リポジトリの正式Draft PR、正式CI、11歴史区域の位置根拠は未了。

## 5. 容量回復の区分（今回は削除しない）

| 区分 | 候補 | 実行条件 |
| --- | --- | --- |
| A: 再生成候補 | Node compile cacheとnpm cache、計205,197,312 bytes（約195.7 MiB） | 所有・稼働中利用・再取得可能性を確認してから個別判断 |
| B: 要追加確認 | 共有ブラウザ約1.23 GB、dist等 | 利用者、復元方法、他案件への影響を調べる |
| C: 保全必須 | baseline、原モデル、未提出commit、bundle/patch、PNG/trace/CI/失敗原票 | 無断削除しない |

現時点で**無条件に安全な削除容量は0 bytes、削除実績も0**。作業領域上のdistを削除しても、別マウントである `/tmp` の空きが増えるとは限らず、今回の観測では別領域として扱う。

## 6. Hachibei-Labとしての次の研究課題（提案、未実施）

1. タスク開始時に `df -h`、`df -i`、作業先のファイルシステム種別・マウントを記録。容量とinode、共有 `/tmp` とworkspaceを別々に確認。
2. `TMPDIR`を作業領域側のタスク固有ディレクトリに切り替えられるか、小さな隔離テストで検証。ツールごとの追従、tmpfs前提の処理、cleanup、環境終了時の扱いに注意。
3. キャッシュには生成元・依存版・再取得手段・利用中プロセス・所有者・最終使用を記録。「キャッシュなら削除可」という自動判断はしない。
4. ローカルにしかない成果はGitHubとの一致とは別に保全し、可能な場合は再取得できる別の許可済み保存先へ退避する。SHA-256に加えて復元試験と再起動後の照合を行う。
5. GitHub提出拒否は操作種別・HTTP status・原応答・時刻・commit SHAを残し、正常なIssue投稿と区別する。原因がUNKNOWNなら迂回・強制・反復送信はしない。
6. 実効容量の監視・アラート・保全ポリシーは環境の共有境界を確認してから設計する。自動削除や常時監視の権限は今回付与しない。

## 7. 本PRの受入・レビュー基準

- [ ] 出典と日付、原報告の実測と提案を区別できる
- [ ] `/tmp` と作業領域の数値を混同していない
- [ ] 削除0、無条件安全容量0、再起動耐性UNKNOWNが明記されている
- [ ] GitHub提出拒否の原因UNKNOWN、正式CI未実施、11区域未了が保持されている
- [ ] 未提出成果の実体、秘密、個人情報を本公開リポジトリへ持ち込んでいない
- [ ] 山中城のコードやGit履歴を変更していない
- [ ] 文書だけの限定採用判断とStage 3-B本体の受入を混同していない

このファイルは**外部Issueの観測報告を整理した二次記録**であり、本PRで山中城の実測や容量回復、GitHub障害解消、最終CIを新たに実証したものではない。
