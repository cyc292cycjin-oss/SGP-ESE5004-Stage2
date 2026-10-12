"""Serialize a light review view of completed exact checks; never reruns arithmetic."""
from pathlib import Path
import hashlib,json,collections

def compact(source):
    source=Path(source)
    raw=source.read_bytes(); data=json.loads(raw)
    selected={3357088,3258844,3455225}
    for family in {r['family'] for r in data['rows']}:
        selected.add(max((r for r in data['rows'] if r['family']==family),
                         key=lambda r:r['A']['violation_original'])['row'])
    result={k:v for k,v in data.items() if k!='rows'}
    result['representation']='LIGHT_REVIEW_VIEW_OF_COMPLETED_FULL_SUPPORT_CHECKS'
    result['full_record']={
        'local_path':str(source).replace('/mnt/d/','D:/'),
        'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
        'preserved_unchanged':True,
        'reproduction_method':'methods/compare_c07.py; uses saved immutable daily CSR/CSC and returned vectors only'}
    result['family_counts']=dict(collections.Counter(r['family'] for r in data['rows']))
    result['selection_rule']='All three diagnostic inventory rows plus maximum exact violation row in each examined family; complete supports retained for these rows. All 533 result summaries and all 7 column checks retained.'
    result['rows']=[]
    for row in data['rows']:
        summary={k:v for k,v in row.items() if k!='support'}
        support=json.dumps(row['support'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
        summary['support_count']=len(row['support'])
        summary['support_canonical_json_sha256']=hashlib.sha256(support).hexdigest()
        summary['support_hash_serialization']='UTF-8 JSON, ensure_ascii=False, sort_keys=True, separators=(comma,colon), no trailing newline'
        summary['complete_support_in_review']=row['row'] in selected
        if row['row'] in selected:summary['support']=row['support']
        result['rows'].append(summary)
    return result

if __name__=='__main__':
    import sys
    src,dst=map(Path,sys.argv[1:3]);assert src.resolve()!=dst.resolve()
    value=compact(src)
    dst.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'rows':len(value['rows']),'columns':len(value['columns']),
                      'complete_review_supports':sum(r['complete_support_in_review'] for r in value['rows']),
                      'review_bytes':dst.stat().st_size,'full_record':value['full_record']},indent=2))
