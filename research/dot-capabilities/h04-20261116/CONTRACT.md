# H04/1 契約とH03互換境界

H03の既存verify.pyは3取得応答のstructuredContent、threadId、nextCursor、latestTurn.status、items[].truncated/textとv1/v2抽出ファイルを読む。3行文書・32桁hex・UTF-8/LF・指定末尾追加は事前PLANにあるがcompareの形式検査は先頭の「架」のバイトしか検査しない。実原票の意味照合は別担当の読取りで補完されていた。H04は旧原票に新たな形式を遡及適用しない。

H04/1は**新規合成envelopeのみ**を受け入れる。旧API応答を自動変換しない。実原票のthread ID文字体系は公開仕様未確認であり、ここで定義する合成ID規則を実スレッドへ主張しない。H03 verifier/testを不変で回帰実行する。

JSONはUTF-8 BOMなし、LF、末尾LF、1MiB以下。重複key、NaN/Infinity、未知field、欠損、型違いを拒否する。最上位キーはコードkeysの完全一致。schema=H04/1、mode=synthetic。

文書はid(英字開始の英数underscore/hyphen 3〜64文字)、version=v1、body、sha256。bodyの新規形式は「架空H04\n識別子:32桁小文字hex\n説明:空でない単一行\n」。この規則はH03にない新しい版として固定。hashは実UTF-8 bytesから再計算。再述は全byte一致、改訂は指定「確認済み\n」の追記だけ許容。

threadsは異なる合成A/B。observationsはcreated(A)、before(B)、transfer(B)、after(B)の4件、sequence=0,1,2,3、識別子非重複、complete=true、truncated=false。全てpaired-001、independent_trials=1。同一Bの前後は一対であり独立2試行には数えない。実タイムスタンプを捏造せず、合成の順序だけ検査する。

routesは7経路を過不足/重複なしで保持。requested/accepted/appliedは別項目だがこの版は実適用を証明しない。applied=YESは拒否。evidenceの形式・hash表記検査は実ファイル存在/出所認証ではない。claim=UNKNOWNを強制する。actual route判定とformat PASSは独立。

失敗はreason codeを返し、content/revisionはNOT_TESTEDのまま。例外は入力構文・Unicode・深さ超過を構造化し、不明入力を正常にしない。部分的に内容が合っていても契約全体不成立ならformat FAIL。受入可能性の範囲はこのバージョンに限定し、任意プラットフォームログ監査器ではない。

本文と同じenvelope内のhashを両方改変した場合、この検査だけで真正性を保証しない。版の真正性は外部固定manifest・Git blob・保存後再取得の別工程で担保する。合成envelope内hashは一貫性検査であり署名/認証ではない。
