# 共有一時領域の緊急診断 Stage 1

2026-11-11。[Issue #27](https://github.com/tetsujisugimori-coder/Hachibei-Lab/issues/27)、関連[Issue #20](https://github.com/tetsujisugimori-coder/Hachibei-Lab/issues/20)。
基準main: 55479ddee78f6ede43cbe550d8703ac1a8a66591。
公開用に編集した集計と匿名化エラーのみ。原証拠本文、絶対workspaceパス、Space識別子、環境ID、mount upperdir、process引数/環境、資格情報は公開しない。

## A. 総合判定

**PARTIAL。復旧・製品受入・マージの許可ではない。**

容量枯渇、現在読める複数案件の作業コピーのfilesystem共有、保全7点のhash一致を確認。provider quota、globalな使用中process、全過去実行の環境同一性、GitHub旧拒否原因、未承認の原証拠保管、環境破棄耐性はUNKNOWN/BLOCKED。

後半に本調査もsandbox準備ENOSPCで新規shellが起動不能になった。反復せずshell調査を終了した。既に得た公開用情報と、既知SHAに一致するcode/testのみをGitHub connector経由で提出する。実環境回復を意味しない。

## B. 容量不足の場所と実測値

2026-11-11 08:02:58 UTC / 17:02:58 JST。df -B1 -P、df -Pi、終了0。

| 領域 | total B | used B | available B | used / total inode | df使用率 |
|---|---:|---:|---:|---:|---:|
| /tmp tmpfs | 5,225,709,568 | 5,225,664,512 | **45,056** | 29,128 / 1,275,808 | 100%、inode3% |
| workspace overlay | 67,586,535,424 | 62,057,799,680 | **2,075,987,968** | 674,303 / 4,194,304 | 97%、inode17% |
| shared候補領域 | workspaceと同じ | 同じ | 同じ | 同じ | 同じ |

workspaceのstatvfs freeは約5.53GB、非特権availableは約2.08GB。df率はusedとavailableに基づく丸めで、used/totalとは異なる。差約3.45GBのprovider内部予約/quota設定の意味はUNKNOWN。

08:05:27 UTCは/tmp同値、workspace used62,057,865,216B、available2,075,922,432B、inode674,308。
08:08:02 UTCのtool担当smoke報告も/tmp45,056B、workspace available2,072,154,112B。最後の値は担当の原応答確認報告であり、後半の最終絶対値の再検証ではない。

/tmpとworkspaceは別filesystem。sharedという名前の領域はworkspaceと同じoverlayで、独立した容量や永続性を持つ証明ではない。承認済みremote保全先の内部容量/quotaは未取得。

### 時間差観測と増加速度

| 観測 | /tmp | workspace | 解釈 |
|---|---|---|---|
| 08:02:58→08:05:27 UTC、149秒 | used差0、inode差0 | used+65,536B、約439.8B/s、inode+5 | 別呼出しの観測差。厳密namespace継続は未確認。自身の記録も含む |
| 08:14:37.131241→08:15:07.138221 UTC、30.00698秒 | **used+45,056B、1,501.5173B/s** | used差0 | 同一process内の2snapshot、environment/mount/path/device/total一致、compare PASS |

後者はstart/endの絶対availableをstdoutへ出していない。完全JSONはローカルに保存済みだが、起動失敗により再読取り未実施。以前の空き45,056Bと同量増加したが、**最終available=0Bを独立に検証済みとはしない**。現在の絶対空きはUNKNOWN。増加主体・粗生成量・削除/生成の相殺・sandbox準備自体の影響はUNKNOWN。

満杯付近の0B/sは安全化ではない。書込みが失敗していれば増加しない。旧山中城記録のworkspace空き約14.7GBとの差から、identity不足のまま厳密な長期増加率は計算しない。

## C. 確認された原因とUNKNOWN

| 項目 | 結果 |
|---|---|
| /tmpのblock不足 | CONFIRMED。空き44KiB相当、100% |
| inode不足 | 今回観測ではREJECTED。tmpは約124万free |
| workspace圧迫 | CONFIRMED。非特権available約2GB |
| sandbox起動時ENOSPC | CONFIRMED。コマンド本体より前に失敗 |
| ENOSPC内部allocationのfilesystem | UNKNOWN。表示targetはsynthetic mountで、/tmpの直接書込失敗とは断定不可 |
| memory/pid/fd limit原因 | UNKNOWN。OOM/EAGAIN/EMFILE原票なし |
| GitHub旧提出拒否原因 | UNKNOWN。原拒否文/要求終端不足 |
| 案件別生成者・増加責任 | UNKNOWN。mtime/uidのみでは認定しない |

08:03頃のread-only resource観測はMemAvailable1,949,925,376B、swap0、open-files soft16384、process soft39792。全host・失敗時の状況ではない。quota command未導入、checked cgroup v2 pathsはENOENT。追加インストールや設定・権限変更なし。

## D. 環境・filesystem比較表と他案件影響

2026-11-11 08:05:27 UTC / 17:05:27 JSTの同一観測でstat/statvfs/mountinfoを照合。

| 対象 | 同じ実行環境か | filesystem | 同じ容量制限か | 根拠と限界 |
|---|---|---|---|---|
| 山中城Stage3Bの現存copy | E1から読取可能 | overlay device0:27 | 共通statvfs pool確認 | 過去実行主体の同一性はUNKNOWN |
| Loading7Dの現存copy | 同上 | overlay device0:27 | 同上 | 全過去試行/CIを含めない |
| Hachibei PR26の現存copy | 同上 | overlay device0:27 | 同上 | 原承認証拠の保存権限とは別 |
| 城郭Stage3Cの現存copy | 同上 | overlay device0:27 | 同上 | 他repo変更なし |
| shared保存候補 | 同上 | overlay device0:27 | 同上 | 別名でも永続/容量隔離ではない |
| 現在の/tmp資産 | E1の観測 | tmpfs device0:39 | 同device資産は共通5,225,709,568B pool | 他namespace/provider内部quotaはUNKNOWN |
| GitHub Actions | remote run | 未測定 | UNKNOWN | local filesystemとの同一性を認定しない |
| Space既存copy | 過去再取得receiptあり | remote内部未取得 | UNKNOWN | 今回remote読戻し/破棄試験なし |
| 別接続computer | available一覧のみ | NOT_MEASURED | UNKNOWN | 関連作業の実行を確認できずattachしない |

現在の共存・共通pool消費は確認した。山中城・Loadingに対応する資産が/tmpに併存することも実測。特定の案件が他案件の個別障害を引き起こした因果はUNKNOWN。

mountinfoはsandboxのread-only親とwrite可能子の重なりを含む。ro/rwの併記をwrite probe成功と誤認しない。namespace fingerprintはprivate側に保持。パス名・容量数の一致だけで全環境を同一視しない。

### 容量消費元の分類台帳

08:04:55 UTC / 17:04:55 JST。匿名ID。allocatedはst_blocks×512、logicalはst_size（directory metadata含む）。最新mtimeは走査で見た最も新しい子項目であり最終使用/生成主体の証拠ではない。

| ID / 分類 | allocated B | logical B | 最新mtime UTC | 所有 / 使用中 |
|---|---:|---:|---|---|
| T01 browser runtime | 1,231,667,200 | 1,230,616,031 | Nov09 09:50:48 | 同local uid / UNKNOWN |
| T02 baseline A | 496,304,128 | 492,321,321 | Nov09 19:32:25 | 同上 |
| T03 baseline B | 495,095,808 | 492,321,443 | Nov09 19:33:01 | 同上 |
| T04 baseline C | 478,486,528 | 474,620,195 | Nov09 19:12:31 | 同上 |
| T05 CI review原証拠 | 396,144,640 | 395,864,745 | Nov10 05:42:18 | 同上 |
| T06 navigation原票 | 183,099,392 | 183,015,757 | Nov09 10:35:51 | 同上 |
| T07 acceptance原票 | 172,814,336 | 172,457,693 | Nov09 11:18:15 | 同上 |
| T08 independent CI原票 | 144,076,800 | 143,937,197 | Nov09 19:12:10 | 同上 |
| T09 failure原票 | 119,300,096 | 119,236,601 | Nov09 10:09:46 | 同上 |
| T10 failure ZIP | 118,046,720 | 118,042,889 | Nov09 10:09:45 | 同上 |
| Node compile cache再出現 | 30,535,680 | 21,112,868 | 記録あり | 同上 |
| npm cache候補 | 47,452,160 | 47,405,665 | 記録あり | 同上 |

大きい個別file: browser executable463,228,928/305,770,496 allocated B、browser library125,206,528/97,128,448 B、原ZIP191,229,952/118,046,720 B。内容は未読。親directory集計との二重合算禁止。

/tmp走査は29,127entry、0.46秒で同device範囲完了、別mount6件除外。symlink先を追わず、同inode重複は一度だけ。workspaceは120,000entryで4.27秒停止、PARTIAL。訪問範囲の候補: 山中城保全/復元群3,109,478,400B、Loading旧copy1,466,900,480B、UI旧copy1,303,187,456B、山中城別copy723,046,400B、UI第14回665,075,712B。全域順位ではない。sharedは19,121entry、0.28秒。scanは非原子的。

browser/cacheは再取得候補だがversion/再取得経路/利用者未確認。baselineは依存・成果・原証拠が混在し得る。CI/失敗原票/trace/PNGは同一原本を再生成できないため保全優先。**安全に削除可能と確定した容量は0B**。

08:05:27 UTCの/proc sampleは見える3process/10fdsだけ。tmp fd0でもglobal未使用の証明ではない。deleted-open fileのglobal量もUNKNOWN。

### 約151MiB退避cacheの現在

既存退避先はworkspaceと同じoverlayに存在。18,978files、114,141,832 logical B、157,745,152 allocated file B（150.44MiB）。親directory含む集計は158,236,672Bで区別する。旧台帳の件数・logical量と一致。

旧記録: pre_move_manifest: NOT_CAPTURED; pre/post hash comparison unavailable。全18,978hash再計算は軽量制約で未実施、内容完全一致とは言わない。/tmp側cacheは再出現し30,535,680 allocated B。恒久分離、生成主体、再増加の因果はUNKNOWN。今回は移動/削除/圧縮/再設定なし。

## E. 未提出成果物の保全状況

今回SHA-256再計算は08:04:44 UTC、7点すべて既存台帳一致。hash一致は真正性・完全履歴・永続性とは別。

| 作業 | code / 未提出状況 | bundle・patch・診断・ログ | 永続先 / 復元可能性 | 判定 |
|---|---|---|---|---|
| 山中城3B | local d6898549b620cff0610228d646fc73d7acd5f055、cached main+4、tracked dirtyなし | patch822,424B、差分bundle123,470B、完全archive421,558,111B再hash | 既存Space再取得receipt、1,912tracked復元/fsck成功の過去記録。今回remote読戻し/restart/destroyなし | LOCAL_HASH_PASS、DURABILITY_PARTIAL |
| 城郭3C | local445f37182f07dae98441bc2a57f103e140c628a9、cached main+2、tracked dirtyなし。今回remote9ed57db22c386ec67a2afabf40b7412fcf957a55 | 完全archive132,281,758B、旧shallow bundle13,379,570B再hash | 既存Space再取得、78files照合、完全history bundle無通信復元記録。旧shallow単独完全復元は不可扱い | LOCAL_HASH_PASS、DURABILITY_PARTIAL |
| Loading7D | local/remote PR88の1c528a2131a0de706d51db56d03aa3c2066da78c一致、Draft | local旧台帳18ZIP428,220,510Bから2ZIP再hash。最新公開報告は旧18+新14=32ZIP約1.54GB | 非公開永続先/承認/容量/保持条件未確定。全32を今回再hashした主張なし | ARCHIVE_BLOCKED |
| Hachibei PR26 | local/remote2df3be413f2b8d060ff8ade731a2830f4ac8074b一致、Draft | 診断code提出済み。本人明示承認原本は未取得、原本SHA未照合 | 承認済み非公開保管先未確認、原証拠HOLD | ORIGINAL_NOT_OBTAINED / BLOCKED |
| 関連UI14・Calculator3B10 | 既存公開報告ではDraft提出済み | 原artifactは既存正式CI保管 | 今回全artifact/期限監査なし | NOT_AUDITED_IN_FULL |

mainよりaheadは未pushの証明ではない。status -unoはtrackedだけでuntracked/ignored全体が空とは言わない。旧差分bundleには前提commitが必要。山中城local branch名のGitHub読取は422だが、他refにcommitが絶対存在しない証明ではない。原本の新規コピー/外部転送なし。

| ID | SHA-256 | bytes |
|---|---|---:|
| 山中城patch | 98c310ddccf93c703e43fc0dc4ed77737728935430cbc467b2bdca9ffe8b753f | 822424 |
| 山中城差分bundle | 41d902414a7edccb55ce9be0b509b049d712323c3a2c415dd56f65685a8b30e8 | 123470 |
| 山中城完全archive | c87e69ad6aaada41bec29313bdfc8f275ad24620f6eed8a3be73106e36e0bde0 | 421558111 |
| 城郭完全archive | b22ee94b345478645dc54300a47c28f327ef5d9c93df8ec3a0234f0bdd09bfa9 | 132281758 |
| 城郭旧bundle | b357252dbf783c2dc7e25b9eb1a53d70def2457af2735b4911b3592ed0e32839 | 13379570 |
| Loading旧CI ZIP1 | 08c7be38eafe7178e3228248fd4f788c7e30ddc4c1d11e2c7346f82242404461 | 2829831 |
| Loading旧CI ZIP2 | dae0a67e61f216dcfd3cfba563676a0cba0d7f6508530cafce4e12b098f5add0 | 4003788 |

## F. 障害別原因分析とGitHubの関係

| 障害 | 時刻 / 原エラー / exit | 分類と限界 |
|---|---|---|
| block不足 | 08:02:58,08:05:27 UTC、df0 | /tmp枯渇CONFIRMED、個別失敗の因果は別 |
| inode不足 | 同時刻、df0 | 今回はREJECTED、全過去時点は未証明 |
| 新規sandbox起動失敗 | 08:05–08:06 UTC監査、さらに08:14–08:16 UTC親/review要求。exit101、command未実行 | failed to register synthetic bubblewrap mount target <workspace>/.aws: No space left on device (os error 28)。linux-sandbox/src/linux_run_main.rs:761:25。ENOSPC CONFIRMED、内部FS/allocator UNKNOWN |
| 過去山中城起動失敗 | 2026-11-10 22:49 UTC以降の既存記録、exit101、同種error | 旧/tmp28,672B、inode3%。同一namespace/完全因果UNKNOWN |
| Loading断続起動失敗 | ユーザー/既存報告あり。個別原時刻/exit未回収 | 今回別監査ENOSPCをLoadingの原エラーへ代用しない。UNKNOWN |
| process/memory | 08:03頃resource読取。cgroup ENOENTで合成shell exit1 | OOM/EAGAIN/EMFILE原票なし、global利用率UNKNOWN |
| GitHub旧create_tree拒否 | 山中城Issue41、原拒否文/HTTP/exit未回収 | auth/permission/reviewer/network/capacityすべてUNKNOWN。拒否迂回なし |
| 城郭先行create_tree要求 | 旧報告は応答待ち中断/結果不確定 | remote/local head差だけで終結を断定しない。再送なし |
| GitHub ref read | 今回山中城local branch名、HTTP422: No commit found for SHA: feat/stage3b-castle-overview-main38 | 対象ref未解決。認証/破損/容量原因へ読み替えない |
| 今回Hachibei branch作成 | connector正常応答 | 当該操作成功。別repo/旧拒否/全write権限の証明でない |
| network/通信 | 今回read/branch正常、独立timeout/DNS/TLS原票なし | 対象通信成立。過去原因UNKNOWN |
| 初期探索pipe | find ... pipe headでBroken pipe、合成shell0 | head先行終了による切詰め、副作用。disk/GitHub障害と別 |

正確なfailure wall-clockがtool応答にない場合はwindowで記す。launcher101と実command exitを分ける。GitHub read/comment/branch/tree/pushは別操作。容量不足がGitHub提出拒否の原因という証拠はない。新規shell失敗後は再試行せず、別の許可済みconnectorで公開内容の提出だけ継続。

## G. 安全上の問題と残るリスク

- 既知/tmp空き44KiB、workspace約1.93GiB。追加増加と起動失敗があり、証拠消失・新規起動不能リスクが残る。
- 原票はlocal保持。remote保全承認のない証拠はBLOCKED。保管先の安全性/ACL/保持期限/容量/読戻し条件を先に確認。
- Loadingの最も早い既存原CI証拠は2026-12-10 22時UTC頃 / 12月11日7時JST頃失効予定という既存報告。今回全32期限を再照合していない。
- scan非原子性、workspace打切り、別mount除外、namespaceの狭いprocess視野を維持。完全な使用中判定なし。
- 公開物は手動編集。private rawは転送せず、コードと合成試験だけ遠隔CIで扱う。

## H. Stage 2–4改善設計（未実施・別途承認）

### Stage 2: 所有/生成/保全優先
元runのnonsecret environment/mount/timeを揃え、同contextで少数の時間差観測。起動不安定なら反復しない。browser/cacheのversion、再生成経路、利用者を確定。baselineを名前だけでcache扱いしない。
保存先、対象データ、アクセス者、保持条件を本人承認後に非破壊コピー・remote readback hash・孤立復元を検証する。原本は残す。その後に限定対象/回復量/利用中確認/rollbackを示して修復承認を求める。

### Stage 3: 案件別TMPDIRと実容量分離
workspace配下TMPDIRはpath分離だけで同overlay quotaを共有する。別mount/quotaを比較。TMPDIRを無視するcompile cache/browser/sandbox準備も対象化。親global設定は変えず、専用jobの設定案として小規模試験を別途承認する。今回build/browser試験追加なし。

### Stage 4: 共通事前確認/安全停止/証拠管理
block available、inode、最大予測一時使用量、原証拠保全を独立check。static thresholdだけで安全保証しない。UTC/identity/exit/欠測/打切りを機械記録、PRIVATEを既定とする。
read-only monitorとjob guardを分離。新規job抑止/自分のjob停止/他案件に触れない境界を明示し、append-only原票/hash/期限/承認済みreadback/環境破棄復元を設計する。今回は監視登録・guard導入・設定変更なし。synthetic ENOSPC等で検証し実FSを埋めない。

優先: 非公開保全先の確認 → 元提出拒否/不確定要求の正規確認 → 限定回復の承認 → 分離/guardの別Stage。

## I. GitHub・CI・独立レビュー

専用branch diagnose/issue27-shared-temp-stage1。新規研究フォルダと専用path-filtered CIのみ。29mock testsを実装者・親・独立担当が成功。初期P2 3件（I/O例外、naive時刻、mount ID順）を修正し同反例で再検証。

独立担当は公開集計とprivate監査記録を照合し、Stage1 code/report限定PASS、P1/P2残件0。7大容量hashを独立に再計算した主張ではない。最終報告ファイル化はsandbox ENOSPCで未実行となり、レビュー本文は会話で受領。

code SHA58e868f5bed3a8c42756a12b01a4f9a7d1c1ad0ad124133303298e5abe90afe1、test SHAbaa61e6d7874578ff0ca1130122e63a6e4b5298279cbc31e866a3b5a1a0dec48。起動障害後に既存authoring textから回収し、独立記録と完全一致を検証。既存local原本は変更しない。公開reportは本ファイルへ整理統合し、新しい時間差測定を追記。最終commitのhosted CIと正式COMMENT reviewはPR/Issueで別報告する。

## J. 無変更確認

共有/tmpの削除・移動・圧縮・初期化、他案件file/process変更、環境変数/system設定変更、原本上書き、CI停止、大量試験、修復、他repo書込みなし。
作成したのは専用code/report、診断用小記録、独立した新作業copy。診断toolはread-onlyだが、プラットフォームのcommand起動自体が内部一時容量を使う可能性までは排除していない。
Hachibei専用branch→Draft PR→Issue報告だけ。Draft解除・mergeなし。

## 公開出典

- [山中城初回観測](https://github.com/tetsujisugimori-coder/yamanaka-historical-terrain/issues/41#issuecomment-6781514664)
- [山中城容量/保全追補](https://github.com/tetsujisugimori-coder/yamanaka-historical-terrain/issues/41#issuecomment-6781554012)
- [Loading最新報告](https://github.com/tetsujisugimori-coder/Loading-museum/pull/88#issuecomment-6789691253)
- [Hachibei原証拠検証](https://github.com/tetsujisugimori-coder/Hachibei-Lab/issues/25#issuecomment-6789177288)

既存private原票/復元receiptは公開しない。新規調査できなかった点はUNKNOWN/BLOCKEDのまま引き渡す。
