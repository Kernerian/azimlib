"""Fictional thematic Mars scenario over explicit real data or labeled synthetic base."""
import argparse,importlib.util
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'thematic/_scenes.py';spec=importlib.util.spec_from_file_location('thematic_scenes',p);scenes=importlib.util.module_from_spec(spec);spec.loader.exec_module(scenes)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--real-data',type=Path);p.add_argument('--show',action='store_true');args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
 fig,_=scenes.mars(args.real_data)
 for fmt in ('png','svg','pdf'):fig.savefig(args.output/('mars-exploration-map.'+fmt))
 if args.show:fig.show()
