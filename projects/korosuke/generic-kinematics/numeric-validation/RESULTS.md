# PR #8 数値安全性修正の実測記録

2026-11-09。ローカル実行時点の結果。実行コードhash、dirty checkout、コマンド、終了コード、所要時間は `evidence/local-2026-11-09/run-metadata.json`。最終GitHub HEADとCIはPRの追記で固定する。未実施のCIをここで成功とは扱わない。

## P2修正と同一反例

| 元の固定入力 | e5079db (修正前) | 修正後 |
|---|---|---|
| huge-angle-52.json | 誤PROJECTED_CLEAR | UNRESOLVED_2D |
| huge-angle-trig-only.json | 誤PROJECTED_CLEAR | UNRESOLVED_2D |
| huge-pivot.json | 誤PROJECTED_CLEAR | PROJECTED_OVERLAP |
| moderate-tiny-boundary.json | 誤PROJECTED_CLEAR | PROJECTED_OVERLAP |

4入力すべて変更なし。新たな入力拒否0件。旧ゲートexit 1、新ゲートexit 0。
巨大角2例は既定の細分幅では重なりを証明しきれず未解決となる。安全とは言わない。
100/160桁の独立点包含による重なり証拠は維持。

P2-01: 正確な有理数角度・中点・周期正規化、実評価点から端点までの移動上界。
P2-02: 共通ローカル座標、pi/Taylor剰余を含む整数区間演算、離隔の下界と移動の上界。
固定epsilon追加ではない。数学的範囲と前提は NUMERICS.md。

## 元の18,000境界試験の再実測

- 修正前: OVERLAP 17,731 / UNRESOLVED 129 / 誤CLEAR 140。
- 修正後: OVERLAP 18,000 / UNRESOLVED 0 / 誤CLEAR 0。
- 全例に独立100桁の厳密な内点重なり witness。対象実装の幾何関数を正解に再利用しない。
- 前後共通入力corpus SHA256: `09ad0281ddc24ad8366fb81e155aba9b03785e2a8c3fd8a82bba43692dfbcc00`。
- ローカル所要時間: 旧2.79秒、新7.49秒（スクリプト全体、同一実行環境1回の参考値）。精度保証の代償として処理時間増。性能改善とは称さない。
- この境界を狙った試験群は一般利用の失敗率推定ではない。

## 通常域・負対照

- 既存9 unittestを維持し、新規11件と合わせ20件成功。
- 既存中立治具4組はCLEAR維持。
- 独立別方式の通常域240例でCLEAR 227例維持、227×721=163,667角度の有限照合で重なりなし。鏡映差0、例題7、不正入力12、故意の誤CLEAR報告4件の検出も成功。
- 新規ゲート負対照3件（誤CLEAR、件数不足、witness欠落）を拒否。
- 正常な無干渉が一律UNRESOLVEDへ退行していないことを確認。有限照合自体を連続保証とはしない。

## 保全・公開範囲と未検証

すべて自作の汎用矩形・数値反例・検査コード。非公開原本にはアクセス・変更・移動・公開していない。Issue #4、PR #5、原本統合条件は未変更。

独立実装レビュー、最終HEADのCI、GitHub保存の再取得結果はPRへ追記する。Python/整数演算とプログラム実装が正しいとの前提があり、機械検証された形式証明ではない。JSON十進文字列の読込誤差、実測不確かさ、実3D干渉、強度、製造公差、配線、実機は対象外。実CADの動的干渉5組は未解決のまま。
