"""Recompute the fixed-cap zone comparison and headline reporting guarantees."""
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
for p in (ROOT/'analysis').iterdir():
    if p.is_dir():sys.path.insert(0,str(p))
from vwn.run import Prep
from vwn.bounds import total
from disclosure_guarantee import wmax

import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=ROOT/'logs/institutional_verification.json')
args=parser.parse_args()
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps({'complete':False,'status':'running'})+'\n')

records=[]
for sg in ['20220309','20240410','20250603','20260603']:
    p=Prep(sg);lp=p.lps(calib=True,dF=('slack',.02));weights=p.W['guFE']
    lo,hi=total(p.units,lp,weights,1.,.1)
    ref=pd.read_csv(ROOT/f'results/disclosure_guarantee_{sg}.csv')
    ref=ref[ref.config=='calib, delta=0.1, s=0.02'].iloc[0]
    rec={'election':sg,'current_width':hi-lo,'reports':{}}
    assert abs(hi-lo-ref.W0)<1e-8
    for prop in ['P2b','P2']:
        width=sum(wmax(lp[u],weights[u],1.,.1,prop) for u in p.units)
        diff=abs(width-ref['Wmax_'+prop]);assert diff<1e-8,(sg,prop,diff)
        rec['reports'][prop]={'maximum_remaining_width':width,'fraction_removed':1-width/(hi-lo),'difference_from_shipped':diff}
    suppressed=sum(wmax(lp[u],weights[u],1.,.1,'P2b',report_tolerance=19) for u in p.units)
    sr=pd.read_csv(ROOT/f'results/suppression_{sg}.csv').query('threshold == 20').iloc[0]
    diff=abs(suppressed-sr.remaining_width_upper);assert diff<1e-8
    rec['primary_suppression_below_20']={'remaining_width_upper':suppressed,'guaranteed_reduction_lower':1-suppressed/(hi-lo),'difference_from_shipped':diff}
    records.append(rec)
    print(sg,'residence-report guarantees verified',flush=True)

zones=[]
ref=pd.read_csv(ROOT/'results/zones_2026.csv')
for imposed,label in [(False,'no zone restriction'),(True,'statutory zones (main)')]:
    p=Prep('20260603',zones=imposed);lp=p.lps(calib=False)
    bounds=np.array(total(p.units,lp,p.W['guFE'],.1,.1))
    row=ref[(ref.variant==label)&(ref.cell=='eta=0.1, delta=0.1')&(ref.spec=='guFE')].iloc[0]
    difference=float(np.max(np.abs(bounds-row[['lo','hi']].to_numpy(float))))
    assert difference<1e-8,(label,difference)
    zones.append({'zones':label,'bounds':bounds.tolist(),'difference_from_shipped':difference})
    print(label,'fixed-cap bounds verified',flush=True)
out={'complete':True,'scope':'Main-assumption exact P2b/P2 guarantees and primary suppression below 20 for four elections, plus the 2026 uniform-cap zone comparison; supplied inputs and existing solver framework; no source authentication or substantive-assumption validation.','residence_reporting':records,'fixed_cap_zone_comparison':zones}
args.output.write_text(json.dumps(out,indent=2)+'\n')
print('Verified residence-report guarantees, suppression and fixed-cap zones.',flush=True)
