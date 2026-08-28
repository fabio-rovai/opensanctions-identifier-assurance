import sys, json
# stream stdin (ftm json, one entity per line), extract embedded identifiers
IDPROPS = ['leiCode','swiftBic','wikidataId','isinCode','okpoCode','innCode',
           'ogrnCode','vatCode','registrationNumber','imoNumber','permId','figiCode']
out = open('raw/idents.jsonl','w')
n=0; kept=0
schema_ct={}
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    try: e=json.loads(line)
    except: continue
    n+=1
    schema_ct[e.get('schema')]=schema_ct.get(e.get('schema'),0)+1
    props=e.get('properties') or {}
    rec={'id':e.get('id'),'schema':e.get('schema')}
    hit=False
    for p in IDPROPS:
        if p in props:
            rec[p]=props[p]; hit=True
    refs=props.get('referents') or e.get('referents')
    if refs: rec['n_referents']=len(refs)
    if hit:
        out.write(json.dumps(rec)+'\n'); kept+=1
    if n % 500000 == 0:
        print(f'{n} entities, {kept} with identifiers', file=sys.stderr)
out.close()
json.dump({'total':n,'with_ids':kept,'schemas':schema_ct}, open('raw/extract_stats.json','w'))
print(f'DONE {n} entities, {kept} with embedded identifiers', file=sys.stderr)
