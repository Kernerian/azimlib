"""Offline integrity, attribution and privacy checks of the optional OSM sample."""
import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def audit():
    sys.path.insert(0, str(ROOT / 'src'))
    from azimlib import DatasetCatalog
    folder = ROOT / 'optional-data/urban-sao-paulo-1.0'
    catalog = DatasetCatalog(folder / 'catalog.json')
    report = catalog.verify()
    entry, = catalog.available()
    assert entry['license'] == 'ODbL-1.0'
    assert entry['copyright'] == 'OpenStreetMap contributors'
    assert 'Open Database License' in (folder / 'LICENSE.txt').read_text('utf-8')
    provenance = json.loads((folder / 'provenance.json').read_text('utf-8'))
    xml = ET.parse(folder / 'data.osm').getroot()
    assert not xml.findall('relation')
    allowed = set(provenance['tag_allowlist'])
    for e in xml:
        assert e.tag in ('node', 'way')
        assert set(e.attrib) == ({'id', 'lon', 'lat'} if e.tag == 'node' else {'id'})
        for t in e.findall('tag'):
            assert t.get('k') in allowed
    features = catalog.load('urban-sao-paulo', version='1.0')
    assert len(features.features) == provenance['counts']['ways'] + provenance['counts']['selected_named_pois']
    assert 'prune optional-data' in (ROOT / 'MANIFEST.in').read_text('utf-8')
    return dict(report, dataset=entry['id'], version=entry['version'], license=entry['license'],
                features=len(features.features), editor_metadata=False, network_requests=0,
                shipped_in_python_archives=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = audit()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2)+'\n', 'utf-8')
    print(json.dumps(report, indent=2))
