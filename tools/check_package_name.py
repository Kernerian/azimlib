"""Read exact normalized-name metadata from PyPI; never installs or reserves it."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import urllib.error
import urllib.request


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();name=re.sub(r'[-_.]+','-','azimlib').lower();url=f'https://pypi.org/pypi/{name}/json'
    result=dict(name='azimlib',normalized_name=name,checked_utc=datetime.now(timezone.utc).isoformat(),url=url,
        scope='Read-only exact PyPI normalized-name lookup. HTTP 404 is an observation, not reservation, trademark clearance or a guarantee of future upload permission.')
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Azimlib-development-name-audit/0.1'}),timeout=30) as response:
            data=json.load(response);result.update(http_status=response.status,state='existing-distribution',project_name=data['info']['name'],version=data['info']['version'])
    except urllib.error.HTTPError as error:
        result.update(http_status=error.code,state='not-found-at-check-time' if error.code==404 else 'lookup-unavailable')
    except (urllib.error.URLError,TimeoutError,OSError,ValueError) as error:
        result.update(http_status=None,state='lookup-unavailable',error=str(error))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
