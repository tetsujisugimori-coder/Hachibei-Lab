"""All inputs are invented synthetic data, never private H03 identifiers."""
import copy, hashlib, json, pathlib, unittest
from verify import validate, ROUTES

def fixture():
    body = '架空H04\n識別子:0123456789abcdef0123456789abcdef\n説明:合成専用\n'
    return dict(schema='H04/1', mode='synthetic', document=dict(id='doc-001',version='v1',body=body,sha256=hashlib.sha256(body.encode()).hexdigest()),restatement=body,revision=body+'確認済み\n',threads=dict(A='synthetic-A',B='synthetic-B'),observations=[dict(id=f'obs-{i:03}',kind=k,thread='synthetic-A' if i==0 else 'synthetic-B',sequence=i,complete=True,truncated=False,trial='paired-001') for i,k in enumerate(('created','before','transfer','after'))], independent_trials=1,routes=[dict(route=r,requested='UNKNOWN',accepted='UNKNOWN',applied='UNKNOWN',self_report='',evidence=[],claim='UNKNOWN') for r in ROUTES],automatic_sharing='UNKNOWN')

def encode(d): return (json.dumps(d,ensure_ascii=False)+'\n').encode()

def cases():
    result = [('normal',encode(fixture()),None)]
    def add(name, edit, reason):
        d=fixture();edit(d);result.append((name,encode(d),reason))
    add('body_mutation',lambda d:d['document'].update(body=d['document']['body'].replace('合成','変更')),'BODY_HASH')
    add('retelling',lambda d:d.update(restatement='別文\n'),'RESTATEMENT_MISMATCH')
    add('revision',lambda d:d.update(revision=d['restatement']+'余分\n'),'REVISION_MISMATCH')
    add('identifier',lambda d:d['document'].update(id='!'),'DOCUMENT_ID_VERSION')
    add('missing',lambda d:d.pop('revision'),'ENVELOPE_STRUCTURE')
    add('type',lambda d:d.update(document=[]),'DOCUMENT_STRUCTURE')
    add('empty',lambda d:d['document'].update(body=''),'TEXT_FORMAT')
    add('unknown_field',lambda d:d.update(extra=0),'ENVELOPE_STRUCTURE')
    add('missing_record',lambda d:d['observations'].pop(),'RECORD_COUNT')
    add('thread_collision',lambda d:d['threads'].update(B='synthetic-A'),'THREAD_IDENTITY')
    add('thread_mismatch',lambda d:d['observations'][3].update(thread='other-B'),'OBSERVATION_IDENTITY_ORDER')
    add('order',lambda d:d['observations'][2].update(sequence=3),'SEQUENCE')
    add('bool_sequence',lambda d:d['observations'][0].update(sequence=False),'SEQUENCE')
    add('truncated',lambda d:d['observations'][1].update(truncated=True),'INCOMPLETE_RECORD')
    add('duplicate_observation',lambda d:d['observations'][1].update(id='obs-000'),'OBSERVATION_ID')
    add('double_trial',lambda d:d.update(independent_trials=2),'INDEPENDENCE_OVERCOUNT')
    add('self_report_control',lambda d:d['routes'][0].update(applied='YES',self_report='blocked'),'UNVERIFIED_CONTROL_APPLICATION')
    add('self_report_route',lambda d:d['routes'][1].update(claim='PASS',self_report='transfer'),'UNSUPPORTED_ROUTE_CLAIM')
    add('automatic_inference',lambda d:d.update(automatic_sharing='PASS'),'AUTOMATIC_SHARING_INFERENCE')
    add('duplicate_route',lambda d:d['routes'][1].update(route='history'),'ROUTE_ID')
    add('real_mode',lambda d:d.update(mode='real'),'SCHEMA_MODE')
    result.extend([('huge_integer',b'{"x":'+b'1'*5000+b'}\n','ValueError'),('syntax',b'{\n','JSONDecodeError'),('utf8',b'\xff\n','UnicodeDecodeError'),('crlf',encode(fixture()).replace(b'\n',b'\r\n'),'JSON_ENCODING'),('duplicate_json',b'{"x":1,"x":2}\n','DUPLICATE_JSON_KEY'),('top_array',b'[]\n','ENVELOPE_STRUCTURE')])
    return result

class Controls(unittest.TestCase):
    pass

def make_test(raw,reason):
    def test(self):
        r=validate(raw)
        self.assertEqual(r['format'],'FAIL' if reason else 'PASS')
        self.assertEqual(r['reasons'],[reason] if reason else [])
        self.assertEqual(r['acquisition_route'],'UNKNOWN')
        self.assertEqual(r['automatic_sharing'],'UNKNOWN')
    return test
for name,raw,reason in cases(): setattr(Controls,'test_'+name,make_test(raw,reason))

if __name__=='__main__': unittest.main()
