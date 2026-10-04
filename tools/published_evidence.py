"""Match a recorded execution hash to an explicitly transformed public snapshot.

This does not change the recorded hash or make it evidence of a new execution.
Only pairs recorded in the publication source map are accepted.
"""
import json
from pathlib import Path


def published_hashes(recorded):
    path = Path(__file__).resolve().parents[1] / 'docs/publication-source-map.json'
    reached = {recorded}
    if not path.exists():
        return reached
    rows = json.loads(path.read_text('utf-8'))['transformations']
    changed = True
    while changed:
        changed = False
        for row in rows:
            if row['original_sha256'] in reached and row['published_sha256'] not in reached:
                reached.add(row['published_sha256'])
                changed = True
    return reached


def equivalent_digest(recorded, current):
    return current in published_hashes(recorded)
