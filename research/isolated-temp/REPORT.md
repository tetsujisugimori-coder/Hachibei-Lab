# Issue #27 専用Temp・Playwright限定検証

## A 総合
PARTIAL / マージ推奨NO（実ブラウザ・永続保全未完）。2026-11-13 JST。
main基準88432afc37274e6bb41f9d3e3a577d739ab06814、tree ef77696c0e210d2c32a1b840d968c3ff45468dde。
PR #28はmerged、Issue #27はOPEN。既存原記録・規約の公開境界を引継ぎ、既存Issueを再利用。
AGENTS.md/CONTRIBUTING.md/.agentsはcheckoutに無し。READMEとStage1の制約を確認。

## B 既存証拠
原pilot result.json 5543B SHA256 faebc916fe923a111b6d33e1bd463f64e6212db9fdbf14060778d672b5088749 完全一致。
8ファイル9364Bを別の案件専用私有領域へ非破壊コピーし、別Pythonプロセスで8/8 hash一致。
原記録の試行日時2026-11-12 18:45:14–15 UTC、Node24.22.1/Python3.12.14。
Node/Python作成・読戻し、Node compile cache3files、親env不変は原記録で確認。
pilotはrepo外の合成試験。**当時の対象HEAD/treeは未収録UNKNOWN**。今回mainを遡及付与しない。
Windowsの既存archive親は読取可能、容量約437GB。実効read-onlyで新規保存認可未成立。
**原証拠のWindows永続保管PENDING**。cloud内コピー/公開Git記録を永久保管と扱わない。

## C 新規限定試行
2026-11-12 19:02:44.318817–19:02:45.154806 UTC（11月13日04:02 JST）。
Playwright1.62.1既存、管理browser pathのbinaryは無し。既存 /usr/bin/chromium を明示。
単独試行1回、runner/Node exit2。Chromium exitCode=null / signal SIGABRT。
原エラー主要部：`socket() failed: Operation not permitted (1)`。
crashpad `--database is required` も記録。根本原因の確定はUNKNOWN。
sandbox無効化や権限緩和、再試行、downloadなし。DOM試験NOT_TESTED。
専用領域のprobe17B読戻しとNode cache6filesを観測、browser profileは空。
実際のbrowser内部Temp/DOM完遂はBLOCKED、全未追跡ファイルUNKNOWN。
終了後、別shellの見えるPID namespaceにChromiumなし。global残存なしとは言わない。

## D 容量と影響
/tmp device39、workspace device27。別filesystem、quota独立UNKNOWN。
/tmp available 5237850112B→同値、free inode1278751→同値。
workspace available61986422784→61985226752B（1196032B減）。同時他作業もあり独占寄与と断定しない。
親5環境変数不変。全システム環境変更なし。既存trackedファイル変更0。
共有/tmpの既存データは移動/削除せず、他案件のfile/processも操作していない。
総量差0は瞬間的内部使用0の証明ではない。Playwright自身の終了cleanupは原ログに記録。
既存案件全域hash比較は未実施。新規専用root外への全システムwrite監査も未実施。
専用folderも同じoverlay poolを消費するため他案件圧迫の可能性は残る。
現在と旧枯渇環境の同一性・回復経緯UNKNOWN。

## E 検証とレビュー
13 synthetic unit tests、既存Stage1の29mock regression PASS。実browser成功とは別。
独立レビューのmissing evidence/wrong values false PASSを再現（RED）。
期待readback/DOM/path/実probe hash、親env不一致、timeout stderr保持、bounded manifestへ修正。
修正版の負対照はBLOCKED（GREEN）。実Chromiumは再試行していない。
正式CI・最終HEAD独立レビューはGitHub提出後に別記録。ここで先取りPASSしない。

## F 次工程
1. 承認された非公開Windows保管と別process hash読戻し。
2. 正規にブラウザ起動可能な環境で別承認の限定試験。保護解除で迂回しない。
3. quota/provider・全内部Temp・性能は別検証。CAD/実案件build/他browserはNOT_TESTED。
今回は構造的分離の限定研究であり、全案件安全性・恒久解決・製品受入ではない。

## G 既存Draftとの関係
[PR #22](https://github.com/tetsujisugimori-coder/Hachibei-Lab/pull/22) は未マージDraft、HEAD f3165388ac29793455b9615f9b447f414825fae6。
既に汎用capacity guard、Node/npm/offline build、Chromium/WebKitのprobeと異常process-group対策を持つ。
今回そのguard/機能を再実装・置換・展開せず、最新main上の独立証拠保全と**Chromiumだけの1回測定**を小さな専用fixtureとして提出する。
既存PR22の試験を今回の実行と数えない。今回fixtureを汎用runnerへ昇格させない。
将来共通化はPR22の境界/timeout/group制御を再利用する別判断とし、並行した新しいcapacity guardは作らない。
