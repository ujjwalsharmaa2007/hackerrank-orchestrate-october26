"""Read structured evidence without assuming that one SQL file covers all systems.

Every observation is tied to its actual evidence ID and capture time. A
positive readback is not treated as a successful deletion merely because an
activity log reports SUCCESS.
"""
import csv
import json
import re
from functools import lru_cache
from pathlib import Path
from database_reader import load_sql_evidence

DATASET = Path(__file__).resolve().parent.parent / 'dataset'
RESOURCE = re.compile(r'\b(?:account|search|support|export|analytics|audit_record|data_flow|backup|tombstone)_[A-Za-z0-9]+\b')
TRACE = re.compile(r'\btrace_id=([^\s]+)')
KV = re.compile(r'([A-Za-z_][A-Za-z_0-9]*)=("[^"]*"|[^\s]+)')


def recursive_match(obj, identifiers):
    if isinstance(obj, dict):
        return any(recursive_match(v, identifiers) for k, v in obj.items() if k not in ('resource_id', 'archive_key'))
    if isinstance(obj, list):
        return any(recursive_match(v, identifiers) for v in obj)
    return isinstance(obj, str) and obj.strip().lower() in identifiers


def read_json_rows(data, meta):
    rows = []
    def add(record, system='', collection='', observed=''):
        if not isinstance(record, dict) or not record.get('resource_id'):
            return
        rows.append({'resource_id':record['resource_id'], 'record':record,
                     'system_id':record.get('system') or system,
                     'collection_name':record.get('record_type') or collection,
                     'observed_at':record.get('observed_at') or record.get('recorded_at') or observed or meta['captured_at'],
                     'evidence_id':meta['file_id'], 'captured_at':meta['captured_at']})
    for snap in data.get('snapshots', []):
        for record in snap.get('records', []):
            add(record, snap.get('data_store',''), snap.get('collection',''), snap.get('captured_at',''))
    for record in data.get('records', []):
        add(record, data.get('source') or data.get('origin',''), data.get('collection',''), data.get('captured_at',''))
    for system, groups in data.get('service_exports', {}).items():
        if not isinstance(groups,dict): continue
        for collection, items in groups.items():
            if isinstance(items,list):
                for record in items: add(record,system,collection)
    return rows


def read_log_rows(text, meta):
    rows=[]
    pending={}
    for line in text.splitlines():
        fields={k:v.strip('"') for k,v in KV.findall(line)}
        if ' {' in line:
            try:
                fields.update(json.loads(line[line.index(' {')+1:]))
            except (ValueError,TypeError):pass
        trace=fields.get('trace_id')
        resource=fields.get('resource_id')
        if not resource:
            continue
        if trace and ('started' in fields.get('event','') or 'lookup_key' in fields):
            pending[trace]=fields
        if trace and trace in pending:
            # Attach the lookup identity to the completed readback with same trace.
            fields={**pending[trace],**fields}
        if not any(token in fields.get('event','') for token in ('completed','read','query','lookup','check','result','evaluated','restore','sync')):
            continue
        rows.append({'resource_id':resource,'record':fields,'system_id':fields.get('service',''),
                     'collection_name':fields.get('event',''), 'observed_at':line[:20],
                     'evidence_id':meta['file_id'],'captured_at':meta['captured_at']})
    return rows


@lru_cache(maxsize=1)
def all_observations():
    with (DATASET/'evidence_files.csv').open(encoding='utf-8-sig',newline='') as f:
        files=list(csv.DictReader(f))
    result=[]
    for meta in files:
        path=DATASET/meta['file_path']
        suffix=path.suffix.lower()
        try:
            if suffix=='.sql':
                for r in load_sql_evidence(meta['file_id']):
                    result.append({'resource_id':r['resource_id'],'record':r['record'],
                                   'system_id':r['origin_system'], 'collection_name':r['collection_name'],
                                   'observed_at':r.get('updated_at') or meta['captured_at'],
                                   'evidence_id':meta['file_id'],'captured_at':meta['captured_at']})
            elif suffix=='.json':
                result.extend(read_json_rows(json.loads(path.read_text(encoding='utf-8-sig')),meta))
            elif suffix=='.log':
                result.extend(read_log_rows(path.read_text(encoding='utf-8-sig'),meta))
            elif suffix=='.txt':
                for line in path.read_text(encoding='utf-8-sig').splitlines():
                    parts=[p.strip() for p in line.lstrip('- ').split('|')]
                    if len(parts)!=6 or not parts[2].startswith(('account_','search_','support_','analytics_','audit_record_','data_flow_','backup_','export_')):continue
                    observed,system,resource,kind,status,subject=parts
                    result.append({'resource_id':resource,'record':{'resource_id':resource,'record_type':kind,'result':status,'subject_reference':subject},'system_id':system,'collection_name':kind,'observed_at':observed,'evidence_id':meta['file_id'],'captured_at':meta['captured_at']})
        except (ValueError, OSError, UnicodeError) as error:
            print('Evidence warning:',meta['file_id'],str(error))
    return result


def get_subject_observations(identity, audit_at, user=None):
    identifiers={str(v).strip().lower() for v in identity['user_ids']+identity['emails'] if v}
    if user:
        for key in ('email_hash','phone','name'):
            if user.get(key):identifiers.add(user[key].strip().lower())
    matched=[]
    for row in all_observations():
        if row['captured_at']>audit_at or row['observed_at']>audit_at:
            continue
        if recursive_match(row['record'],identifiers):
            matched.append(row)
    # Once a resource is linked to the user, include subsequent readbacks for
    # that resource even if PII has already been erased.
    ids={r['resource_id'] for r in matched}
    for row in all_observations():
        if row['resource_id'] in ids and row['captured_at']<=audit_at and row['observed_at']<=audit_at and row not in matched:
            matched.append(row)
    return matched
