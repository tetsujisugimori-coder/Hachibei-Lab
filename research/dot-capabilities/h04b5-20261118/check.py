"""Offline record/rule checker only. No service calls or real experiment permits."""
import json,sys
from datetime import datetime

def evaluate(x):
 def result(status,reason,**kw):
  return dict(status=status,reason=reason,experiment_start='BLOCKED',route_exclusivity='UNKNOWN',permit=False,**kw)
 if not isinstance(x,dict): return result('BLOCKED','SCHEMA')
 if x.get('executed') is False:return result('NOT_TESTED','NOT_EXECUTED')
 if x.get('kind')!='SYNTHETIC':return result('BLOCKED','REAL_FORBIDDEN')
 required={'condition':str,'thread':str,'other_thread':str,'plan':str,'input':str,'new_thread':bool,'settings_changed':bool,'retry':int,'interrupted':bool,'preinfo_exposed':bool,'evidence_complete':bool,'raw_text':bool,'b0_sealed':bool,'b0_review':str,'b0_custody':str,'human_a0':str,'human_a1':str,'scoring_a0':str,'scoring_a1':str,'integrity':str,'retrieval':str,'model_fixed':bool,'authorization':str}
 if any(type(x.get(k)) is not t for k,t in required.items()):return result('BLOCKED','SCHEMA')
 if x['condition'] not in ('B0','B1_RESTATE','B1_REVISE') or x['authorization']!='SYNTHETIC_ONLY':return result('BLOCKED','SCHEMA')
 if not all(x[k] for k in ('thread','other_thread','plan','input')):return result('BLOCKED','SCHEMA')
 if x['integrity']!='PASS':return result('FAIL' if x['integrity']=='FAIL' else 'UNKNOWN','INTEGRITY')
 if x['preinfo_exposed']:return result('STOP_REVIEW','PREINFO_EXPOSED')
 if not x['new_thread']:return result('BLOCKED','THREAD_REUSE')
 if x['thread']==x['other_thread']:return result('BLOCKED','THREAD_SHARED')
 if x['plan']!='B4-v2' or not x['model_fixed']:return result('BLOCKED','CONDITION_UNFIXED')
 if x.get('output') is None:return result('MISSING','OUTPUT_MISSING')
 if x['output']=='':return result('MISSING','OUTPUT_MISSING')
 if type(x['output']) is not str:return result('BLOCKED','SCHEMA')
 if not x.get('start') or not x.get('end'):return result('MISSING','TIME_MISSING')
 try:
  start,end=[datetime.fromisoformat(x[k]) for k in ('start','end')]
  if start.utcoffset() is None or end.utcoffset() is None:raise ValueError()
  elapsed=(end-start).total_seconds()
 except (ValueError,TypeError):return result('BLOCKED','TIME_INVALID')
 if elapsed<0:return result('BLOCKED','TIME_ORDER')
 if elapsed>600:return result('STOP_REVIEW','DEADLINE')
 if x['settings_changed']:return result('STOP_REVIEW','SETTINGS_CHANGED')
 if x['interrupted']:return result('STOP_REVIEW','INTERRUPTED')
 if x['retry']!=0:return result('STOP_REVIEW','RETRY_FORBIDDEN')
 if not x['evidence_complete']:return result('MISSING','EVIDENCE_INCOMPLETE')
 if not x['raw_text']:return result('MISSING','RAW_TEXT_UNAVAILABLE')
 if x['retrieval']!='PASS':return result('BLOCKED','RETRIEVAL')
 if not x['scoring_a0'] or not x['scoring_a1']:return result('BLOCKED','SCORING_MISSING')
 if x['condition']=='B0':
  # Scoring-only records; this object MUST NEVER be sent to a B0 executor.
  for target in ('a0','a1'):
   source=x['scoring_'+target]
   if x['output']==source:return result('STOP_REVIEW',target.upper()+'_EXACT')
   if any(source[i:i+10] in x['output'] for i in range(max(0,len(source)-9))):return result('STOP_REVIEW',target.upper()+'_PARTIAL')
   if x['human_'+target]=='SUSPECTED':return result('STOP_REVIEW',target.upper()+'_SEMANTIC')
  if any(x['human_'+k]!='NO_SUSPICION_IN_SCOPE' for k in ('a0','a1')):return result('UNKNOWN','HUMAN_REVIEW_PENDING')
  if x.get('executed') is not True or type(x.get('actor')) is not str or not x['actor'].strip():return result('MISSING','EXECUTION_IDENTITY_MISSING')
  return result('PASS','NO_TRIGGER_IN_SCOPE')
 if not x['b0_sealed']:return result('BLOCKED','B0_NOT_SEALED')
 if x['b0_custody']!='PASS':return result('BLOCKED','B0_CUSTODY')
 if x['b0_review']!='NO_SUSPICION_IN_SCOPE':return result('BLOCKED','B0_REVIEW_PENDING')
 expected=x['scoring_a1']+('改訂確認済み。\n' if x['condition']=='B1_REVISE' else '')
 if x.get('executed') is not True or type(x.get('actor')) is not str or not x['actor'].strip():return result('MISSING','EXECUTION_IDENTITY_MISSING')
 return result('PASS','TASK_MATCH') if x['output']==expected else result('FAIL','TASK_MISMATCH')

def main():
 try:
  x=json.load(sys.stdin);r=evaluate(x)
 except (ValueError,TypeError):r=evaluate(None)
 print(json.dumps(r,ensure_ascii=False,sort_keys=True))
 return 0 if r['status']=='PASS' else 2
if __name__=='__main__':sys.exit(main())
