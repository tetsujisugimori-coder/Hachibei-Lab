import sys,pathlib,copy,json,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]))
from validate_fixture_results import validate
shape={'a':[0,0,0],'b':[.5,0,0],'size_a':[1,1,1],'size_b':[1,1,1]}
row={'id':'known-overlap',**copy.deepcopy(shape),'expected_volume_mm3':.5,'measured_volume_mm3':.5,'expected_distance_mm':0.,'measured_distance_mm':0.,'status':'VOLUME_OVERLAP'}
trusted={'known-overlap':shape}; assert validate([row],trusted)
checks=[]
def reject(name,r,t):
 try:validate([r],t)
 except ValueError:checks.append({'control':name,'result':'REJECTED'})
 else:raise AssertionError(name+' falsely accepted')
r=copy.deepcopy(row);r.update(expected_volume_mm3=0.,measured_volume_mm3=0.,expected_distance_mm=5.,measured_distance_mm=5.,status='SEPARATED_AT_POSE');reject('forged-both-oracle-and-result',r,trusted)
r=copy.deepcopy(row);r['b']=[8,0,0];reject('forged-input',r,trusted)
micro=copy.deepcopy(shape);micro['b'][0]=1-1e-8;v=1-micro['b'][0];r=dict(row,**micro,expected_volume_mm3=v,measured_volume_mm3=0.,status='MICRO_OVERLAP_REPORTED');reject('erased-positive-micro-volume',r,{'known-overlap':micro})
zero=copy.deepcopy(shape);zero['b'][0]=1;r=dict(row,**zero,expected_volume_mm3=0.,measured_volume_mm3=1e-8,status='CONTACT_OR_WITHIN_TOLERANCE');reject('invented-positive-micro-volume',r,{'known-overlap':zero})
print(json.dumps({'pass':True,'controls':checks},indent=2))
