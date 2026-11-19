# H04-B5 独立技術レビュー 初回

担当Bは実装Aと別AIセッション。同一基盤・アカウント・共有workspace・履歴継承あり。人的第三者独立監査ではない。実装未読でB4から20境界期待を固定し、その後35既存case・sequence/archiveおよび追加8件を実行した。これは合成文書/実装審査であり実サービス実験ではない。

## 指摘
- P2-01 OPEN: X01 `output=""` がPASS/NO_TRIGGER_IN_SCOPE。空応答を原文字列取得成功として扱えずMISSING等で停止すべき。出力欠落対照はnullだけで不十分。
- P2-02 OPEN: X02 `executed=false` がPASS。未実施をNOT_TESTEDとする契約が合成checkerに欠ける。入力schemaに実施状態を明示し、未実施は結果採点しないこと。
- P3-01 OPEN: X03 actor=nullでもevidence_complete=trueのみでPASS。EVIDENCE必須主体情報と合成票schemaの対応を明示し、対象範囲内の欠落を検知すること。check単体を完全な証拠validatorと呼ばない。

既存35は35/35一致。sequence/archiveのunittest成功。追加8は5成功・3不一致。原入力・事前期待はadditional-oracle.json、実際の応答はadditional-results.json。期待値を実装に合わせて変更していない。

B4のB0/A0/A1両監視、B1独立新規・予定改訂許容・原A1基準、B0保全後B1作成、3枠、600秒/retry0、経路UNKNOWN/実験BLOCKED、合成permit=falseは設計上維持。7経路名・集合も維持。全環境の内部状態/原byte取得にUNKNOWN/NOT_TESTEDが明示され、画面OFFと遮断保証を分離。

採点関数は最初のtriggerでreturnするため両対象の独立採点列を返さない。停止安全性は維持するが、実験用原票はA0/A1各結果を別に取得する必要がある。実運用adapter未実装のため現段階では非blocking範囲限界。

正式受入は指摘修正・同一入力再試験・固定HEAD取得・証拠照合後に判断。実験開始BLOCKEDを維持。
