"""Original historical-atlas structure; all thematic geography is fictional."""
import argparse
from pathlib import Path
from editorial_050 import historical
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--show',action='store_true');args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
 fig,_=historical()
 for fmt in ('png','svg','pdf'):fig.savefig(args.output/('historical-trade-map.'+fmt))
 if args.show:fig.show()
