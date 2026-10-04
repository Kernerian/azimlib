"""Record actual environment versions and license-file hashes, without home paths.

This inventory does not mean the listed distributions are bundled by Azimlib or
that their top-level license alone covers every binary/transitive component.
"""
import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import platform


def inventory():
    packages=[]
    for dist in sorted(metadata.distributions(),key=lambda d:d.metadata['Name'].lower()):
        m=dist.metadata
        texts=[]
        for file in dist.files or ():
            name=str(file).replace('\\','/')
            if any(token in Path(name).name.upper() for token in ('LICENSE','LICENCE','COPYING','NOTICE')):
                path=dist.locate_file(file)
                if path.is_file():
                    texts.append(dict(file=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        packages.append(dict(name=m['Name'],version=dist.version,
            license_expression=m.get('License-Expression'),license_metadata=m.get('License'),
            project_urls=m.get_all('Project-URL',[]),home_page=m.get('Home-page'),
            requirements=m.get_all('Requires-Dist',[]),license_files=texts))
    return dict(python=platform.python_version(),packages=packages,
        scope='Observed external development environment, not wheel contents or a lockfile. Top-level metadata and license-file hashes are evidence pointers, not a full component/legal review of each binary.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();result=inventory()
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(len(result['packages']),'external distributions inventoried; none vendored by this command.')
