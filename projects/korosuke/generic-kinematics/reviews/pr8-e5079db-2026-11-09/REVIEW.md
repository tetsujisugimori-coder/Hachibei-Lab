# PR #8 Stage 3A 独立レビュー

- 確認日: 2026-11-09 JST
- 総合判定: **FAIL（現在の入力契約に対する PROJECTED_CLEAR の保証）**
- 限定マージ推奨: **NO**
- レビュー作業: 完了。通常域・公開安全性の確認結果と、誤った CLEAR を返す反例を分離して記録する。
- 評価対象: `e5079db255403134d1864fc8b4ed8b3e8418350d`
- tree: `8e6e7719ed6ddf69607346bfd10c526eb091e30c`
- base/main: `03a05c06243def8aed338b1568ece66897148300`
- 対象: [PR #8](https://github.com/tetsujisugimori-coder/Hachibei-Lab/pull/8)、[Issue #7](https://github.com/tetsujisugimori-coder/Hachibei-Lab/issues/7)
- 実装・既存テスト・PR の提出ブランチは変更していない。証拠のみ別のレビュー用ブランチへ保存する。Draft は維持し、マージしない。

## 1. 固定した変更範囲

開始時の PR は open / draft / unmerged。変更は次の6ファイル、422行追加・削除なし。

1. `.github/workflows/korosuke-generic-clearance.yml`
2. `projects/korosuke/generic-kinematics/README.md`
3. `projects/korosuke/generic-kinematics/example-neutral.json`
4. `projects/korosuke/generic-kinematics/sweep.py`
5. `projects/korosuke/generic-kinematics/test_dense_sampling.py`
6. `projects/korosuke/generic-kinematics/test_sweep.py`

各ファイルの SHA-256 は `public-safety.json`。評価対象の `AGENTS.md` は存在しなかった。`sweep.py` の SHA-256 は `8f61135bb7feef58519c70e459a260ea9db51865b9245eedf73e5f991ab42833`。

## 2. 数学上の設計と実装上の区別

厳密な実数演算では、関節ローカル矩形の最大半径 r と、中点からの最大角差 α について、任意点の移動距離は rα 以下になる。軸平行外接矩形間の距離は矩形本体間の距離以下なので、この下限が移動上限と余裕の和を超えれば区間全体を安全側に認定できる。SAT の接触を含む比較、深度・角幅上限で UNRESOLVED にする設計も、この前提では妥当。

しかし、現在の実装は実数の上下限を binary64 の丸め済み計算値として扱う。中点の表現誤差、角度変換、回転座標、外接矩形・距離の丸め誤差を安全側に包む処理がない。以下の入力はバリデータに受理され、誤った PROJECTED_CLEAR が返る。**「理論式が保守的」と「浮動小数点実装も保守的」は同義でない。**

## 3. 阻害指摘

### P2-01: 大きな絶対角度で真の中点と実際の評価点がずれ、区間を誤認定

- 箇所: `sweep.py:45-48,81-84,127-134`
- 反例: `huge-angle-52.json`
- 入力角度: 4503599627370496° → 4503599627370497°。どちらも有限で、範囲幅は1°なので現行の入力契約を満たす。
- 実測: 1標本、1認定区間、`PROJECTED_CLEAR`。
- 計算上の中点は始点へ丸められ、実際には終点まで1°離れるのに半角0.5°の移動上限を使用する。巨大角をそのまま radians 変換する誤差も加わる。
- 独立証拠: 終点は360°を法として17°。高精度計算では移動矩形の中心が固定矩形の内部にあり、両軸の内側余裕は約 5×10^-7 mm。対象の SAT・corner 計算は証明に再利用していない。
- 分離対照: `huge-angle-trig-only.json` は幅2°で表現可能な内部中点を持つが、終点18°の重なりを同様にCLEARとする。中点の丸めだけを直しても巨大角の三角関数評価の問題は残る。
- 期待: OVERLAP の検出、または表現精度のため UNRESOLVED / 明示的入力拒否。CLEAR は不可。
- 修正案: 許容する角度領域を明示し、周期正規化前後の区間幅・端点を保つ。真の中点を仮定せず、実際に評価した角度から両端までの最大距離を安全側に使用する。細分不能・丸め限界は未解決へ倒す。単に `lo+(hi-lo)/2` へ変更するだけでは表現できない中点の問題は解消しない。

### P2-02: 座標・距離の丸め誤差を含まない「距離下限」により、実際の重なりを CLEAR とする

- 箇所: `sweep.py:81-84,99-108,132-134`
- 反例1: `huge-pivot.json`
- pivot=[10^16,0] mm、角度45〜45.1°、moving中心=[1.2,-1.2] mm、size=[0.01,0.01] mm、fixed中心=[10^16+2,0] mm、size=[1,1] mm。
- 実測: `PROJECTED_CLEAR`。計算した bbox gap は2 mm、移動上限は約0.001487 mm。
- 独立証拠: 実際に評価した45.05°の移動矩形中心は固定矩形内にあり、x方向の内側余裕は約0.197056 mm、y方向は約0.498519 mm。世界座標への加算・減算で小寸法が失われ、誤った距離を認定する。
- 反例2: `moderate-tiny-boundary.json`。pivot=0、中心座標約1.5 mm、角度約0.3°で発生する。角度幅は約5×10^-15°、toleranceは既定値0。
- 実測: bbox gap 2.220446049250313×10^-16 mm が、移動上限約6.893505×10^-17 mmを超えるとして CLEAR。
- 独立証拠: 実際の標本角で、移動矩形の隅が固定矩形の内部へ約5.081×10^-17 mm入る。接触も重なり扱いの契約なので CLEAR は誤り。
- 期待: 数値誤差以内では CLEAR にせず、OVERLAP / UNRESOLVED / 明示的入力拒否。
- 修正案: 共通ローカル原点で計算し、下限を下側・上限を上側へ丸める保証または計算全体の誤差包絡を導入する。許容する座標・寸法・角幅・最小余裕の領域も明文化する。巨大座標だけを禁止しても通常座標の極小境界反例は残る。経験的な固定 epsilon の追加だけを一般保証として扱わない。

両指摘は公開用の合成治具で再現した P2 の数値契約違反であり、現物ロボットが危険であると断定するものではない。ただし、この検査器の主目的である安全側の CLEAR を破るため、限定採用にも阻害となる。P0/P1 は確認していない。

## 4. 独立実行の結果

### 既存検証

- ローカル Python 3.12.14: 既存9試験成功、exit 0。原ログ: `existing-tests.log`。
- neutral例: 4ペア CLEAR、exit 0。`neutral-result.json`。
- [GitHub Actions run 42535095790](https://github.com/tetsujisugimori-coder/Hachibei-Lab/actions/runs/42535095790)、job 128897528936: completed / success。Python 3.11.18、Ubuntu 26.04.1。9試験とneutral例をjobログで確認した。
- ActionsがcheckoutしたのはPR合成merge commit `15d54668787aa0360b13ec9ce0b1a9d152d00c3a`。提出HEADと混同しない。ローカル独立検査は提出HEADそのものを取得して実施。
- workflowにartifact保存手順はない。CIの原ZIPを取得したとは主張しない。`ci-record.json` に確認事項を記録。

### 別方式の通常域検証

`independent_checks.py` は、回転中心＋基底ベクトルで矩形を構成し、線分交差＋凸多角形包含で独立に判定する。対象の `corners` / `intersects` はオラクルとして呼ばない。

- 明白な無干渉、重なり、境界接触、区間途中だけの重なり、深度上限未解決、極小間隔、微小寸法の7例: 期待どおり。
- 固定seedの240例中227例を対象がCLEARと判定。その227例×721角度、計163,667標本で独立計算との重なり矛盾は見つからず。
- 240例のy鏡映・角度符号反転で状態一致。降順角度は現行仕様で入力拒否されるため、直接の逆方向時間パラメータ対応をPASSとしたものではない。
- NaN、Infinity、bool、非正寸法、空群、重複ID、降順・過大角幅、bool深度、負余裕、非正細分幅の12不正入力を拒否。
- 既知の重なり4例の報告を故意にCLEARへ置き換える負対照を、独立オラクルが4/4検出。
- 結果: `independent-results.json`。密走査は連続角度全体の証明でも、全入力の保証でもない。通常域の成功は数値境界の失敗を覆さない。

### 高精度反例

`reproduce_false_clear.py` は mpmath を独立オラクルとして利用し、対象の出力と内部計算値を観測する部分と、幾何学的重なりを証明する部分を分離する。既存に利用可能だった mpmath を使用し、対象プロジェクトの必須依存には追加していない。入力floatをそのまま高精度へ変換し、都合のよい十進値へ置き換えない。

4反例を検査する回帰ゲートはexit 1（正しい拒否）を返した。対象検査器は4/4で誤ったCLEARを返しており、受入FAILを意味する。100桁と160桁の照合結果、詳細数値は `false-clear-results.json` に保存。実装担当が修正したら、同じ4入力を変えずに再実行し、通常域・接触・細分上限・負対照も回帰させる必要がある。本レビューでは実装修正をしていないため、修正後PASSへ変更していない。

追加の `stress_tiny_boundaries.py` は0.01〜60°を0.01°刻みとし、2/4/90 ULP幅の角度区間で、独立高精度計算によって必ず重なる境界治具18,000例を構築した。対象の結果はOVERLAP 17,731、UNRESOLVED 129、誤ったCLEAR 140。これは弱点を狙った反例群であり、一般利用での誤判定率ではない。結果は `tiny-boundary-stress-results.json`。この探索スクリプトのexit 0は探索処理の完了を表し、対象検査器の受入成功を意味しない。

## 5. 公開安全性

6変更ファイルを内容確認し、公開した追加レビュー証拠も自作の合成矩形・検証コード・集計に限定した。変更内にキャラクター外観形状、非公開CAD、専用復元寸法・生成コード、第三者画像・モデル、非公開Space直URL・ID、既知形式の秘密情報は見つからなかった。静的なパターン検査だけではなく、コードとデータ内容を確認した。検査範囲とhashは `public-safety.json`。

非公開原本を開いて比較したわけではないため、「あらゆる第三者権利・秘密の不在」を法的または網羅的に保証するものではない。Issue #4、PR #5、Spaceの原本には変更を加えていない。

## 6. 独立性・未検証

- 実装担当とは別のレビュー担当と数値監査担当が、固定HEADを取得して独自のコード・反例を実行した。対象実装の修正には関与していない。
- 別の計算方式・高精度演算を用いたが、同じクラウド実行環境を共有している。別ハードウェア・別Python実装での再現は未実施。
- mpmathの高精度照合は独立計算であり、形式証明・区間演算による全入力保証ではない。
- 3D実衝突、製造公差、機械強度、トルク、締結、配線は未検証。元の動的干渉5組は未解決のまま。
- 既存の密走査試験は対象と同じ回転・SAT関数を再利用しており、今回の数値欠陥を独立に検出する根拠にはならない。

## 7. 再現手順と次の判断

評価対象HEADを取得し、以下を実行する。結果は第三者環境でも同一であると保証せず、Python・数学ライブラリ・環境を併記する。

```sh
python -m unittest discover -s projects/korosuke/generic-kinematics -v
python <evidence>/independent_checks.py --source projects/korosuke/generic-kinematics/sweep.py --output independent-results.json
python <evidence>/reproduce_false_clear.py --source projects/korosuke/generic-kinematics/sweep.py --output false-clear-results.json --regression-gate
python projects/korosuke/generic-kinematics/sweep.py <evidence>/huge-angle-52.json
python projects/korosuke/generic-kinematics/sweep.py <evidence>/huge-angle-trig-only.json
python projects/korosuke/generic-kinematics/sweep.py <evidence>/huge-pivot.json
python projects/korosuke/generic-kinematics/sweep.py <evidence>/moderate-tiny-boundary.json
```

高精度反例の再現用にmpmathが必要。未導入環境では未実行として記録し、対象プロジェクトの既存9試験成功と代替しない。

現HEADはDraftのまま保持。P2-01/P2-02を修正し、同一反例の正しい拒否・検出、通常入力の保全、最終CIと独立再受入を経て、限定採用を再判定する。
