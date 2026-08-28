import json, re, collections

def alpha_to_num(v): return "".join(c if c.isdigit() else str(ord(c)-55) for c in v)
LEI_RE = re.compile(r"^[0-9A-Z]{18}[0-9]{2}$")
def lei_ok(v):
    v=(v or "").strip()
    if not LEI_RE.match(v): return False, "malformed" if v else "empty"
    return (int(alpha_to_num(v))%97==1), None if int(alpha_to_num(v))%97==1 else "checksum"

BIC_RE = re.compile(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$")
def bic_ok(v):
    v=(v or "").strip().upper()
    return bool(BIC_RE.match(v))

QID_RE = re.compile(r"^Q[1-9][0-9]*$")
def qid_ok(v): return bool(QID_RE.match((v or "").strip()))

# ISIN: 12 chars, 2-letter country + 9 alnum + check digit (Luhn over base36-expanded)
ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
def isin_ok(v):
    v=(v or "").strip().upper()
    if not ISIN_RE.match(v): return False
    s="".join(c if c.isdigit() else str(ord(c)-55) for c in v[:-1])
    digits=[int(x) for x in s]
    tot=0
    for i,d in enumerate(reversed(digits)):
        d = d*2 if i%2==0 else d
        tot += d-9 if d>9 else d
    check=(10-(tot%10))%10
    return check==int(v[-1])

VALID = {'leiCode':lei_ok, 'swiftBic':lambda v:(bic_ok(v),None if bic_ok(v) else 'malformed'),
         'wikidataId':lambda v:(qid_ok(v),None if qid_ok(v) else 'malformed'),
         'isinCode':lambda v:(isin_ok(v),None if isin_ok(v) else 'checksum-or-malformed')}

report={}
examples=collections.defaultdict(list)
for prop,fn in VALID.items():
    total=checked=conf=0
    reasons=collections.Counter()
    seen_val=collections.defaultdict(set)  # value -> entity ids (multiplicity)
    for line in open('raw/idents.jsonl'):
        r=json.loads(line)
        if prop not in r: continue
        vals=r[prop] if isinstance(r[prop],list) else [r[prop]]
        for v in vals:
            total+=1
            ok,reason=fn(v)
            checked+=1
            if ok: conf+=1
            else:
                reasons[reason]+=1
                if len(examples[prop])<25: examples[prop].append({'id':r['id'],'schema':r['schema'],'value':v})
            seen_val[v.strip()].add(r['id'])
    multi={v:sorted(ids) for v,ids in seen_val.items() if len(ids)>1}
    report[prop]={'total':total,'conformant':conf,'nonconformant':total-conf,
                  'pct_conformant':round(100*conf/total,3) if total else None,
                  'reasons':dict(reasons),
                  'values_on_multiple_entities':len(multi),
                  'multi_examples':dict(list(multi.items())[:8])}
report['examples']=dict(examples)
json.dump(report,open('reports.json','w'),indent=1,default=str)
for p in VALID:
    d=report[p]; print(f"{p}: {d['conformant']}/{d['total']} conformant ({d['pct_conformant']}%), "
          f"{d['nonconformant']} bad {dict(d['reasons'])}, {d['values_on_multiple_entities']} shared across entities")
