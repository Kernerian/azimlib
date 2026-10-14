"""Small offline trials only; never download or imply planet-scale validation."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import azimlib as azl
from pbf_fixture import header, primitive, scene
_spec = importlib.util.spec_from_file_location('benchmark_pbf',
    Path(__file__).resolve().parents[1] / 'tools/benchmark_pbf.py')
benchmark_pbf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(benchmark_pbf)


class PlanetProtocolTests(unittest.TestCase):
    def test_complete_byte_count_unknown_blocks_and_full_references(self):
        from pbf_fixture import blob
        raw = header()+blob('future',b'unknown')+primitive(scene())
        with azl.OSMIndex(raw) as index:
            self.assertEqual(index.statistics['input_bytes_read'],len(raw))
            report = index.audit_references()
            self.assertTrue(report['complete'] and report['passed'])
            self.assertEqual((report['nodes'],report['ways'],report['relations']),(9,4,2))
            self.assertEqual(report['missing_members'],0)
            self.assertEqual(len(report['structural_sha256']),64)
            self.assertEqual(report,index.audit_references())
        with self.assertRaisesRegex(ValueError,'closed'):
            index.audit_references()

    def test_raw_relation_missing_members_are_not_silently_accepted(self):
        records = [dict(kind='relation',id=1,tags={'type':'route'},
                        members=(('relation',2,''),('node',99,''),('way',88,''))),
                   dict(kind='relation',id=2,tags={'type':'route'},members=(('relation',1,''),))]
        with azl.OSMIndex(header()+primitive(records)) as index:
            report = index.audit_references()
            self.assertFalse(report['passed'])
            self.assertEqual(report['missing_members'],2)
            self.assertEqual(report['relation_members'],4)

    def test_skipped_way_references_are_still_audited(self):
        records = [dict(kind='way',id=1,refs=(99,100),tags={'highway':'path'})]
        with azl.OSMIndex(header()+primitive(records),missing='skip') as index:
            report = index.audit_references()
            self.assertFalse(report['passed'])
            self.assertEqual(report['missing_way_nodes'],2)

    def test_hash_is_order_independent_and_sensitive_to_member_identity(self):
        records = scene()
        digests=[]
        for values in (records,list(reversed(records))):
            with azl.OSMIndex(header()+primitive(values)) as index:
                digests.append(index.audit_references()['structural_sha256'])
        self.assertEqual(*digests)
        records += [dict(kind='relation',id=50,tags={'type':'route'},members=(('node',1,'stop'),))]
        with azl.OSMIndex(header()+primitive(records)) as index:
            self.assertNotEqual(digests[0],index.audit_references()['structural_sha256'])

    def test_regional_report_full_input_and_audit_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'fixture.pbf';output=Path(directory)/'result.json'
            source.write_bytes(header()+primitive(scene()))
            args=[str(source),'--sha256',hashlib.sha256(source.read_bytes()).hexdigest(),
                  '--output',str(output),'--full-reference-audit','--reserve-free-bytes','0']
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(benchmark_pbf.main(args),0)
            report=json.loads(output.read_text())
            self.assertTrue(report['complete_input_verified'])
            self.assertTrue(report['references']['passed'])
            self.assertFalse(report['planet_scale_confirmed'])
            with patch.object(azl.OSMIndex,'audit_references',return_value={'passed':False}):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(benchmark_pbf.main(args),1)
            report=json.loads(output.read_text())
            self.assertFalse(report['passed'])
            self.assertNotIn(str(source),json.dumps(report))

    def test_planet_mode_requires_strict_full_unfiltered_dated_manifest(self):
        base=['absent.pbf','--scope','planet','--output','absent.json','--sha256','0'*64]
        for extra in ([],['--dataset-version','2026-01-01','--source-url','https://planet.openstreetmap.org/pbf/planet-latest.osm.pbf',
                         '--full-reference-audit'],
                      ['--dataset-version','not-a-date','--source-url','https://planet.openstreetmap.org/pbf/planet-260101.osm.pbf',
                       '--full-reference-audit']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                benchmark_pbf.main(base+extra)
        for extra in (['--missing','skip'],['--bbox','0','0','1','1']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                benchmark_pbf.main(base+['--dataset-version','2026-01-01','--source-url',
                    'https://planet.openstreetmap.org/pbf/planet-260101.osm.pbf','--full-reference-audit']+extra)

    def test_memory_enforcement_fails_closed_without_supported_controller(self):
        with patch.object(benchmark_pbf.sys,'platform','win32'),self.assertRaises(ValueError):
            benchmark_pbf.memory_cgroup(8*1024**3)
        with patch.object(benchmark_pbf.sys,'platform','linux'):
            with patch.object(Path,'read_text',return_value='0::/\n'),self.assertRaises(ValueError):
                benchmark_pbf.memory_cgroup(1024)
            values={'cgroup':'0::/trial\n','memory.max':'1024','memory.swap.max':'0',
                    'memory.peak':'500','memory.events':'oom 0\noom_kill 0\n'}
            with patch.object(Path,'read_text',autospec=True,side_effect=lambda p:values[p.name]):
                snapshot=benchmark_pbf.memory_cgroup(1024)
                self.assertEqual(snapshot()['peak_bytes'],500)
                values['memory.max']='max'
                with self.assertRaises(ValueError):snapshot()
                values['memory.max']='1024';values['memory.swap.max']='1'
                with self.assertRaises(ValueError):snapshot()
                values['memory.swap.max']='0';values['memory.events']='oom 1\noom_kill 1\n'
                with self.assertRaises(ValueError):snapshot()


if __name__ == '__main__':
    unittest.main()
