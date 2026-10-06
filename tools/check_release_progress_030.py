"""Validate the stable 0.3.0 checklist IDs, totals and evidence sections."""
import re
from pathlib import Path


def main():
    target = Path(__file__).resolve().parents[1] / 'docs/release-progress-0.3.md'
    text = target.read_text('utf-8')
    entries = re.findall(r'^- \[([ x])\] \*\*(\d+\.\d{2})\*\* (.+)$', text, re.M)
    expected = {f'{step}.{number:02}' for step in range(1, 11) for number in range(1, 9)}
    actual = [item[1] for item in entries]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise SystemExit('Missing, duplicate or unexpected checklist IDs')
    done = sum(state == 'x' for state, _, _ in entries)
    declared = re.search(r'\*\*(\d+) concluídos / (\d+) pendentes\*\*', text)
    if declared is None or tuple(map(int, declared.groups())) != (done, len(entries)-done):
        raise SystemExit('Declared checklist count does not match entries')
    for step in range(1, 11):
        finished = sum(state == 'x' for state, item, _ in entries if item.startswith(f'{step}.'))
        if finished and f'### Lote {step} ' not in text:
            raise SystemExit(f'Step {step} has completed items without a batch evidence section')
    print(f'0.3.0 checklist: {done}/{len(entries)} completed; {len(entries)-done} pending.')


if __name__ == '__main__':
    main()
