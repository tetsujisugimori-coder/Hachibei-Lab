"""Deterministic adversarial near-tangent cases; not a random accuracy estimate.
Uses 100-digit independent rotation of a known moving corner. Each constructed
fixed box strictly contains that corner at the exact sampled float angle.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import mpmath as mp
mp.mp.dps=100
parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
s=importlib.util.spec_from_file_location('candidate',args.source)
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
counts=Counter();examples=[];input_hash=hashlib.sha256();case_hash=hashlib.sha256()
for i in range(1,6001):
    lo=i/100
    for ulps in (2, 4, 90):
        hi=lo+ulps*math.ulp(lo)
        mid=(lo+hi)/2
        assert lo<mid<hi
        theta=mp.mpf(mid)*mp.pi/180
        x=mp.mpf('1.5')*mp.cos(theta)+mp.mpf('.5')*mp.sin(theta)
        y=mp.mpf('1.5')*mp.sin(theta)-mp.mpf('.5')*mp.cos(theta)
        left=float(x)
        if mp.mpf(left)>=x: left=math.nextafter(left,-math.inf)
        width=2**-20; fx=left+width/2; fy=float(y)
        assert mp.mpf(fx)-mp.mpf(width)/2 < x < mp.mpf(fx)+mp.mpf(width)/2
        assert abs(y-mp.mpf(fy)) < mp.mpf('.5')
        raw={'schema_version':1,'joint':{'pivot_mm':[0,0],'start_deg':lo,'end_deg':hi},
             'moving':[{'id':'m','center_mm':[1,0],'size_mm':[1,1]}],
             'fixed':[{'id':'f','center_mm':[fx,fy],'size_mm':[width,1]}]}
        input_hash.update((json.dumps(raw,sort_keys=True,separators=(',',':'))+'\n').encode())
        result=c.screen(raw)['pairs'][0]
        case_hash.update((json.dumps(result,sort_keys=True,separators=(',',':'))+'\n').encode())
        counts[result['status']]+=1
        if result['status']=='PROJECTED_CLEAR' and len(examples)<5:
            examples.append({'input':raw, 'result':result,
                             'strict_corner_x_penetration_mm':mp.nstr(x-(mp.mpf(fx)-mp.mpf(width)/2),60)})
report={'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),
        'input_corpus_sha256':input_hash.hexdigest(),'case_results_sha256':case_hash.hexdigest(),
        'canonical_serialization':'UTF-8 json.dumps(sort_keys=True,separators=(comma,colon)) + newline, original loop order',
        'description':'Adversarial constructed strict-corner overlaps, ordinary angles 0.01 through 60 degrees at 0.01 spacing, interval spans 2/4/90 angle ULPs. Not a statistical accuracy estimate.',
        'mpmath_digits':100,'total_cases':sum(counts.values()),'all_cases_have_independent_strict_overlap_witness':True,
        'candidate_counts':dict(counts),'false_clear_examples':examples}
args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='false_clear_examples'}))
