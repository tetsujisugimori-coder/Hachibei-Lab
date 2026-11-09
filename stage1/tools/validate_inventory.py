#!/usr/bin/env python3
"""Validate public Stage 1 records, not corpus completeness or private evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_PREFIX = 'https://github.com/tetsujisugimori-coder/Hachibei-Lab/'
CI_PATH = '.github/workflows/stage1-inventory.yml'
IMMUTABLE_BASE = '48f5fe96aa6df48de64272f2eabd0bad66d92a5a'
PROTECTED_FILES = ('README.md', 'stage1/evidence/baseline.json',
                   'stage1/evidence/conflicts-before.md', 'stage1/evidence/public-issues.json',
                   'stage1/evidence/unit.log', 'stage1/evidence/validation.json')
DOMAINS = {'EDOBEN', 'PHILOSOPHY', 'BEHAVIOR', 'CONSTITUTION', 'RULES_OPERATIONS'}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def validate_data(index, schema, snapshots, summary):
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(index)
    require(index['visibility'] == 'PUBLIC', 'public index visibility')
    rows = index['sources']
    ids = [r['source_id'] for r in rows]
    require(len(ids) == len(set(ids)), 'duplicate source ID')
    require(set(ids) == {'PUB-001', 'PUB-002'}, 'unexpected public source')
    records = {r['id']: r for r in snapshots['records']}
    require(len(records) == len(snapshots['records']), 'duplicate snapshot ID')
    for s in records.values():
        require(hashlib.sha256(s['body'].encode()).hexdigest() == s['body_sha256'], 'snapshot hash mismatch')
        require(s['url'].startswith(PUBLIC_PREFIX), 'snapshot URL outside verified public repository')
    for r in rows:
        n = int(r['source_id'].split('-')[1])
        s = records[f'ISSUE-{n}-CURRENT']
        require(r['publication_status'] == 'PUBLIC', 'private row in public index')
        require(r['title'] == s['title'], 'title not backed by public source')
        require(r['original_location'] == s['url'] == r['publication_evidence'], 'origin or public evidence mismatch')
        require(r['body_sha256'] == s['body_sha256'], 'body hash mismatch')
        require(r['body_evidence'] == f'evidence/public-issues.json#ISSUE-{n}-CURRENT', 'body evidence mismatch')
        require(r['service_updated_at'] == s['updated_at'], 'updated_at mismatch')
        require(r['service_revision'] == 'UNKNOWN', 'timestamp is not a service revision')
        require(r['application_state'] == 'NOT_A_RULE', 'research plan promoted to rule')
        require(r['document_version'] == 'UNKNOWN', 'undeclared document version')
        require(FormatChecker().conforms(r['last_verified_at'], 'date-time'), 'verification timestamp')
    before = records['ISSUE-2-BEFORE']['body']
    after = records['ISSUE-2-CURRENT']['body']
    paragraph = before.split('## 現在の提出阻害\n', 1)[1].split('\n\n##', 1)[0]
    require(paragraph in after, 'Issue #2 history removed')
    require('## 過去の提出阻害' in after and 'RESOLVED' in after, 'Issue #2 stale current blocker')
    require(set(r['domain'] for r in summary['domains']) == DOMAINS, 'five-domain coverage')
    require(len(summary['domains']) == 5, 'duplicate domains')
    for d in summary['domains']:
        expected = sum(d['domain'] in s['domains'] for s in rows)
        require(d['public_plan_references'] == expected, 'public plan count mismatch')
        require(d['public_research_originals_verified'] == 0, 'plans counted as original research')
        require(d['corpus_total'] == 'UNKNOWN', 'unknown total invented')
        require(d['coverage_ratio'] == 'UNKNOWN', 'coverage ratio invented')
        for field in ('body_verified', 'unverified', 'duplicate_candidates', 'conflict_candidates'):
            require(d[field] == 'PRIVATE_EVIDENCE_ONLY', 'private counts require separate evidence')
    return ['schema_and_required_fields', 'unique_stable_ids', 'public_source_provenance',
            'snapshot_hashes', 'version_and_application_separation', 'issue2_history_preserved',
            'five_domain_public_counts']

def allowed_change(path):
    return path.startswith('stage1/') or path == CI_PATH


def validate_scope(paths):
    require(all(allowed_change(p) for p in paths), 'change outside Stage 1 and its sole CI workflow')


def scan_public_files(root):
    findings = []
    allowed_hosts = {'github.com', 'help.openai.com', 'openai.com', 'json-schema.org'}
    candidates = sorted((root / 'stage1').rglob('*')) + [root / CI_PATH]
    patterns = (
        r'(?i)(?:sk-[a-z0-9]{20,}|gh[pousr]_[a-z0-9]{20,})',
        r'(?i)-----BEGIN [A-Z ]*PRIVATE KEY-----',
        r'(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}',
        r'(?i)(?:file|sediment|library-file|project-file)://',
        r'(?i)(?:page_|libfile_|file_)[0-9a-f]{16,}',
        r'(?i)/work' + r'space/|/ho' + r'me/|/Us' + r'ers/',
        r'(?i)[a-z]:[\\/]' + r'Users[\\/]',
    )
    for p in candidates:
        if not p.is_file() or '__pycache__' in p.parts or p.suffix == '.pyc':
            continue
        text = p.read_text()
        for url in re.findall(r"https?://[A-Za-z0-9][^\s<>\"'\)]+", text):
            parsed = urlparse(url.rstrip('.,'))
            require(parsed.hostname in allowed_hosts, f'unapproved URL host in {p.relative_to(root)}')
            require(not parsed.query, f'URL query in {p.relative_to(root)}')
        for pattern in patterns:
            require(not re.search(pattern, text), f'sensitive-pattern candidate in {p.relative_to(root)}')
        findings.append(str(p.relative_to(root)))
    return findings


def validate_immutable_files(root):
    for name in PROTECTED_FILES:
        expected = subprocess.check_output(['git', '-C', str(root), 'show', IMMUTABLE_BASE + ':' + name])
        require((root / name).read_bytes() == expected, 'immutable public evidence changed: ' + name)
    return list(PROTECTED_FILES)


def run(root=ROOT):
    read = lambda name: json.loads((root / 'stage1' / name).read_text())
    passed = validate_data(read('public-index.json'), read('ledger.schema.json'),
                           read('evidence/public-issues.json'), read('domain-summary.json'))
    template = read('private-ledger-template.json')
    require(template == {'schema_version':'1.0','visibility':'PRIVATE','sources':[]}, 'private template is not empty')
    passed.append('empty_private_template')
    files = scan_public_files(root)
    passed.append('bounded_public_pattern_scan')
    git = lambda *args: subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
    baseline = read('evidence/baseline.json')
    expected = git('show', baseline['previous_review_head'] + ':stage1/conflicts.md') + '\n'
    require((root/'stage1/evidence/conflicts-before.md').read_text() == expected, 'old conflicts history altered')
    require(git('hash-object', 'README.md') == baseline['readme_blob'], 'README changed')
    changed = git('diff','--name-only',baseline['previous_review_head']).splitlines()
    untracked = git('ls-files','--others','--exclude-standard').splitlines()
    validate_scope(changed + untracked)
    protected = validate_immutable_files(root)
    require('RESOLVED' in (root/'stage1/conflicts.md').read_text(), 'resolution absent')
    passed += ['old_conflicts_preserved', 'readme_unchanged', 'scope_limited_to_stage1_and_sole_ci', 'immutable_public_evidence']
    return {'result':'PASS', 'scope':'Public structure and bounded checks only', 'checks':passed,
            'scanned_files':files, 'immutable_files':protected,
            'not_proven':['Corpus completeness', 'Current-rule adoption', 'Private ledger body or ACL',
                          'Absence of every possible secret', 'CI success', 'Final remote HEAD match']}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(run(args.root), ensure_ascii=False, indent=2))
