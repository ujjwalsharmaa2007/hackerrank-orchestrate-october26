"""Evidence-based, time-bounded deletion audit evaluator."""
import csv
from functools import lru_cache
from pathlib import Path
from audit_agent import detect_deletion_request
from identity_resolver import resolve_identity
from unified_evidence import get_subject_observations

DATASET=Path(__file__).resolve().parent.parent/'dataset'

@lru_cache(maxsize=1)
def identities():
    with (DATASET/'user_identities.csv').open(encoding='utf-8-sig',newline='') as f:
        return {r['user_id']:r for r in csv.DictReader(f)}

@lru_cache(maxsize=1)
def activities():
    with (DATASET/'system_activity.csv').open(encoding='utf-8-sig',newline='') as f:
        result={}
        for row in csv.DictReader(f):result.setdefault(row['resource_id'],[]).append(row)
    for rows in result.values():rows.sort(key=lambda r:r['event_time'])
    return result

PREFIX_POLICY={
    'account':('DELETE','account_service'), 'search':('DELETE','search_service'),
    'export':('DELETE','export_service'), 'analytics':('ANONYMIZE','analytics_platform'),
    'support':('REDACT','support_platform'), 'audit_record':('RETAIN','security_service'),
    'data_flow':('DISABLE_FLOW','integration_service'), 'backup':('BLOCK_RESTORE','backup_service'),
    'tombstone':('REDACT','account_service')
}

def resource_policy(resource_id,observations):
    prefix=next((p for p in sorted(PREFIX_POLICY,key=len,reverse=True) if resource_id.startswith(p+'_')),None)
    if prefix is None:return None
    action,system=PREFIX_POLICY[prefix]
    if prefix=='support':
        # An attachment exclusively owned by the subject can be deleted;
        # shared conversation text is normally redacted.
        if any('attachment' in str(o['collection_name']).lower() for o in observations):action='DELETE'
    return action,system


def observation_state(row, action):
    d=row['record']
    result=str(d.get('result','')).upper()
    if result in ('NOT_FOUND','ABSENT','DELETED'):return 'ABSENT'
    if result in ('FOUND','PRESENT','ACTIVE','IDENTIFIABLE','EXPOSED_PII'):return 'ACTIVE' if action in ('DISABLE_FLOW','BLOCK_RESTORE') else 'PRESENT'
    if result in ('ANONYMIZED','REDACTED','DISABLED','BLOCKED'):return result
    if 'status_code' in d:
        return 'ABSENT' if str(d['status_code'])=='404' else 'PRESENT' if str(d['status_code'])=='200' else None
    if 'http_status' in d:
        return 'ABSENT' if str(d['http_status'])=='404' else 'PRESENT' if str(d['http_status'])=='200' else None
    if 'rows' in d and ('lookup' in str(d.get('event','')) or 'read' in str(d.get('event',''))):
        return 'ABSENT' if str(d['rows'])=='0' else 'PRESENT' if str(d['rows'])=='1' else None
    if action=='BLOCK_RESTORE' and 'deletion_block' in d:
        return 'BLOCKED' if str(d['deletion_block']).lower()=='true' else 'ACTIVE'
    if action=='DISABLE_FLOW':
        if str(d.get('enabled','')).lower() in ('false','0'):return 'DISABLED'
        if str(d.get('enabled','')).lower() in ('true','1'):return 'ACTIVE'
    if action=='BLOCK_RESTORE':
        if str(d.get('restore_allowed','')).lower() in ('false','0'):return 'BLOCKED'
        if str(d.get('restore_allowed','')).lower() in ('true','1'):return 'ACTIVE'
    if action=='ANONYMIZE':
        fields=['user_id','customer_reference','email','phone','email_hash']
        if any(k in d for k in fields):
            return 'ANONYMIZED' if all(d.get(k) in (None,'','null') for k in fields) else 'PRESENT'
    if action=='REDACT':
        fields=['requester_email','requester_name','requester_phone','email','phone','full_name']
        if any(k in d for k in fields):
            return 'REDACTED' if all(d.get(k) in (None,'','null','[REDACTED]') for k in fields) else 'PRESENT'
    if action=='DELETE' and d.get('resource_id'):
        return 'PRESENT'
    if action=='RETAIN' and d.get('resource_id'):
        return 'PRESENT'
    return None

STEP_TYPES={
 'DELETE':(('REPORT_REMAINING_RECORD','PRESENT'),('DELETE_RECORD','ABSENT'),('VERIFY_RECORD_ABSENT','ABSENT')),
 'REDACT':(('REPORT_EXPOSED_PII','PRESENT'),('REDACT_RECORD','REDACTED'),('VERIFY_RECORD_REDACTED','REDACTED')),
 'ANONYMIZE':(('REPORT_EXPOSED_PII','PRESENT'),('ANONYMIZE_RECORD','ANONYMIZED'),('VERIFY_RECORD_ANONYMIZED','ANONYMIZED')),
 'DISABLE_FLOW':(('REPORT_ACTIVE_DATA_FLOW','ACTIVE'),('DISABLE_DATA_FLOW','DISABLED'),('VERIFY_DATA_FLOW_DISABLED','DISABLED')),
 'BLOCK_RESTORE':(('REPORT_RESTORE_RISK','ACTIVE'),('BLOCK_RESTORE','BLOCKED'),('VERIFY_RESTORE_BLOCKED','BLOCKED')),
 'RETAIN':(None,None,('VERIFY_RECORD_PRESENT','PRESENT'))
}

def evaluate_case(request):
    if not detect_deletion_request(request['request_text']):return 'NOT_APPLICABLE',[]
    identity=resolve_identity(request['email'])
    user=next((identities().get(uid) for uid in identity['user_ids'] if uid in identities()),None)
    rows=get_subject_observations(identity,request['audit_at'],user)
    groups={}
    for row in rows:groups.setdefault(row['resource_id'],[]).append(row)
    findings=[];remediations=[];verifications=[]
    for resource_id,observations in sorted(groups.items()):
        policy=resource_policy(resource_id,observations)
        if not policy:continue
        action,system=policy
        # Use the most recent readback at or before the audit; snapshots and
        # action reports are not interchangeable with verified readbacks.
        observations.sort(key=lambda r:(r['observed_at'],r['captured_at']))
        state_obs=[(observation_state(r,action),r) for r in observations]
        state_obs=[(s,r) for s,r in state_obs if s]
        if not state_obs:continue
        state,evidence=state_obs[-1]
        expected={'DELETE':'ABSENT','REDACT':'REDACTED','ANONYMIZE':'ANONYMIZED',
                  'RETAIN':'PRESENT','DISABLE_FLOW':'DISABLED','BLOCK_RESTORE':'BLOCKED'}[action]
        finding,remediation,verification=STEP_TYPES[action]
        def step(phase,operation_state,evidence_id):
            op,st=operation_state
            return {'step_no':0,'phase':phase,'system_id':system,'resource_id':resource_id,
                    'operation':op,'state':st,'evidence_id':evidence_id}
        if state!=expected and action!='RETAIN':
            if finding:findings.append(step('FINDING',finding,evidence['evidence_id']))
            if remediation:remediations.append(step('REMEDIATION',remediation,''))
            verifications.append(step('VERIFICATION',verification,''))
        else:
            verifications.append(step('VERIFICATION',verification,evidence['evidence_id']))
    incomplete=bool(findings)
    if not groups:
        return 'INCOMPLETE',[]
    steps=findings+remediations+verifications
    for n,step in enumerate(steps,1):step['step_no']=n
    return ('INCOMPLETE' if incomplete else 'COMPLETE'),steps
