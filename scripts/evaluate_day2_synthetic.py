"""Reproducible SYNTHETIC fixture evaluation; not campus accuracy."""
import csv, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from matching_system.nlp_retrieval import TextReport, TfidfRanker
ROOT = Path(__file__).resolve().parents[1]
def read(path):
    with (ROOT/path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))
def main():
    reports = read('data/raw/campus/synthetic_campus_reports.csv')
    pairs = read('data/raw/campus/labelled_campus_pairs.csv')
    ids = {r['report_id']: r for r in reports}
    assert len(ids) == len(reports)
    assert all(p['lost_report_id'] in ids and p['found_report_id'] in ids for p in pairs)
    parent = {i:i for i in ids}
    def find(i):
        while parent[i] != i:
            i = parent[i]
        return i
    for p in pairs:
        if p['label'] == 'match':
            a,b = find(p['lost_report_id']),find(p['found_report_id'])
            parent[max(a,b)] = min(a,b)
    def split(i):
        return 'test' if int(hashlib.sha256(find(i).encode()).hexdigest(),16)%3 == 0 else 'development'
    found = [TextReport(r['report_id'],'found',r['description'],r['category']) for r in reports if r['report_type']=='found']
    ranker = TfidfRanker(found)
    queries = []
    for r in reports:
        if r['report_type'] != 'lost': continue
        relevant = {p['found_report_id'] for p in pairs if p['lost_report_id']==r['report_id'] and p['label']=='match'}
        ranking = ranker.rank(TextReport(r['report_id'],'lost',r['description'],r['category']),limit=5)
        ranks = [i+1 for i,x in enumerate(ranking) if x['found_report_id'] in relevant]
        queries.append(dict(query_id=r['report_id'],group=find(r['report_id']),split=split(r['report_id']),relevant=sorted(relevant),ranking=ranking,recall_at_5=len(ranks)/len(relevant) if relevant else None,reciprocal_rank=1/min(ranks) if ranks else 0))
    metrics = {}
    for s in ['development','test','all']:
        q = [q for q in queries if (s=='all' or q['split']==s) and q['relevant']]
        metrics[s] = dict(query_count=len(q),recall_at_5=sum(x['recall_at_5'] for x in q)/len(q) if q else None,mrr_at_5=sum(x['reciprocal_rank'] for x in q)/len(q) if q else None)
    extra = read('data/fixtures/day1/synthetic_queries.csv')
    no_match = []
    for q in extra:
        if q['label'] != 'no_match_in_fixture': continue
        ranked = ranker.rank(TextReport(q['query_id'],'lost',q['description']),limit=5)
        no_match.append(dict(query_id=q['query_id'],returned_count=len(ranked),ranking=ranked))
    out = dict(evidence='SYNTHETIC ONLY; not campus accuracy',inventory_count=len(found),report_count=len(reports),pair_count=len(pairs),excluded_uncertain_pairs=sum(p['label'] in ['plausible','uncertain'] for p in pairs),binary_metrics='not calculated; uncertain excluded; design labels are not verified',metrics=metrics,no_match=dict(query_count=len(no_match),empty_result_count=sum(not x['ranking'] for x in no_match),queries=no_match),queries=queries,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['data/raw/campus/synthetic_campus_reports.csv','data/raw/campus/labelled_campus_pairs.csv']})
    dest = ROOT/'results/day2_synthetic_evaluation.json'
    dest.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps({k:out[k] for k in ['evidence','metrics','no_match','excluded_uncertain_pairs']},indent=2))
if __name__ == '__main__': main()
