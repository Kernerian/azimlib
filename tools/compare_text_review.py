"""Verify review packet identities/hashes; never grant human acceptance."""
import argparse
import hashlib
import json
from pathlib import Path


def compare(packets,*,allow_partial=False):
    records=[];seen=set();source=None;fonts=None
    for directory in map(Path,packets):
        manifest=json.loads((directory/'manifest.json').read_text('utf8'))
        system=manifest['system']
        if system not in ('Windows','Linux','Darwin') or system in seen:
            raise ValueError('Require distinct supported platforms')
        seen.add(system)
        if manifest['stage']!='7.08' or manifest['status']!='awaiting-three-platform-human-approval':
            raise ValueError('Unexpected review stage/status')
        if source is None:source=manifest['source_sha256'];fonts=manifest['fonts']
        elif source!=manifest['source_sha256'] or fonts!=manifest['fonts']:
            raise ValueError('Review packets must have identical runtime source and pinned fonts')
        for name,digest in manifest['files'].items():
            if Path(name).name!=name or name in ('.','..'):
                raise ValueError('Unsafe review packet filename')
            path=directory/name
            if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                raise ValueError('Review output hash mismatch')
        native={entry['backend']:entry for entry in manifest['native']}
        if set(native)!= {'tk','qt'}:raise ValueError('Require both native captures')
        if any(entry['file'] not in manifest['files'] for entry in native.values()):
            raise ValueError('Native captures must be hashed review outputs')
        records.append(dict(system=system,files=len(manifest['files']),engines=manifest['engines']))
    complete=seen=={'Windows','Linux','Darwin'}
    if not complete and not allow_partial:
        raise ValueError('All three platform packets are required; explicit --allow-partial only verifies available packets')
    return dict(schema_version=1,stage='7.08',packet_integrity=True,
                all_platforms_present=complete,human_approval=False,
                status='awaiting-human-review' if complete else 'awaiting-remaining-platform-packets',
                platforms=records)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet',required=True,type=Path,action='append')
    parser.add_argument('--allow-partial',action='store_true')
    parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args();result=compare(args.packet,allow_partial=args.allow_partial)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result))
