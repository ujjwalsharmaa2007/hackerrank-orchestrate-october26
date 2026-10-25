"""Evaluate sample requests directly; sample IDs are not in output.csv."""
import csv
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'src'))
from case_evaluator import evaluate_case
with (ROOT/'dataset/sample_deletion_requests.csv').open(encoding='utf-8-sig',newline='') as f:
    requests=list(csv.DictReader(f))
with (ROOT/'dataset/sample_output.csv').open(encoding='utf-8-sig',newline='') as f:
    expected={r['case_id']:r for r in csv.DictReader(f)}
status_correct=0;steps_exact=0
for request in requests:
    actual_status,actual_steps=evaluate_case(request)
    gold=expected[request['case_id']]
    status_correct+=actual_status==gold['deletion_status']
    steps_exact+=actual_steps==json.loads(gold['steps_json'])
    print(f"{request['case_id']}: status={actual_status}, expected={gold['deletion_status']}, steps={len(actual_steps)}")
print(f'\nStatus accuracy: {status_correct}/{len(requests)}')
print(f'Exact step matches: {steps_exact}/{len(requests)}')
