import json,glob,sys,datetime as dt,collections
P=lambda s:dt.datetime.fromisoformat(s.replace('Z','+00:00'))
js={}
for f in glob.glob(sys.argv[1]+'/*'):
    for j in json.load(open(f))['jobs']['jobs']: js[j['id']]=j
b=[j for j in js.values() if j['name'][:1]=='b' and j['name'][1:2].isdigit()]
print('jobs',len(b), collections.Counter((j['run_attempt'],j['status'],j.get('conclusion')) for j in b))
b1=[j for j in b if j['run_attempt']==1]
t0=min(P(j['created_at']) for j in b1)
st=sorted((P(j['started_at'])-t0).total_seconds()/60 for j in b1 if j['status']!='queued')
f=lambda i: round(st[i-1],1) if len(st)>=i else None
print('first',f(1),'400',f(400),'785',f(785),'last',round(st[-1],1))
q=sorted((P(j['started_at'])-P(j['created_at'])).total_seconds()/60 for j in b1)
print('queue p50',round(q[len(q)//2],1),'p90',round(q[int(len(q)*.9)],1),'max',round(q[-1],1))
ev=[]
for j in b1:
    ev+=[(P(j['started_at']),1),(P(j['completed_at']) if j.get('completed_at') else dt.datetime.now(dt.timezone.utc),-1)]
ev.sort(); c=p=0
for t,d in ev: c+=d; p=max(p,c)
print('peak',p)
