import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
import sys
import numpy as np
from adversary_world import *
def flat(N,c,k0):
    def adv(seed):
        R=market(seed); L=Ledger(); runs=[]
        for i in range(N):
            r=returns_of(random_weights(seed,i),R); tt=running_tstat(r)
            hit=np.flatnonzero((np.arange(1,T+1)>=k0)&(tt>=c))
            if hit.size: r=r.copy(); r[hit[0]+1:]=0.0
            runs.append((L.trial(r), r))
        return L.passes(best(L,runs))
    return adv
for N in (1,2,3,5):
    res=[]
    for c in (1.5,2.0,2.5,3.0,4.0,6.0):
        for k0 in (2,3,5,10,20):
            r=pass_rate(flat(N,c,k0), range(3000 if N<=2 else 1500)); res.append((r.rate,c,k0,str(r)))
    res.sort(reverse=True); print(N, res[:3], flush=True)
# sanity: the honest strategy (never flat) at N=1 on the same seeds
print("honest", pass_rate(flat(1,1e9,2), range(10000)))
