"""Private-byte comparison; does not infer sharing mechanisms. Python stdlib only."""
import hashlib, json, pathlib, re, sys

def compare(v1, restatement, revision):
    if not re.fullmatch(rb'\xe6\x9e\xb6.*', v1, re.S):
        raise ValueError('v1 format')
    if restatement != v1:
        raise ValueError('restatement mismatch')
    if revision != v1 + '確認済み\n'.encode():
        raise ValueError('revision mismatch')
    return {'restatement': 'PASS', 'reflection': 'PASS', 'automatic_sharing': 'UNKNOWN'}

def verify(p):
    a=json.loads((p/'Aread.json').read_text())['structuredContent']
    b=json.loads((p/'Bbefore.json').read_text())['structuredContent']
    c=json.loads((p/'Bafter.json').read_text())['structuredContent']
    assert a['threadId'] != b['threadId'] == c['threadId'], 'thread identity'
    for r in [a,b,c]:
        assert r['nextCursor'] is None and r['latestTurn']['status']=='completed'
        assert all(not i['truncated'] for i in r['items'])
    body=re.findall(r'```text\n(.*?)```',a['items'][0]['text'],re.S)[0].encode()
    assert body == (p/'v1.txt').read_bytes(), 'original mismatch'
    marker=re.search(rb'[a-f0-9]{32}',body).group()
    assert marker not in json.dumps(b).encode(), 'baseline leakage'
    blocks=re.findall(r'```text\n(.*?)```',c['items'][0]['text'],re.S)
    result=compare(body,blocks[0].encode(),blocks[1].encode())
    assert blocks[1].encode()==(p/'v2.txt').read_bytes(), 'revision file'
    return result

if __name__=='__main__':
    print(json.dumps(verify(pathlib.Path(sys.argv[1]))))
