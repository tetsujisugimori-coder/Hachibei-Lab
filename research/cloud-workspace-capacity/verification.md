# 検証記録（2026-11-11 UTC）

## 今回の新規検証

- Guard synthetic unit: **37 tests PASS**。閾値境界、設定拒否、disk/inode分離、保全manifest、見落とし修正、child/孫process停止、無関係process生存、signal、log failure、別device拒否など。
- Probe hardening synthetic: **3 tests PASS**。symlink/`..`による/tmp進入拒否、timeout/通常終了の所有group停止、別sessionのsentinel生存。
- 実測read-only check: `/tmp` disk STOP（空き0 bytes）、inode OK。workspace disk WARN（82.0575%、空き11,507,179,520 bytes）、inode OK。2026-11-11T00:47:21 UTC、exit20。容量を実際に埋める故障試験は行っていない。
- 実Node/npm/小型build: PASS。実Chromium/WebKit: FAILED。詳細は別レポートと原票JSON。probe測定後のhardening版ではブラウザ再実行NOT_RUN。
- Python構文検査、差分空白検査を実施。GitHub CIと最終HEADへの独立レビューはPR上の記録を正とする。

37/3はunittestのmethod数。subTest条件数を加算しない。実測probeの6コマンドや以前の16ブラウザ条件とは別集計。

## 既存コード回帰

実行したもの: Stage1 **27 PASS**、Stage2 **58 PASS**、Stage3 **52 PASS**、generic-kinematics **20 PASS**。既存コード・既存workflowの変更はない。

Stage1は最初、checkoutに固定参照commit `48f5fe96aa6df48de64272f2eabd0bad66d92a5a` がないため1 ERROR（26 PASS）だった。通常履歴取得だけでは含まれず、その既知commitを取得して再実行し27 PASS。テストを書換えて回避していない。FreeCAD/他project browser等の全リポジトリaggregateは今回未実行。

## 保全と結論

ローカル実行原票はこの専用run領域に保持。公開証拠には限定的な測定値、syntheticログ、サニタイズ済みbrowserログのみを含め、山中城等の未提出source/Git objectは含めない。

作業中にexec-server disconnect/復旧timeoutも観測した。環境再接続後に作業ファイルの存在を確認したが、任意の再起動や環境破棄後の耐性証明には拡張しない。

**総合PARTIAL**: opt-in guardの限定的な機能検証とNode/buildのTMPDIR実測まで。ブラウザ成功、GitHub拒否原因、全cache完全隔離、保存物の別環境復元・耐久性は未証明。自動削除/共有/tmp削除0、他案件変更0、Draft解除/mergeなし。
