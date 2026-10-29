import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
import sys; sys.path.insert(0,"tests")
import numpy as np
from adversary_world import *
def adv_factory(N,c,k0,mode,par):
    def adv(seed):
        R=market(seed); L=Ledger(); runs=[]
        for i in range(N):
            w=random_weights(seed,i); r=returns_of(w,R); tt=running_tstat(r)
            hit=np.flatnonzero((np.arange(1,T+1)>=k0)&(tt>=c))
            if hit.size:
                k=hit[0]+1
                if mode=="resume":     # flat from k, trade again for the last `par` periods
                    r=r.copy(); r[k:T-par]=0.0
                elif mode=="tiny":     # weights scaled by par instead of zero
                    r=r.copy(); r[k:]*=par
            runs.append((L.trial(r), r))
        return L.passes(best(L,runs))
    return adv
for mode,pars in (("resume",(1,2,5)),("tiny",(1e-6,1e-3,1e-2,0.05))):
    for par in pars:
        for N in (1,2):
            res=[]
            for c,k0 in ((2.0,2),(2.5,3),(2.0,20),(3.0,2)):
                r=pass_rate(adv_factory(N,c,k0,mode,par),range(2000)); res.append((r.rate,c,k0))
            print(mode,par,"N",N,"max",max(res),flush=True)
