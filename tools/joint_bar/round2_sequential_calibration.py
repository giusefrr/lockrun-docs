import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_sys.path[:0] = [_HERE, _os.path.join(_HERE, "..", "..", "tests")]
import numpy as np
from statistics import NormalDist
Nd = NormalDist()
T, M, ALPHA = 250, 100, 0.05

def sup_z(x, m=M):
    """sup over k in [m, T] of the PSR statistic vs 0: sr_k sqrt(k-1)/sqrt(1 - skew sr + (kurt-1)/4 sr^2), moment estimators as lockrun.stats."""
    n, T_ = x.shape
    k = np.arange(1, T_ + 1)
    s1, s2, s3, s4 = (np.cumsum(x ** p, 1) for p in (1, 2, 3, 4))
    mu = s1 / k
    m2 = s2 / k - mu ** 2
    m3 = s3 / k - 3 * mu * s2 / k + 2 * mu ** 3
    m4 = s4 / k - 4 * mu * s3 / k + 6 * mu ** 2 * s2 / k - 3 * mu ** 4
    sd = np.sqrt(m2 * k / (k - 1))
    sr = mu / sd
    skew, kurt = m3 / m2 ** 1.5, m4 / m2 ** 2
    z = sr * np.sqrt(k - 1) / np.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr ** 2)
    return z[:, m - 1:].max(1), z[:, -1]

rng = np.random.default_rng(7)
out = {}
for name, draw in (("normal", lambda n: rng.normal(size=(n, T))),
                   ("student-t df=5", lambda n: rng.standard_t(5, size=(n, T)))):
    sups, fixed = [], []
    for _ in range(10):
        s, f = sup_z(draw(50_000)); sups.append(s); fixed.append(f)
    sups, fixed = np.concatenate(sups), np.concatenate(fixed)
    c = np.quantile(sups, 1 - ALPHA)
    se = np.sqrt(ALPHA * (1 - ALPHA) / len(sups))
    lo, hi = np.quantile(sups, [1 - ALPHA - 2 * se, 1 - ALPHA + 2 * se])
    out[name] = c
    print(f"{name}: c_seq = {c:.4f} [{lo:.4f}, {hi:.4f}] (500k paths); P(z_T >= 1.645) = {np.mean(fixed >= 1.645):.4f}; "
          f"P(sup z_k >= 1.645) = {np.mean(sups >= 1.645):.4f}")

# Siegmund-type continuous approximation: P(sup over log-time span L of an OU) ~ 1-Phi(c) + c phi(c) L/2
L = np.log(T / M)
f = lambda c: (1 - Nd.cdf(c)) + c * Nd.pdf(c) * L / 2 - ALPHA
a, b = 1.0, 4.0
for _ in range(60):
    mid = (a + b) / 2; a, b = (mid, b) if f(mid) > 0 else (a, mid)
print(f"continuous (Siegmund) approximation, span ln(T/min_t) = {L:.3f}: c = {a:.4f}")
# Robbins normal mixture (sigma known), valid for every n >= 1: S_n >= sqrt((n+rho) log((n+rho)/(rho alpha^2)))
best = min((max(np.sqrt((1 + rho / n) * np.log((n + rho) / (rho * ALPHA ** 2))) for n in range(M, T + 1)), rho)
           for rho in np.geomspace(1, 1e4, 400))
print(f"Robbins mixture boundary, best rho = {best[1]:.0f}: constant equivalent over [100, 250] = {best[0]:.4f}")
print(f"Bonferroni over the {T - M + 1} stopping times: {Nd.inv_cdf(1 - ALPHA / (T - M + 1)):.4f}")
print(f"fixed T (today's PSR bar): {Nd.inv_cdf(1 - ALPHA):.4f}")
