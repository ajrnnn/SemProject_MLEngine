"""Capture SYNTHETIC HTTP preview evidence without a running server."""
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from matching_system.api import app
ROOT = Path(__file__).resolve().parents[1]
def main():
    baseline = json.loads(subprocess.check_output(['git','show','HEAD:results/day2_synthetic_evaluation.json'],cwd=ROOT))
    subprocess.run([sys.executable,'scripts/evaluate_day2_synthetic.py'],cwd=ROOT,check=True,capture_output=True)
    evaluation = json.loads((ROOT/'results/day2_synthetic_evaluation.json').read_text())
    for key in ['source_sha256','metrics','queries','excluded_uncertain_pairs','no_match']:
        assert evaluation[key] == baseline[key], 'Frozen Day 2 evidence changed: '+key
    with (ROOT/'data/fixtures/day3/demo_reports.csv').open(encoding='utf-8-sig',newline='') as f:
        rows = list(csv.DictReader(f))
    query = next(r for r in rows if r['report_id']=='demo-lost-bottle')
    payload = {k:query[k] for k in ['item_name','description','category_id','location_id','event_date']}
    with TestClient(app) as client:
        health = client.get('/health')
        bottle = client.post('/preview/matches',json={**payload,'limit':3})
        empty = client.post('/preview/matches',json={'item_name':'Telescope','description':'Violet telescope marked SYNTHETIC-X999','limit':3})
        invalid = client.post('/preview/matches',json={})
    assert health.status_code == bottle.status_code == empty.status_code == 200
    assert invalid.status_code == 422
    matches = bottle.json()['matches']
    assert matches[0]['found_report_id'] == 'demo-found-metal'
    assert any(x['found_report_id']=='demo-found-plastic' for x in matches)
    assert all(x['workflow']['ownership_approved'] is False for x in matches)
    assert empty.json()['matches'] == []
    out = dict(evidence='SYNTHETIC ONLY; designed labels, not verified real-world matches or campus accuracy',baseline_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),demo_fixture_sha256=hashlib.sha256((ROOT/'data/fixtures/day3/demo_reports.csv').read_bytes()).hexdigest(),evaluation=evaluation,health=health.json(),cases=[dict(case='authored suggestion and misleading candidate',request=payload,response=bottle.json()),dict(case='empty lexical result',request={'item_name':'Telescope','description':'Violet telescope marked SYNTHETIC-X999'},response=empty.json())],invalid_request_status=invalid.status_code,android='pending: no Android source/build configuration in this checkout')
    (ROOT/'results/day3_api_evidence.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps({'health':health.json(),'bottle':bottle.json(),'empty':empty.json()},indent=2))
if __name__ == '__main__':
    main()
