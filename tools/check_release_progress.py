"""Audit the numbered release checklist; Markdown remains the single source."""
import re
from pathlib import Path


def main():
    target=Path(__file__).resolve().parents[1]/'docs/release-progress.md'
    text=target.read_text(encoding='utf-8')
    entries=re.findall(r'^- \[([ x])\] \*\*(\d\.\d{2})\*\* (.+)$',text,re.M)
    expected={f'{step}.{number:02}' for step,count in enumerate((12,10,10,10,12),1) for number in range(1,count+1)}
    actual=[item[1] for item in entries]
    if len(actual)!=len(set(actual)) or set(actual)!=expected:
        raise SystemExit(f'Missing/duplicated/extra IDs: {sorted(expected.symmetric_difference(actual))}')
    completed=sum(status=='x' for status,_,_ in entries);pending=len(entries)-completed
    stated=re.search(r'\*\*(\d+) concluídos / (\d+) pendentes\*\*',text)
    if stated is None or tuple(map(int,stated.groups()))!=(completed,pending):
        raise SystemExit(f'Update the declared total: {completed} completed / {pending} pending')
    for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if '://' not in link and not (target.parent/link.split('#')[0]).exists():
            raise SystemExit(f'Broken local link: {link}')
    print(f'Checklist: {len(entries)} stable IDs; {completed} completed / {pending} pending; local links valid.')
    for step in range(1,6):
        items=[item for item in entries if item[1].startswith(f'{step}.')]
        done=sum(item[0]=='x' for item in items)
        print(f'Step {step}: {done}/{len(items)}; pending: '+', '.join(item[1] for item in items if item[0]!='x'))


if __name__=='__main__':main()
