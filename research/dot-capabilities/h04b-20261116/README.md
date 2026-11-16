# H04-B 開始前基盤（実験は未承認）

- PLAN.md: スコープ、A/B0/B1、事前判定、停止条件。
- READINESS.json / ROUTE-AUDIT.md: 9開始条件と7経路を別管理。
- CONTAMINATION.md: B0混入/B1独立性・H04-D引継ぎ。
- gate.py: 純粋データの開始条件判定。通信/権限設定/実験起動機能なし。
- test_gate.py: 正常/異常/UNKNOWN/BLOCKEDの合成検証。

`python -m unittest discover -s research/dot-capabilities/h04b-20261116 -v`
`python research/dot-capabilities/h04b-20261116/gate.py research/dot-capabilities/h04b-20261116/READINESS.json`

contract PASSは入力契約の整合、logical_gate PASSは合成前提がすべて満たされた仮定上の結果。execution_allowedは常にfalse。real modeは未実装で拒否。今回の本物の準備台帳はlogical_gate BLOCKED。実験承認・実設定・秘密正解・thread独立性は未成立。実際の共有機能や経路排他性はUNKNOWN。

H03は同じBの前後1事例。H04-A/Cはsynthetic envelopeの形式検査。今回のH04-B準備は開始条件のみ、既存検証器や研究結果を置換しない。親Draft PR #42未マージに依存する積上げ成果。
