# Stage 2 研究資料と規則の関係

Stage 1の資料IDを再利用し、本文・解釈・規則の地位・未承認提案を別々に追跡する研究基盤。正式規則の制定、採用、失効、権限拡張を行う仕組みではない。

- [対応台帳](public-relations.json) / [項目定義](ledger-format.md) / [JSON Schema](relations.schema.json)
- [規則体系図](governance-map.md)
- [矛盾と未決定事項](conflicts.md)
- [行動適用モデルと6事例](behavior-model.md)
- [Stage 3候補](stage3-proposals.md)
- [総合報告](report.md) / [検証方法](verification.md)

公開台帳は既存の公開研究計画2資料、計画境界4条項、4対応だけを扱う。正式規則4件という意味ではない。本人限定の研究原本・規則本文・承認履歴の実照合は別保存先に保ち、公開repo・CIに本文・具体名称・ID・内部所在・私有集計を入れない。[空テンプレート](private-relations-template.json)は実資料でも調査済み証拠でもない。

## 開始点と変更境界

基準mainは `e485df5718d6324c1ad2592d61833f5217c56d57`。Stage 1 [PR #3](https://github.com/tetsujisugimori-coder/Hachibei-Lab/pull/3) は2026-11-09T23:37:48Zにマージ済み。Stage 1の限定棚卸し受入は引き継ぐが、全原典読了・全規則採用の認定には拡張しない。

開始時の未解決Issueは #1・#2・#4・#9・#11、未マージPRは #5・#12。研究基盤の依存はStage 1のみ。他案件を変更しない。Issue #2本文の過去のDraft表示より、PR APIの現在のmerged状態を優先して事実を記録した。Stage 1文書の旧Stage 2提案は履歴として保存し、今回の依頼で認められていない移行・改訂・能力実験を自動開始しない。

base treeにAGENTS.mdは存在しなかった。不存在の規則を作らず、READMEとStage 1文書、アクセス可能な既存資料を確認する。基準時点に存在した全ファイルのバイト不変を検査する。変更はstage2/と専用CIの追加のみ。

## 再検査

```sh
python -m pip install jsonschema==4.26.0
python -m unittest discover -s stage2/tools -v
python -m unittest discover -s stage1/tools -v
python stage2/tools/validate_relations.py
git diff --check e485df5718d6324c1ad2592d61833f5217c56d57...HEAD
```

公開台帳を検索する例：`python -c 'import json; d=json.load(open("stage2/public-relations.json")); print([r for r in d["relations"] if r["rule_id"]=="PLAN-002"])'`。私有台帳は別の本人限定検索対象であり、公開CIに渡さない。
