# H04 Issue #45: 読取専用のアクセス観測と合成混入負対照

対象: Issue #45。H04-A/C・H04-Bの研究基盤がmainに取り込まれた後の **非通信・非秘密** 限定検証。実A/B0/B1作成・送信と設定変更はしない。

- `ACCESS-AUDIT.md`: 現接続で実行したSpaceメタデータ・共有範囲・7経路判定。実測できた部分と未確認項目を分離。
- `preflight.py`: 架空値だけを入力するオフライン漏出検出関数。本文、digest、所在の一致を8個の合成surfaceで確認する。**見つからなくても隔離PASSにはしない**。全結果で`isolation=UNKNOWN`、`execution_allowed=false`。
- `test_preflight.py`: 漏出の正対照、欠測、型不正、非合成モード拒否。
- `test_gate_regression.py`: 7経路×8項目×4非PASSと9開始条件×4非PASSに対して既存H04-B開始ゲートの安全側判定を確認。既存本体は変更しない。
- `VERIFICATION.md`: ローカル・正式CI・独立レビュー・証拠保全を区別した提出記録。

実行: `python3 -m unittest discover -s research/dot-capabilities/h04-issue45-20261116 -p 'test_*.py' -v`

制限: 実対象の取得経路・Memory内部仕様・実B0の混入排除はUNKNOWN。ここでの合成PASSは実験開始承認ではない。原本の削除・移動・上書きなし、公開repoに非公開原票やSpace内部IDを記載しない。小規模テキストのみ、追加予算20MiB、実使用ピーク未測定。
