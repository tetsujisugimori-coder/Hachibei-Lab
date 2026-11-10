#!/usr/bin/env python3
"""Bounded public data checks. Never imports owner-only evidence or certifies adoption."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse, unquote
from jsonschema import Draft202012Validator
ROOT = Path(__file__).resolve().parents[2]
BASE = 'e485df5718d6324c1ad2592d61833f5217c56d57'
WORKFLOW = '.github/workflows/stage2-relations.yml'
def require(ok, message):
    if not ok: raise ValueError(message)
def unique(rows, key):
    values=[r[key] for r in rows]
    require(len(values)==len(set(values)), 'duplicate '+key)
    return set(values)
def validate_data(data, schema, source_index, snapshots):
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(data)
    require(data['visibility']=='PUBLIC','private dataset in public validator')
    groups=[('sources','source_id'),('rules','rule_id'),('relations','relation_id'),('conflicts','conflict_id'),('proposals','proposal_id'),('scenarios','scenario_id')]
    ids={g:unique(data[g],k) for g,k in groups}
    require(ids['sources']=={'PUB-001','PUB-002'},'public source set is restricted to Stage 1')
    for group,prefix,count in [('rules','PLAN-',4),('relations','REL-PUB-',4),('conflicts','OPEN-',7),('proposals','S3-',7)]:
        require(ids[group]=={prefix+f'{n:03}' for n in range(1,count+1)},'required '+group+' set incomplete or expanded')
    sources={r['source_id']:r for r in source_index['sources']}
    snaps={r['id']:r for r in snapshots['records']}
    require(len(snaps)==len(snapshots['records']),'duplicate source snapshot')
    rules={r['rule_id']:r for r in data['rules']}
    for r in data['sources']:
        origin=sources[r['source_id']]
        require(r['title']==origin['title'] and r['location']==origin['original_location'],'source identity mismatch')
        require(r['stage1_ref']=='stage1/public-index.json#'+r['source_id'],'Stage 1 reference mismatch')
        require(r['body_check']==origin['body_check_status'],'unverified source promoted')
        require(r['publication_status']=='PUBLIC' and r['classification']=='RESEARCH_PLAN','private or reclassified source')
        require(r['edition']=='UNKNOWN','invented edition')
    def citation(c):
        require(c['source_id'] in ids['sources'],'dangling citation source')
        expected='ISSUE-'+str(int(c['source_id'][-3:]))+'-CURRENT'
        require(c['snapshot_id']==expected,'citation points to different source')
        ss=snaps[expected]; body=ss['body']
        require(hashlib.sha256(body.encode()).hexdigest()==ss['body_sha256']==c['body_sha256'],'source hash mismatch')
        require(1<=c['start_line']<=c['end_line']<=len(body.splitlines()),'citation range invalid')
        selected='\n'.join(body.splitlines()[c['start_line']-1:c['end_line']])
        require(c['quote'] in selected,'quote not at cited lines')
        require(c['quote'].count('\n')==c['end_line']-c['start_line'],'citation range overstated')
    for r in data['rules']:
        require(r['source_id'] in ids['sources'],'dangling rule source'); citation(r['citation'])
        require(r['source_id']==r['citation']['source_id'],'rule quote source mismatch')
        require(r['authority_category']=='RESEARCH_PLAN' and r['document_status']=='RESEARCH_ONLY' and r['application_state']=='NOT_A_RULE','plan promoted to formal rule')
        require(r['approval_evidence']==r['effective_from']==r['effective_until']=='UNKNOWN','invented approval or effective period')
        require(r['runtime_verification']=='NOT_TESTED','runtime claim unsupported')
    seen=set()
    for r in data['relations']:
        require(r['source_id'] in ids['sources'] and r['rule_id'] in ids['rules'],'dangling relation'); citation(r['citation'])
        require(r['citation']['source_id']==r['source_id'],'relation quote source mismatch')
        require(r['source_claim']==r['citation']['quote'],'source text and interpretation mixed')
        key=(r['source_id'],r['rule_id'],r['citation']['quote'],r['kind'])
        require(key not in seen,'duplicate relation');seen.add(key)
        require(bool(r['limitations']) and bool(r['cautions']) and bool(r['next_questions']),'missing interpretation limits')
        if r['kind']=='PROPOSAL':require(r['proposal_id'] in ids['proposals'],'unlinked proposal')
        elif r['proposal_id'] is not None:require(r['proposal_id'] in ids['proposals'],'dangling proposal')
        if r['kind']=='UNKNOWN':require(r['strength']=='INSUFFICIENT','unknown relationship overstated')
        if r['kind']=='DIRECT':require(r['strength']=='TEXT_MATCH','direct relation lacks bounded text correspondence')
    for r in data['conflicts']+data['proposals']:
        require(set(r['rule_ids'])<=ids['rules'],'dangling rule reference')
        if 'source_ids' in r:require(set(r['source_ids'])<=ids['sources'],'dangling conflict source')
    require(ids['scenarios']=={f'CASE-{n:03}' for n in range(1,7)},'six required scenarios missing')
    for r in data['scenarios']:
        require(r['status']=='DESIGN_ONLY' and not r['public_evidence'],'unobserved model promoted to implementation')
        require(len(r['steps'])>=7 and bool(r['not_proven']),'incomplete scenario')
    return ['strict_schema','unique_ids','stage1_identity_reuse','source_text_hashes','exact_quote_lines','referential_integrity','no_automatic_adoption','interpretation_separation','six_design_scenarios']
def validate_scope(paths):
    require(all(p.startswith('stage2/') or p==WORKFLOW for p in paths),'change outside Stage 2')
def scan(root):
    patterns=[r'(?i)(?:page_|libfile_|file_)[0-9a-f]{16,}',r'(?i)Sentinel_[0-9a-f]{16,}',r'(?i)(?:sk-[a-z0-9]{20,}|gh[pousr]_[a-z0-9]{20,})',r'(?i)-----BEGIN [A-Z ]*PRIVATE KEY-----',r'(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}',r'(?i)/work'+r'space/|/ho'+r'me/|/Us'+r'ers/']
    files=sorted(p for p in (root/'stage2').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')+[root/WORKFLOW]
    for p in files:
        text=p.read_text()
        for pattern in patterns:require(not re.search(pattern,text),'sensitive-pattern candidate: '+str(p.relative_to(root)))
        for url in re.findall(r'''https?://[^\s<>"'`)]+''',text):
            u=urlparse(url.rstrip('.,'));require(u.hostname in {'github.com','json-schema.org'},'unapproved external URL')
            require(not u.query,'URL query not permitted')
        if p.suffix=='.md':
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
                if '://' in target or target.startswith('#'):continue
                clean=unquote(target.split('#')[0]); require((p.parent/clean).resolve().is_relative_to(root.resolve()),'link escapes repository')
                require((p.parent/clean).exists(),'broken repository link: '+clean)
    return len(files)
def run(root=ROOT):
    read=lambda p:json.loads((root/p).read_text())
    data=read('stage2/public-relations.json')
    passed=validate_data(data,read('stage2/relations.schema.json'),read('stage1/public-index.json'),read('stage1/evidence/public-issues.json'))
    baseline=read('stage2/evidence/baseline.json');require(baseline['base']==BASE,'base changed')
    git=lambda *args:subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
    existing=git('ls-tree','-r','--name-only',BASE).splitlines()
    require(set(existing)==set(baseline['protected']),'baseline inventory missing')
    for p in existing:
        original=subprocess.check_output(['git','-C',str(root),'show',BASE+':'+p])
        require(hashlib.sha256(original).hexdigest()==baseline['protected'][p],'baseline hash changed')
        require((root/p).read_bytes()==original,'existing source or rule modified: '+p)
    validate_scope(git('diff','--name-only',BASE).splitlines()+git('ls-files','--others','--exclude-standard').splitlines())
    template=read('stage2/private-relations-template.json')
    require(all(template[k]==[] for k in ['sources','rules','relations','conflicts','proposals','scenarios']),'private template not empty')
    Draft202012Validator(read('stage2/relations.schema.json')).validate(template)
    scanned=scan(root)
    passed+=['all_base_files_byte_unchanged','scope_allowlist','empty_private_template','bounded_public_scan','repository_links_exist']
    return {'result':'PASS','checks':passed,'public_counts':{k:len(data[k]) for k in ['sources','rules','relations','conflicts','proposals','scenarios']},'formal_rules_adopted':0,'scanned_files':scanned,'not_proven':['Private evidence by public CI','Current adoption of owner-only rules','Every external link remains live','All possible secrets absent','Complete research corpus','Actual autonomy or runtime behavior','CI success from local run']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    print(json.dumps(run(a.root),ensure_ascii=False,indent=2))
