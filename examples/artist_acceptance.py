"""Run from the project: python examples/artist_acceptance.py.

Real bundled state geometry; all thematic/field/route values are synthetic.
The demo uses the same public calls as the integrated acceptance case.
"""
import importlib.util
from pathlib import Path
import azimlib as azl

project=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('artist_case',project/'tools/artist_acceptance_case.py')
case_tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(case_tool)
target=project/'gallery';target.mkdir(exist_ok=True)
case=case_tool.build()
for state in ('before','after'):
    if state=='after':case_tool.edit(case)
    for extension in ('png','svg','html'):
        path=target/f'artist-acceptance-{state}.{extension}'
        if extension=='html':path.write_text(case['fig'].to_html(),encoding='utf-8')
        else:case['fig'].savefig(path)
azl.close(case['fig'])
print(target/'artist-acceptance-after.png')
