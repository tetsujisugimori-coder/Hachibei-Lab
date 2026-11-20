# クラウド作業領域 容量管理共通仕様 v0.1

## 対象と非対象

事実: PR #21は共有/tmp枯渇の二次記録で、TMPDIR分離や再起動耐性を未検証としていた。本仕様はIssue #20を継続し、小規模計測と明示実行CLIを追加する。

採用: ディスク/inode別測定、タスク別一時領域、Git-visible成果の保全チェック、起動前の拒否、実行中の限定停止・記録。

非対象: 共有/tmp掃除、自動削除、定期常駐、元の山中城ソースやGitオブジェクトの移設、元repo/他案件の設定変更、リソースquota、任意のプロセス隔離、GitHub提出拒否の解消、再起動/環境破棄の耐性証明。自動削除は設定としても有効化できず、常にfalse。将来追加する場合も別の明示承認を要する。

## 識別と観測

1. 呼出しはworkspace、Git root、task ID、run rootを明示。repoとrun-rootは測定workspaceと同じfilesystem deviceを必須とし、別mountへの見落としを防ぐ。commandが任意の他pathへ書き込むことを禁止するsandboxではない。
2. /tmpとworkspaceを別レコードにし、それぞれ総bytes、非特権利用可能bytes、使用率、総inode、利用可能inode、inode使用率、device/mount/type、UTC時刻を記録。
3. 使用率は使用量/(使用量+利用可能量)。予約領域を利用可能量と混同しない。同じdeviceでもレコードは保持し、容量を合算しない。
4. 読取失敗・inodeカウンタ不明はUNKNOWNで起動拒否/停止。mount名取得だけの失敗は容量測定と区別。
5. キャッシュ使用量の観測から削除可否を推定しない。今回のprobeは指定した共有cacheのmetadata fingerprintの前後比較であり、全共有領域の無変更証明ではない。

## 保全分類

| 分類 | 例 | 扱い |
|---|---|---|
| 原本・未提出成果 | local commit、stage/unstaged差分、untracked、bundle/patch | 優先保全。hashとHEAD照合。無断削除しない |
| 証拠 | trace、PNG、失敗原票、CIログ、計測JSON | 元データと生成条件/版/時刻を紐付け、公開時は秘密を除く |
| 再生成候補 | Node/npm cache、browser binary、build output | 候補に過ぎない。所有者・稼働・生成元・版・復旧方法を確認するまで削除しない |
| 未分類・他案件 | 古い名前のdir、共有tmp、所有不明 | 保存。横断削除しない |

Gitチェックの限定性とmanifest形式はREADMEを参照。preservation状態とcapacity状態は別欄とし、一方のPASSを他方へ流用しない。

## 状態遷移と副作用

- CHECK: read-only測定/保全検査。外部通信なし、既存git indexを更新しない。
- PREFLIGHT: 新規専用run dirへ小さい記録を試みる。容量STOP/UNKNOWNまたは保全不足なら子を開始しない。記録領域まで満杯ならstderrへ失敗を出し、成功としない。
- RUNNING: 自分で開始したforeground commandにだけ環境変数を渡す。別session/process groupを作る。shell=Trueは使わない。
- STOPPED: 容量STOP/UNKNOWN、SIGINT/SIGTERM、記録失敗で自分のgroupへSIGTERM。3秒猶予後SIGKILL。直接childの通常終了時にも同groupの残存background childを終了させる。プロセス名検索や他案件のkillはしない。
- RETAINED: 成功/失敗/中断いずれもファイルを保持。終了hookや一括cleanupはない。

**境界:** Linux process groupはsecurity sandboxではない。子がsetsid等でgroupを脱出した場合は停止保証がない。daemon化するcommand、trustedでないcommand、別グループへ委譲するjobに使わない。SIGKILL/実行基盤消失時はfinal eventが欠落し得る。同一UIDの敵対的なsymlink差替えやGit内容の並行変更に対する原子的snapshotも保証しない。開始直前にworkspaceと保全物への他のwriterを止める。

ログは8MiBで上限、Git readは15秒/8MiBで上限。保全対象が上限を超える案件はUNKNOWNとして個別手順へ戻す。

## 戻し方・環境終了時

設定は子プロセス内だけで、親shell/global config変更がないため設定rollbackは不要。既存PLAYWRIGHT_BROWSERS_PATHとXDG_CACHE_HOMEは維持。新規run dirだけが残る。元の実行コマンドを通常の環境で呼ぶことでguard未使用へ戻るが、容量STOPの原因が解決したことを意味しない。

環境終了前に未提出成果と証拠を選別し、承認済み保存先でhash/復元確認を行う。自動uploadはない。終了後のworkspace/tmp保持はプラットフォーム保証を未確認でUNKNOWN。手動削除は今回の範囲外、所有と使用状況を確認して別承認を得る。cacheであっても削除0を維持。

## 受入境界

新規unitテスト、今回の隔離probe、GitHub CI、独立レビューを別々に記録する。以前の16ブラウザ条件、4故障条件、389unit、212原本保全を今回の新規PASSに数えない。ブラウザ起動失敗はそのままFAIL/未検証とし、Nodeやbuild成功で代替しない。マージ/Draft解除は本作業の対象外。
