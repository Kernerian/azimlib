"""Stable 112-ID inventory with explicit deferments; never infer final acceptance.

Only four explicitly annotated deferments are excluded from the active scope.
Publication still requires every active ID, including human/final acceptance.
"""
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEFERRED_040=frozenset(('2.08','9.08','13.06','13.07'))
REVALIDATION_040=frozenset(('14.01','14.06'))

def check(text,*,require_complete=False):
    entries=re.findall(r'^- \[([ x])\] \*\*(\d+\.\d{2})\*\* (.+)$',text,re.M)
    expected=[f'{stage}.{item:02}' for stage in range(1,15) for item in range(1,9)]
    if [item for state,item,title in entries]!=expected:raise ValueError('Expected ordered unique 112 stable checklist IDs')
    done=sum(state=='x' for state,item,title in entries)
    scoped=re.search(r'\*\*(\d+) concluídos / (\d+) adiados / (\d+) pendentes de entrega ou revalidação\*\*',text)
    annotations=re.findall(r'^  Estado: \*\*(ADIADO|REVALIDAÇÃO FINAL)\*\* \((\d+\.\d{2})\)',text,re.M)
    deferred=[];revalidation=[]
    if scoped:
        if len(annotations)!=len({item for status,item in annotations}):raise ValueError('Duplicate inventory status')
        states={item:state for state,item,title in entries}
        deferred=[item for status,item in annotations if status=='ADIADO']
        revalidation=[item for status,item in annotations if status=='REVALIDAÇÃO FINAL']
        if set(deferred)!=DEFERRED_040:raise ValueError('Only the four explicit 0.4 deferments are authorized')
        if not set(revalidation)<=REVALIDATION_040:raise ValueError('Unknown historical revalidation item')
        if any(states.get(item)!=' ' for status,item in annotations):raise ValueError('Deferred/revalidation items cannot be checked complete')
        if tuple(map(int,scoped.groups()))!=(done,len(deferred),112-done-len(deferred)):raise ValueError('Scoped checklist totals disagree with entries')
    else:
        if annotations:raise ValueError('Status annotations require explicit scoped totals')
        declared=re.search(r'\*\*(\d+) concluídos / (\d+) pendentes?\*\*',text)
        if declared is None or tuple(map(int,declared.groups()))!=(done,112-done):raise ValueError('Checklist totals disagree with entries')
    for stage in range(1,15):
        if any(state=='x' and item.startswith(str(stage)+'.') for state,item,title in entries) and f'### Lote {stage} ' not in text:raise ValueError('Completed items need batch evidence')
    pending=[item for state,item,title in entries if state!='x']
    active_pending=[item for item in pending if item not in deferred]
    if require_complete and active_pending:raise ValueError('Release blocked by active pending IDs: '+', '.join(active_pending))
    return dict(passed=True,total=112,completed=done,deferred=deferred,
                pending=active_pending,revalidation_required=revalidation,
                original_uncompleted=pending,active_total=112-len(deferred),
                active_scope_complete=not active_pending,release_ready=not active_pending,
                scope_note='Inventory consistency is not exact-candidate acceptance; all 108 active IDs require completion')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--require-complete',action='store_true');p.add_argument('--output',type=Path);args=p.parse_args()
    result=check((ROOT/'docs/release-progress-0.4.md').read_text('utf8'),require_complete=args.require_complete)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2))
