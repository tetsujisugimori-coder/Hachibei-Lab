# コロ助CAD：権利調査と保存・公開運用案

- 文書ID: KRS-RIGHTS-001 / 改訂1
- 調査日: 2026-11-08 UTC（2026-11-09 JST）
- 総合判定: **PARTIAL**。調査・運用提案であり、個別行為の適法性を保証する法律意見ではない。
- 関連: [Issue #4](https://github.com/tetsujisugimori-coder/Hachibei-Lab/issues/4)、[Draft PR #5](https://github.com/tetsujisugimori-coder/Hachibei-Lab/pull/5)
- 基準main: `6a3088a329df5384a3091c8f1e7338c4d855648f` / tree `f3d62b072541285d8f19e92eb4b65502a2c4a699`
- 読取確認: README、main全tree、PR #5の説明と差分。mainはREADMEのみ、AGENTS.mdは404。PR #5はDraft・未マージ、HEAD `ed0a236d7501e2dbfb61ce4561ebfddb6c9130c1`。先行差分を本branchに混入しない。

## 結論

推奨は **標準案＝C（公開は独自技術のみ）＋D（外観・機構・電子回路・ソフトを分離）**。忠実な外観とそれを再生成するコードは既存非公開保存を維持し、外観表現を含まない汎用機構の研究を続ける。新しいprivate GitHubへの保存は合理的な候補だが、別途承認と利用主体・共有範囲・クラウド利用条件の確認後とする。

ガイドライン未確認は、すべての個人制作が法律上禁止という意味ではない。一方、非営利・自作・privateという表示だけで許諾や例外が成立するわけでもない。**保存、制作、第三者共有、公開配布を別々に判定**する。

## 成果物

- [調査報告](report.md)：公式方針、法律と文化、GitHubの論点
- [出典台帳](sources.json)：根拠区分、実読状態、限界
- [利用形態別判断](risk-matrix.json)：行為と条件を機械可読化
- [運用案・次工程](policy.md)：3案、成果物別境界、実施順序
- [検証記録](verification.md)：文書検証と独立レビューの区別

## 変更しないもの

原本、Space保存先、既存履歴・hash・PR #5、研究・江戸弁等の既存成果は変更しない。Private repo新設、原本移行、権利者問い合わせ、製品開発、マージは実施しない。本提出には画像、CAD、外観生成コード、私有ダウンロードURL、秘密情報を含めない。
