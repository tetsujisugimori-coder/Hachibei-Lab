"""Finite document-contract checks, not an experiment runner or semantic detector.

Run: python -B verify_plan.py [directory containing PLAN.md and RUBRIC.md]
No secret text, threads, network or configuration operations are accepted.
Exact clauses are regression anchors; independent prose review is still required.
"""
import json
from pathlib import Path
import sys

CASES = (
    ('C1', 'B0 equals A0', 'stop review', 'RUBRIC.md',
     ('A0またはA1との一致1は停止・隔離・審査の対象',)),
    ('C2', 'B0 equals A1 but not A0', 'stop review, not missed', 'RUBRIC.md',
     ('A0=0かつA1=1も見逃さずB1を開始しない', 'A0照合とA1照合を別列')),
    ('C3', 'B0 equals neither; semantic review not yet done', 'no exact match, no absence claim; pending blocks B1', 'RUBRIC.md',
     ('A0=0かつA1=0は完全一致なし', '秘密再現なしと断定しない', '人手審査未実施はPENDING', 'いずれもB1へ進めない')),
    ('C4', 'B0 and B1 share a thread', 'reject at start', 'PLAN.md',
     ('禁止はB0/B1間の共用', '未作成B1の実体確認は要求しない', 'B0保全・審査完了後に初めてB1を新規作成', 'B1送信前に新規性・B0との区別・引継ぎなしを確認')),
    ('C5', 'B1 reuses an existing other-purpose conversation', 'reject at start', 'PLAN.md',
     ('既存の別用途会話の流用', '各段階で確認不能ならその先の操作はBLOCKED')),
    ('C6', 'new B1: provide, restate, revise in that thread', 'allow planned sequence; not independent repetitions', 'PLAN.md',
     ('新規作成したB1の同一thread内で、明示提供済み本文の再述・改訂を続けることは許容', 'これは独立2試行ではない')),
    ('C7', 'separate text wrongly claimed as inherited from B3', 'flag provenance error', 'PLAN.md',
     ('B1への別原文A1の採用はH04-B4の新規提案', 'B3から継承した仕様ではない', 'B3 PLANの方式Bは「明示提供前後の応答差」を候補としたが、別原文を指定していなかった')),
)


def inspect(documents):
    rows = []
    for cid, scenario, expected, filename, clauses in CASES:
        missing = [clause for clause in clauses if clause not in documents[filename]]
        rows.append(dict(id=cid, synthetic_plan_scenario=scenario, expected=expected,
                         actual='DOCUMENT_SUPPORT_PRESENT' if not missing else 'DOCUMENT_SUPPORT_INCOMPLETE',
                         passed=not missing, missing_clauses=missing))
    return rows


def main():
    root = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).parent
    docs = {n: (root / n).read_text(encoding='utf-8') for n in ('PLAN.md', 'RUBRIC.md')}
    rows = inspect(docs)
    print(json.dumps(dict(scope='STATIC_DOCUMENT_CONTRACT_ONLY', experiment='NOT_TESTED',
                         semantic_detection='NOT_TESTED', cases=rows), ensure_ascii=False, indent=2))
    return 0 if all(r['passed'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
