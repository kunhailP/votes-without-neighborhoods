"""Joint price-tail and geographic scope sensitivity (Online Appendix C29).
Cross the exclusion of Gangnam, Seocho and Songpa with trimming the highest
remaining neighborhood log prices, retaining every ballot accounting constraint.
"""
from vwn.paths import RES
import numpy as np
import pandas as pd
from vwn.run import Prep
from vwn.data import weights
from vwn.bounds import total, bounds_with_w
from vwn.lp import KMS
OUT=RES
P=Prep('20260603');gu=np.asarray(P.labs['guFE']);base=P.has & ~np.isin(gu,['강남구','서초구','송파구'])
rows=[]
for slack in [.02,.05]:
 lps=P.lps(calib=True,dF=('slack',slack))
 for trim in [0,.05,.10]:
  keep=base.copy()
  if trim:keep &= P.x<=np.quantile(P.x[base],1-trim)
  w=np.zeros(len(P.x));w[keep]=weights(P.x[keep],gu[keep],True)
  lo,hi=total(P.units,lps,P.wsplit(w),1.,.1)
  assert np.isfinite(lo) and np.isfinite(hi)
  rows.append(dict(slack=slack,delta=.1,trim_within_remaining=trim,n=int(keep.sum()),lower=lo,upper=hi))
  print(rows[-1],flush=True)
 pd.DataFrame(rows).to_csv(OUT/'scope_price_tail_20260603.csv',index=False)
# Leave-one-district-out under the main setting: constraints separate by district;
# omitting a district rescales every retained district's FE slope weights equally.
lps=P.lps(calib=True,dF=('slack',.02));w=np.zeros(len(P.x));w[base]=weights(P.x[base],gu[base],True);ws=P.wsplit(w)
contrib={u:bounds_with_w(lps[u],ws[u],KMS,1.,.1) for u in P.units}
den={u:float(((P.x[base & (gu==u)]-P.x[base & (gu==u)].mean())**2).sum()) for u in np.unique(gu[base])}
D=sum(den.values());lo=sum(v[0] for v in contrib.values());hi=sum(v[1] for v in contrib.values());loo=[]
for u in den:
 scale=D/(D-den[u]);loo.append(dict(omitted=u,lower=(lo-contrib[u][0])*scale,upper=(hi-contrib[u][1])*scale))
pd.DataFrame(loo).to_csv(OUT/'scope_leave_one_out_20260603.csv',index=False)
print('Leave-one-district-out minimum lower bound:',min(x['lower'] for x in loo),flush=True)

# Independently re-solve the omitted district with the smallest lower bound.
worst=min(loo,key=lambda row:row["lower"])
keep=base & (gu!=worst["omitted"]);w=np.zeros(len(P.x));w[keep]=weights(P.x[keep],gu[keep],True)
check=total(P.units,lps,P.wsplit(w),1.,.1)
assert np.allclose(check,[worst["lower"],worst["upper"]],rtol=1e-10,atol=1e-10)
