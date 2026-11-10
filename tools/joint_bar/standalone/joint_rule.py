"""The rule, self-contained: numpy only, no lockrun.

Ported from lockrun/stats.py, lockrun/dummies.py, lockrun/exposure.py, lockrun/calibration.py and
lockrun/trials.py (evaluate_promotion). lockrun's suite (tests/test_joint_bar_standalone.py) runs this
module and the package on the same seeded inputs and requires identical decisions and statistics.

  Holdout.before(i)   the DSR as before the rule of 27 October 2026: the PSR on all T against sr0, with N
                      every opening plus the reserved fresh verification and V floored at the null
                      variance; the lowest of five families' values against the threshold.
  Holdout.joint(i)    the joint bar: z, the plain t-statistic on returns over their ex-ante risk (rule version 2),
                      F(z / scale)^n against the threshold in each of the five families, the scale
                      leaving the candidate out, n every opening but fresh verifications. stat="psr": the
                      rule before, rule version 1, whose z is the PSR statistic against 0 (what a holdout
                      initialised before 30 October 2026 keeps; lockrun's suite compares this copy with the
                      package under both).
  rule version 3      spending by trial: alpha_of, spending_table, trial_bar, tilted_paths, and passes_v3: a trial
                      passes iff its plain t over ex-ante risk is above the b_k of its place among the openings. No n, no
                      scale, no families. lockrun's suite holds these identical to lockrun/calibration.py.
"""
from __future__ import annotations

import functools
import math
from dataclasses import dataclass, field
from math import comb, e, sqrt
from statistics import NormalDist

import numpy as np

EULER_GAMMA = 0.5772156649
_NORMAL = NormalDist()
EXPOSURE = {"window": 60, "warmup": 20, "floor": 0.1}
DEFAULT_STAT = "t"
NULL_RATIO = 1e-10
NORMAL_DF = 200
DF_FLOOR = 4
MIN_RESIDUALS = 30
N_GRID = (1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000)
N_CAP = 1000
ALPHA_PLANNED = 0.045
ALPHA_TAIL = 0.005
PLAIN_FLOOR = 1e-3
DEEPEST_ALPHA = 1e-16
LEVELS_PER_DECADE = 10
MARGIN_SE = 3.0
REL_SE_MAX = 0.15
MIN_HITS = 100
IS_COMPONENTS = 8
DEFENSIVE = 0.1
IS_PILOT_PATHS = 20_000
IS_PILOT_ROUNDS = 3
DUMMY_C = 0.005           # z below which a weakly correlated pair is "too close"
DUMMY_RHO_WEAK = 0.5      # |rho| below which a pair counts as weakly correlated
DUMMY_ALPHA = 0.01        # target per-search false-positive rate for the partner-count test
DUP_RHO = 1 - 1e-9        # correlation above which a pair is the same series up to scale
DUP_SR = 1e-9             # Sharpe difference below which such a pair is a duplicate


# ---------------------------------------------------------------- per-period Sharpe statistics

def validate_returns(returns) -> np.ndarray:
    r = np.asarray(returns, dtype=float).ravel()
    if r.size == 0:
        raise ValueError("returns series is empty")
    if not np.all(np.isfinite(r)):
        raise ValueError("returns contain NaN or inf")
    if r.size < 2 or np.all(r == r[0]):
        raise ValueError("returns have zero standard deviation")
    if r.std(ddof=1) <= 1e-9 * max(abs(r.mean()), 1e-12):
        raise ValueError("returns have degenerate relative dispersion (std <= 1e-9 x |mean|)")
    return r


@dataclass(frozen=True)
class Moments:
    T: int
    sr: float    # per-period Sharpe, sample std (ddof=1)
    skew: float  # moment estimator
    kurt: float  # moment estimator, non-excess (normal = 3)


def moments(returns) -> Moments:
    r = validate_returns(returns)
    mu = r.mean()
    c = r - mu
    m2 = np.mean(c**2)
    return Moments(T=int(r.size), sr=float(mu / r.std(ddof=1)), skew=float(np.mean(c**3) / m2**1.5),
                   kurt=float(np.mean(c**4) / m2**2))


def sharpe_variance(trial_srs) -> float:
    srs = np.asarray(trial_srs, dtype=float)
    if srs.size < 2:
        raise ValueError("V needs at least 2 trials")
    return float(np.var(srs, ddof=1))


def null_sharpe_variance(T: int) -> float:
    """Exact variance of the per-period Sharpe estimator under the null: (T-1) / (T (T-3))."""
    if T <= 3:
        raise ValueError(f"null Sharpe variance needs T > 3, got T={T}")
    return (T - 1) / (T * (T - 3))


def expected_max_sharpe(V: float, N: int) -> float:
    """SR0: expected maximum per-period Sharpe of N independent null trials."""
    if N < 2:
        raise ValueError("SR0 needs N >= 2")
    g = EULER_GAMMA
    return sqrt(V) * ((1 - g) * _NORMAL.inv_cdf(1 - 1 / N) + g * _NORMAL.inv_cdf(1 - 1 / (N * e)))


def probabilistic_sharpe(sr: float, sr_star: float, T: int, skew: float, kurt: float) -> float:
    den2 = 1 - skew * sr + ((kurt - 1) / 4) * sr**2
    if den2 <= 0:
        raise ValueError("non-positive variance term in the PSR denominator")
    return _NORMAL.cdf((sr - sr_star) * sqrt(T - 1) / sqrt(den2))


def deflated_value(m: Moments, trial_srs, N: int) -> float:
    """The DSR with V floored at the null variance at the candidate's T; the PSR against 0 for N < 2."""
    if N < 2:
        return probabilistic_sharpe(m.sr, 0.0, m.T, m.skew, m.kurt)
    v_null = null_sharpe_variance(m.T)
    V = v_null if len(trial_srs) < 2 else max(sharpe_variance(trial_srs), v_null)
    return probabilistic_sharpe(m.sr, expected_max_sharpe(V, N), m.T, m.skew, m.kurt)


# ---------------------------------------------------------------- the dummy detector

@dataclass
class Flags:
    suspicious: set = field(default_factory=set)
    duplicates: set = field(default_factory=set)

    @property
    def flagged(self) -> set:
        return self.suspicious | self.duplicates


def partner_threshold(n: int, c: float = DUMMY_C, alpha: float = DUMMY_ALPHA) -> int:
    """Smallest k with P(Binomial(n-1, p0) >= k) <= alpha / n, at least 2."""
    m, p0 = n - 1, 2 * _NORMAL.cdf(c) - 1
    tail, k = 1.0, 0
    while k <= m:
        if tail <= alpha / n and k >= 2:
            return k
        tail -= comb(m, k) * p0**k * (1 - p0) ** (m - k)
        k += 1
    return m + 1


def flag(series: list) -> Flags:
    """Flag dummy trials among return series of one T (Memmel 2003): weakly correlated pairs whose Sharpes
    are closer than sampling noise allows, and exact duplicates up to scale."""
    out = Flags()
    by_t: dict[int, list[int]] = {}
    for i, r in enumerate(series):
        by_t.setdefault(len(r), []).append(i)
    for T, idx in by_t.items():
        n = len(idx)
        if n < 2 or T < 4:
            continue
        R = np.array([np.asarray(series[i], dtype=float) for i in idx])
        mu, sd = R.mean(1, keepdims=True), R.std(1, ddof=1, keepdims=True)
        s = (mu / sd).ravel()
        Z = (R - mu) / sd
        rho = np.clip(Z @ Z.T / (T - 1), -1.0, 1.0)
        d = np.abs(s[:, None] - s[None, :])
        var = (2 - 2 * rho + (s[:, None] ** 2 + s[None, :] ** 2 - 2 * np.outer(s, s) * rho**2) / 2) / T
        z = d / np.sqrt(np.maximum(var, 1e-300))
        off = ~np.eye(n, dtype=bool)
        if n >= 3:
            suspicious = off & (np.abs(rho) < DUMMY_RHO_WEAK) & (z < DUMMY_C)
            out.suspicious |= {idx[a] for a in np.flatnonzero(suspicious.sum(1) >= partner_threshold(n))}
        dup = off & (rho > DUP_RHO) & (d < DUP_SR)
        for a in range(n):
            if dup[a, :a].any():          # duplicates an earlier trial: the earliest stays
                out.duplicates.add(idx[a])
    return out


# ---------------------------------------------------------------- ex-ante risk normalization

def window_covariances(R: np.ndarray, p: dict = EXPOSURE) -> tuple[np.ndarray, np.ndarray]:
    """(S, ok): the sample covariance of the `window` rows strictly before each step, for the steps with at
    least `warmup` rows (ok). No shrinkage. A complete panel: every asset a return every period."""
    Tn, A = R.shape
    P = np.concatenate([np.zeros((1, A, A)), np.cumsum(R[:, :, None] * R[:, None, :], 0)])
    m = np.concatenate([np.zeros((1, A)), np.cumsum(R, 0)])
    t = np.arange(Tn)
    a = np.maximum(0, t - p["window"])
    n = (t - a).astype(float)
    ok = n >= p["warmup"]
    mu = (m[t] - m[a])[ok] / n[ok, None]
    S = ((P[t] - P[a])[ok] - n[ok, None, None] * mu[:, :, None] * mu[:, None, :]) / (n[ok, None, None] - 1)
    return S, ok


def risks_of(W: np.ndarray, cov) -> np.ndarray:
    """sqrt(w' S w) per step: 0 for no weights or the null space (variance at most NULL_RATIO times the
    weights' variance with no correlation), NaN where there is no estimate."""
    if isinstance(cov, Estimator):
        return cov.risks(W)
    S, ok = cov
    out = np.full(len(W), np.nan)
    w = W[ok]
    var = np.einsum("ti,tij,tj->t", w, S, w)
    uncorrelated = np.einsum("ti,tii->t", w * w, S)
    out[ok] = np.where((uncorrelated == 0) | (var <= NULL_RATIO * uncorrelated), 0.0, np.sqrt(np.maximum(var, 0)))
    out[~(W != 0).any(1)] = 0.0
    return out


def shrink_toward_diagonal(X: np.ndarray) -> np.ndarray:
    """The sample covariance of rows X, shrunk toward its diagonal by the estimator's own intensity (Ledoit &
    Wolf 2004, for this target as in Schaefer & Strimmer 2005): the off-diagonals' estimated sampling variance
    over their squares, within [0, 1]."""
    n, k = X.shape
    C = X - X.mean(0)
    P = C.T @ C
    S = P / (n - 1)
    if k < 2:
        return S
    Y = C * C
    off = ~np.eye(k, dtype=bool)
    num = (n / (n - 1) ** 3) * ((Y.T @ Y) - P * P / n)[off].sum()
    den = (S[off] ** 2).sum()
    d = 1.0 if den == 0 else min(1.0, max(0.0, num / den))
    return (1 - d) * S + d * np.diag(np.diag(S))


EIGEN_FLOOR = 0.01
MIN_WINDOW_PER_ASSET = 3


class Estimator:
    """A candidate covariance estimate (statistical rule, standalone only; the product's is the sample
    covariance): per set of held assets, as the rule's S is.
    lw        S shrunk toward its diagonal, the intensity chosen by the estimator
    minwin    a window, and a warm-up, of at least 3 times the held assets
    eigfloor  a step whose smallest window eigenvalue is under 1% of the median eigenvalue is inactive
    Iterates as (S, ok) over every asset, the state an adversary knows."""

    def __init__(self, R: np.ndarray, p: dict):
        self.R, self.p, self.kind = R, p, p["cov"]
        self._by_mask: dict = {}
        self.A = R.shape[1]
        self.S, self.ok, _ = self._state(np.ones(self.A, bool))

    def __iter__(self):
        return iter((self.S, self.ok))

    def __getitem__(self, i):
        return (self.S, self.ok)[i]

    def _state(self, mask: np.ndarray) -> tuple:
        key = mask.tobytes()
        if key not in self._by_mask:
            self._by_mask[key] = self._compute(mask)
        return self._by_mask[key]

    def _compute(self, mask: np.ndarray) -> tuple:
        R, p = self.R[:, mask], self.p
        k, Tn = R.shape[1], R.shape[0]
        if self.kind == "minwin":
            least = MIN_WINDOW_PER_ASSET * k
            window, warmup = max(p["window"], least), max(p["warmup"], least)
        else:
            window, warmup = p["window"], p["warmup"]
        if self.kind == "lw":
            t = np.arange(Tn)
            ok = t - np.maximum(0, t - window) >= warmup
            S = np.empty((int(ok.sum()), k, k))
            for j, s in enumerate(np.flatnonzero(ok)):
                S[j] = shrink_toward_diagonal(R[max(0, s - window):s])
            return S, ok, None
        S, ok = window_covariances(R, {"window": window, "warmup": warmup})
        inactive = None
        if self.kind == "eigfloor":
            v = np.linalg.eigvalsh(S) if len(S) else np.empty((0, k))
            inactive = v[:, 0] < EIGEN_FLOOR * np.median(v, axis=1)
        return S, ok, inactive

    def risks(self, W: np.ndarray) -> np.ndarray:
        out = np.full(len(W), np.nan)
        held = W != 0
        out[~held.any(1)] = 0.0
        for mask in np.unique(held[held.any(1)], axis=0):
            steps = (held == mask).all(1)
            S, ok, inactive = self._state(mask)
            at = np.flatnonzero(ok[steps])                       # among these steps, those with an estimate
            where = np.flatnonzero(steps)[at]
            index = np.cumsum(ok) - 1
            w = W[where][:, mask]
            s = S[index[where]]
            var = np.einsum("ti,tij,tj->t", w, s, w)
            un = np.einsum("ti,tii->t", w * w, s)
            r = np.where((un == 0) | (var <= NULL_RATIO * un), 0.0, np.sqrt(np.maximum(var, 0)))
            if inactive is not None:
                r = np.where(inactive[index[where]], 0.0, r)
            out[where] = r
        return out


class BoundedCov(tuple):
    """The sample covariance's (S, ok), with a candidate's bound on one normalized return (statistical rule,
    standalone only):
    risk_floor  f: a step's risk under f x the median of the strategy's risks > 0 is raised to it and stays active;
                a step with no estimate or zero risk stays inactive
    winsor      k: each normalized return, of ex-ante sd 1 by construction, clipped to [-k, k]"""

    def __new__(cls, pair: tuple, risk_floor: float | None = None, winsor: float | None = None):
        self = super().__new__(cls, pair)
        self.risk_floor, self.winsor = risk_floor, winsor
        return self


def estimator(R: np.ndarray, p: dict = EXPOSURE):
    """The state risks_of needs: the sample covariance's (S, ok) unless p names another estimate or a bound."""
    if p.get("cov", "sample") != "sample":
        return Estimator(R, p)
    pair = window_covariances(R, p)
    return BoundedCov(pair, p.get("risk_floor"), p.get("winsor")) if p.get("risk_floor") or p.get("winsor") else pair


def winsorized(x: np.ndarray, k: float) -> np.ndarray:
    return np.clip(x, -k, k)


def bounded_returns(r: np.ndarray, risk: np.ndarray, cov, floor_of: float | None = None) -> np.ndarray:
    """r / risk on the steps given, under cov's bound. floor_of: the floor, when not these steps' own."""
    f, k = getattr(cov, "risk_floor", None), getattr(cov, "winsor", None)
    if f:
        live = np.isfinite(risk) & (risk > 0)
        floor = floor_of if floor_of is not None else f * float(np.median(risk[live])) if live.any() else np.nan
        risk = np.maximum(risk, floor)
    x = r / risk
    return winsorized(x, k) if k else x


def bounded_steps(W: np.ndarray, risk: np.ndarray, cov) -> np.ndarray:
    """The active steps under cov's bound: a floor keeps every step with an estimate and risk > 0. A
    winsorization leaves them the rule's."""
    if not getattr(cov, "risk_floor", None):
        return active_steps(risk)
    return np.flatnonzero(np.isfinite(risk) & (risk > 0))


def risks_panel(W: np.ndarray, R: np.ndarray, p: dict = EXPOSURE) -> np.ndarray:
    return risks_of(W, window_covariances(R, p))


def active_steps(risk: np.ndarray, floor: float = EXPOSURE["floor"]) -> np.ndarray:
    """The active steps' indices: an estimate, risk > 0, and risk >= floor x the median of the risks > 0."""
    live = np.isfinite(risk) & (risk > 0)
    if not live.any():
        return np.array([], int)
    return np.flatnonzero(live & (risk >= floor * float(np.median(risk[live]))))


def declared_active(risk: np.ndarray, floor: float = EXPOSURE["floor"]) -> np.ndarray:
    """Rule version 3: the declared portfolio's active steps, fixed once at opening from its ex-ante risk over the
    whole holdout (risk >= floor x the median of the declared risks > 0). A trial within its declaration is graded
    on these steps alone (graded_on), so the trial that stops at tau is graded on a prefix of x_d, the series the
    declared bar takes the sup over; its own risks never move the set."""
    return active_steps(np.asarray(risk, dtype=float), floor)


def graded_on(r: np.ndarray, risk: np.ndarray, active) -> np.ndarray:
    """A trial's normalized returns on the declared active steps where it holds risk: r_t / risk_t for t in active
    (in order) with risk_t > 0 and t within the trial; the steps after its stop (risk 0) drop out."""
    r, risk = np.asarray(r, dtype=float), np.asarray(risk, dtype=float)
    a = np.asarray(active, dtype=np.int64)
    a = a[a < min(len(r), len(risk))]
    keep = a[np.isfinite(risk[a]) & (risk[a] > 0)]
    return r[keep] / risk[keep]


def active_moments(r: np.ndarray, risk: np.ndarray, floor: float = EXPOSURE["floor"]) -> tuple[int, Moments | None]:
    """(T_eff, the moments of r / risk on the active steps, None when they are no valid series)."""
    idx = active_steps(risk, floor)
    try:
        return len(idx), moments(r[idx] / risk[idx])
    except ValueError:
        return len(idx), None


def active_series(r: np.ndarray, risk: np.ndarray, floor: float = EXPOSURE["floor"]) -> np.ndarray:
    idx = active_steps(risk, floor)
    return r[idx] / risk[idx]


def psr_z(m: Moments) -> float:
    """z = sr sqrt(T_eff - 1) / sqrt(1 - skew sr + (kurt - 1)/4 sr^2); -inf when the variance term is not positive."""
    den = 1 - m.skew * m.sr + (m.kurt - 1) / 4 * m.sr ** 2
    return m.sr * (m.T - 1) ** 0.5 / den ** 0.5 if den > 0 else float("-inf")


# ---------------------------------------------------------------- the joint bar c(n)

def residuals(returns_by_asset: dict) -> np.ndarray:
    out = []
    for xs in returns_by_asset.values():
        x = np.asarray(xs, dtype=float)
        if x.size >= 3 and x.std(ddof=1) > 0:
            out.append((x - x.mean()) / x.std(ddof=1))
    return np.concatenate(out) if out else np.array([])


def fit_df(z) -> tuple[float, float | None]:
    """(df used, df fitted): Student-t df by profile likelihood over a fixed grid, unit variance; the
    grid's top, NORMAL_DF, stands for normal. Floor DF_FLOOR."""
    z = np.asarray(z, dtype=float).ravel()
    if z.size < MIN_RESIDUALS or not z.std() > 0:
        return DF_FLOOR, None
    z = (z - z.mean()) / z.std(ddof=1)
    best = None
    for df in [round(float(d), 6) for d in np.concatenate([np.linspace(2.05, 10, 160), np.geomspace(10, NORMAL_DF, 60)])]:
        s = math.sqrt((df - 2) / df)
        ll = (z.size * (math.lgamma((df + 1) / 2) - math.lgamma(df / 2) - 0.5 * math.log(df * math.pi) - math.log(s))
              - (df + 1) / 2 * float(np.log1p((z / s) ** 2 / df).sum()))
        if best is None or ll > best[0]:
            best = (ll, df)
    fitted = float(NORMAL_DF) if best[1] >= NORMAL_DF - 1e-6 else best[1]
    return max(float(DF_FLOOR), fitted), fitted


def sup_z(x: np.ndarray, min_t: int) -> np.ndarray:
    """sup over k in [min_t, T] of z_k, per row of x."""
    k = np.arange(1, x.shape[1] + 1, dtype=float)[min_t - 1:]
    s1, s2, s3, s4 = (np.cumsum(x ** p, 1)[:, min_t - 1:] for p in (1, 2, 3, 4))
    mu = s1 / k
    m2 = s2 / k - mu ** 2
    m3 = s3 / k - 3 * mu * s2 / k + 2 * mu ** 3
    m4 = s4 / k - 4 * mu * s3 / k + 6 * mu ** 2 * s2 / k - 3 * mu ** 4
    with np.errstate(invalid="ignore", divide="ignore"):
        sr = mu / np.sqrt(m2 * k / (k - 1))
        den = 1 - (m3 / m2 ** 1.5) * sr + ((m4 / m2 ** 2) - 1) / 4 * sr ** 2
        z = sr * np.sqrt(k - 1) / np.sqrt(den)
    return np.nanmax(np.where(np.isfinite(z), z, np.nan), 1)


def sup_t(x: np.ndarray, min_t: int) -> np.ndarray:
    """sup over k in [min_t, T] of the plain t-statistic of the first k returns, per row of x."""
    k = np.arange(1, x.shape[1] + 1, dtype=float)[min_t - 1:]
    s1, s2 = (np.cumsum(x ** p, 1)[:, min_t - 1:] for p in (1, 2))
    with np.errstate(invalid="ignore", divide="ignore"):
        t = (s1 / k) / np.sqrt((s2 - s1 * s1 / k) / (k - 1) / k)
    return np.nanmax(np.where(np.isfinite(t), t, np.nan), 1)


def levels(threshold: float, paths: int) -> list[float]:
    body = [round(p, 4) for p in np.linspace(0.01, 0.99, 99)]
    deepest = math.log10(paths) - 0.5
    tail = [1 - 10 ** -u for u in np.arange(2.0, deepest + 1e-9, 0.02)]
    exact = [threshold ** (1 / n) for n in N_GRID if threshold < 1]
    return sorted({float(p) for p in body + tail + exact if 0 < p < 1})


def start_k(T: int, min_t: int) -> int:
    return min(max(min_t, 4), T)


@functools.lru_cache(maxsize=16)
def calibrate(T: int, min_t: int, df: float, threshold: float, paths: int, seed: int, stat: str = DEFAULT_STAT,
              spending: tuple | None = None) -> dict:
    """F's quantiles: the null CDF of the sup of the plain t for one trial, iid Student-t(df) returns (normal
    from NORMAL_DF), `paths` paths drawn in order from default_rng(seed). stat "psr": of sup z_k;
    "w3": of the plain t of draws of unit variance, what a normalized return has, clipped to [-3, 3] first.
    spending: (planned openings, importance-sampling paths[, the deepest level wanted]): rule version 3's bars too."""
    sup = sup_t if stat == "t" or stat.startswith("w") else sup_z
    clip = float(stat[1:]) if stat.startswith("w") else None
    unit = 1.0 if df >= NORMAL_DF else math.sqrt(df / (df - 2))
    rng = np.random.default_rng(seed)
    chunk = max(1000, int(2.5e8 / (12 * 8 * T)))
    sups = []
    for start in range(0, paths, chunk):
        n = min(chunk, paths - start)
        x = rng.normal(size=(n, T)) if df >= NORMAL_DF else rng.standard_t(float(df), size=(n, T))
        sups.append(sup(x if clip is None else winsorized(x / unit, clip), start_k(T, min_t)))
    s = np.sort(np.concatenate(sups))
    ps = levels(threshold, paths)
    qs = np.quantile(s, ps)
    zs = np.maximum.accumulate(np.r_[qs, s[-1]])
    jb = {"T": T, "min_t": min_t, "threshold": threshold, "df": df, "paths": paths, "seed": seed,
          "zs": zs, "ps": np.r_[ps, 1.0]}
    if spending is not None:
        jb["spending"] = spending_table(s, T, start_k(T, min_t), df, seed, *spending)
    return jb


# ---------------------------------------------------------------- rule version 3: spending by trial

def alpha_of(k: int, planned: int) -> float:
    """alpha_k: 0.045 / N up to the planned openings, then 0.005 * 6 / (pi^2 (k - N)^2): at most 0.05 in all."""
    return ALPHA_PLANNED / planned if k <= planned else ALPHA_TAIL * 6 / (math.pi ** 2 * (k - planned) ** 2)


def tail_levels(deepest: float = DEEPEST_ALPHA) -> list:
    n = round(-math.log10(DEEPEST_ALPHA) - 2) * LEVELS_PER_DECADE
    return [a for a in (10.0 ** (-2 - i / LEVELS_PER_DECADE) for i in range(n + 1)) if a >= deepest * (1 - 1e-12)]


def tilted_paths(rng, n: int, T: int, start: int, df: float, b: float) -> tuple:
    """(sup t, likelihood ratio p/q) of n paths from a mixture: each component tilts the normal part of the first k
    draws to the mean and variance that put the t-statistic at k on b; DEFENSIVE of the paths are left at the null, so
    no ratio exceeds 1 / DEFENSIVE. The mean of ratio x 1{sup >= c} is P(sup >= c) under the null."""
    ks = np.unique(np.round(np.geomspace(start, T, IS_COMPONENTS)).astype(int))
    rho = b / np.sqrt(ks)
    sigma = 1 / np.sqrt(1 + rho * rho)
    mu = rho * sigma
    weights = np.r_[DEFENSIVE, np.full(len(ks), (1 - DEFENSIVE) / len(ks))]
    sups, ratios = [], []
    chunk = max(1000, int(2.5e8 / (12 * 8 * T)))
    for at in range(0, n, chunk):
        m = min(chunk, n - at)
        comp = rng.choice(len(ks) + 1, size=m, p=weights)
        z = rng.normal(size=(m, T))
        tilted = np.arange(T)[None, :] < np.r_[0, ks][comp][:, None]
        z = np.where(tilted, np.r_[0.0, mu][comp][:, None] + np.r_[1.0, sigma][comp][:, None] * z, z)
        x = z if df >= NORMAL_DF else z * np.sqrt(df / rng.chisquare(df, size=z.shape))
        sups.append(sup_t(x, start))
        s1, s2 = np.cumsum(z, 1)[:, ks - 1], np.cumsum(z * z, 1)[:, ks - 1]
        log_q = -ks * np.log(sigma) - (s2 - 2 * mu * s1 + ks * mu * mu) / (2 * sigma * sigma) + s2 / 2
        ratios.append(1 / (DEFENSIVE + (1 - DEFENSIVE) * np.exp(log_q).mean(1)))
    return np.concatenate(sups), np.concatenate(ratios)


def tail_curve(s: np.ndarray, w: np.ndarray | None = None) -> tuple:
    n = len(s)
    order = np.argsort(-s, kind="stable")
    s = s[order]
    w = np.ones(n) if w is None else w[order]
    p = np.cumsum(w) / n
    return s, p, np.sqrt(np.maximum(np.cumsum(w * w) / n - p * p, 0.0) / n)


def read_level(curve: tuple, alpha: float) -> tuple:
    s, p, se = curve
    over = p + MARGIN_SE * se > alpha
    i = int(np.argmax(over)) if over.any() else len(s)
    if i < MIN_HITS:
        return None, None
    rel = float(se[i - 1] / p[i - 1])
    return (float(s[i - 1]) if rel <= REL_SE_MAX else None), rel


def _station_curve(T, start, df, seed, station, alpha, is_paths) -> tuple:
    rng = np.random.default_rng([seed, 3, station])
    b = math.sqrt(2 * math.log(1 / alpha))
    for _ in range(IS_PILOT_ROUNDS):
        s, p, _ = tail_curve(*tilted_paths(rng, IS_PILOT_PATHS, T, start, df, b))
        over = p > alpha
        if over.any():
            b = float(s[max(int(np.argmax(over)) - 1, 0)])
    return tail_curve(*tilted_paths(rng, is_paths, T, start, df, b))


def spending_table(plain: np.ndarray, T: int, start: int, df: float, seed: int, planned: int, is_paths: int,
                   deepest: float = DEEPEST_ALPHA) -> dict:
    plain_curve = tail_curve(plain)
    curves: dict = {}

    def bar_at(alpha: float) -> tuple:
        if alpha >= max(PLAIN_FLOOR, 1000 / len(plain)) * (1 - 1e-12):      # the plain table has the paths for it
            return read_level(plain_curve, alpha)
        station = int(round(-2 * math.log10(alpha)))
        if station not in curves:
            curves[station] = _station_curve(T, start, df, seed, station, 10.0 ** (-station / 2), is_paths)
        return read_level(curves[station], alpha)

    alpha0 = ALPHA_PLANNED / planned
    planned_bar, planned_rel = bar_at(alpha0) if alpha0 >= DEEPEST_ALPHA else (None, None)
    out, top, dead = [], -math.inf, False
    for alpha in tail_levels(deepest):
        b, rel = (None, None) if dead else bar_at(alpha)
        dead = dead or b is None
        if b is not None:
            top = b = max(top, b)
        out.append([alpha, b, rel])
    return {"planned_openings": planned, "alpha_planned": ALPHA_PLANNED, "alpha_tail": ALPHA_TAIL, "is_paths": is_paths,
            "margin_se": MARGIN_SE, "rel_se_max": REL_SE_MAX, "components": IS_COMPONENTS, "defensive": DEFENSIVE,
            "planned": {"alpha": alpha0, "bar": planned_bar, "rel_se": planned_rel}, "levels": out}


def trial_bar(sp: dict, k: int) -> tuple:
    """(alpha_k, b_k) from a spending table; None for b_k is +infinity, a plain FAIL."""
    alpha = alpha_of(k, sp["planned_openings"])
    if k <= sp["planned_openings"]:
        return alpha, sp["planned"]["bar"]
    for level, b, _ in sp["levels"]:
        if level <= alpha:
            return alpha, b
    return alpha, None


def passes_v3(t, b: float | None, min_t: int) -> bool:
    """Rule version 3's verdict on one trial: its plain t over ex-ante risk strictly above b_k."""
    if b is None or t is None or t.active is None or t.t_eff < min_t or t.t_eff <= 3:
        return False
    return t.tstat > b


# ---------------------------------------------------------------- rule version 3, the trial's own bar
#
# b_k from the trial's own normalized returns x (its active steps, r / ex-ante risk), not from the holdout's assets: the
# (1 - alpha_k) quantile of the sup over k in [start, T] of the plain t of series y of length T built from x by a
# stationary block bootstrap (blocks of mean length BOOT_BLOCK(T), a rule of T alone, never of the data), each y made
# mean zero by `mode`. The bar is the m-th largest of B = ceil(m / alpha) - 1 replicates, m = BOOT_M: a trial passes
# iff fewer than m replicates reach its t, so that #{S_b >= t} + 1 <= alpha (B + 1). The replicates' uniforms come from
# default_rng(seed) in batches of BOOT_BATCH and do not depend on len(x): the same seed gives the same replicates, the
# bar is a function of x and the seed alone, and anyone holding both recomputes it.

BOOT_M = 20
BOOT_BATCH = 1000
BOOT_MODES = ("signs", "center")


def boot_seed(opening: bytes, secret: bytes) -> list[int]:
    """A trial's seed: SHA256(its signed opening record || the holdout's secret), eight 32-bit words for default_rng.
    The security is the secret's: unknown to the researcher when the weights are chosen (the data host makes it and
    keeps it until the holdout is retired, then publishes it), so the block sampling that grades a series cannot be
    chosen against. The hash only binds each seed to its own trial and spreads it; with the secret known beforehand
    the seed is known, and a bar can be steered (tests/test_boot_seed.py)."""
    import hashlib
    d = hashlib.sha256(bytes(opening) + bytes(secret)).digest()
    return [int.from_bytes(d[i:i + 4], "big") for i in range(0, 32, 4)]


def boot_block(T: int) -> float:
    """The stationary bootstrap's mean block length: T^(1/3), the rate of Politis and White (2004), fixed from T."""
    return T ** (1 / 3)


def boot_replicates(alpha: float, m: int = BOOT_M) -> int:
    return max(int(math.ceil(m / alpha - 1e-9)) - 1, m)


class BootStream:
    """The replicates' randomness for one seed, independent of the series: per replicate and step, the uniform that
    places the current block's start, the step's offset inside its block, and its sign."""

    def __init__(self, seed, T: int, B: int, block: float | None = None):
        self.T, self.B, self.block = T, B, boot_block(T) if block is None else block
        self.seed = seed
        self._batches: list = []

    def batch(self, j: int) -> tuple:
        while len(self._batches) <= j:
            i = len(self._batches)
            M = min(BOOT_BATCH, self.B - i * BOOT_BATCH)
            rng = np.random.default_rng([*np.atleast_1d(self.seed).tolist(), i])
            pos = np.arange(self.T)
            new = rng.random((M, self.T)) < 1 / self.block
            new[:, 0] = True
            u = rng.random((M, self.T))
            last = np.maximum.accumulate(np.where(new, pos, 0), axis=1)
            start_u = np.take_along_axis(u, last, 1)
            off = (pos - last).astype(np.int32)
            signs = np.where(rng.random((M, self.T)) < 0.5, -1.0, 1.0)
            self._batches.append((start_u, off, signs))
        return self._batches[j]

    def batches(self) -> int:
        return -(-self.B // BOOT_BATCH)


def boot_sups(x: np.ndarray, stream: BootStream, j: int, start: int, mode: str = "signs") -> np.ndarray:
    """One batch's sup t of the replicates built from x."""
    n = len(x)
    start_u, off, signs = stream.batch(j)
    idx = (np.floor(start_u * n).astype(np.int64) + off) % n
    if mode == "signs":
        y = x[idx] * signs
    elif mode == "center":
        y = x[idx] - x.mean()
    else:
        raise ValueError(mode)
    return sup_t(y, start)


def boot_bar(x, alpha: float, seed, T: int, min_t: int, mode: str = "signs", m: int = BOOT_M,
             stream: BootStream | None = None) -> float:
    """b_k for the series x: the m-th largest replicate sup."""
    x = np.asarray(x, dtype=float)
    stream = stream or BootStream(seed, T, boot_replicates(alpha, m))
    s = np.concatenate([boot_sups(x, stream, j, start_k(T, min_t), mode) for j in range(stream.batches())])
    s = np.where(np.isnan(s), -np.inf, s)
    return float(np.sort(s)[-m])


def boot_passes(x, t: float, alpha: float, seed, T: int, min_t: int, mode: str = "signs", m: int = BOOT_M,
                stream: BootStream | None = None) -> bool:
    """t > boot_bar(x, ...), decided without the whole bar: false as soon as m replicates reach t."""
    x = np.asarray(x, dtype=float)
    stream = stream or BootStream(seed, T, boot_replicates(alpha, m))
    reached = 0
    for j in range(stream.batches()):
        reached += int((boot_sups(x, stream, j, start_k(T, min_t), mode) >= t).sum())
        if reached >= m:
            return False
    return True


def passes_boot(trial, alpha: float, seed, T: int, min_t: int, mode: str = "signs", m: int = BOOT_M, stream=None) -> bool:
    """Rule version 3 with the trial's own bar: its plain t over ex-ante risk above boot_bar of its own series."""
    if trial is None or trial.active is None or trial.t_eff < min_t or trial.t_eff <= 3:
        return False
    return boot_passes(trial.x, trial.tstat, alpha, seed, T, min_t, mode, m, stream)


def bar(jb: dict, n: int) -> float:
    """c(n) = F^-1(threshold^(1/n)), extrapolated linearly in log n beyond N_CAP."""
    if n < 1:
        raise ValueError("n >= 1")
    if n <= N_CAP:
        return float(np.interp(jb["threshold"] ** (1 / n), jb["ps"], jb["zs"]))
    a, b = bar(jb, N_CAP // 2), bar(jb, N_CAP)
    return b + (b - a) * (math.log(n) - math.log(N_CAP)) / (math.log(N_CAP) - math.log(N_CAP // 2))


def _cdf(jb: dict, z: float) -> float:
    zs, ps = jb["zs"], jb["ps"]
    if z > zs[-1]:
        return 1.0
    keep = np.r_[zs[1:] != zs[:-1], True]   # ties: the last level
    return float(np.interp(z, zs[keep], ps[keep], left=0.0))


def value(jb: dict, z: float, n: int) -> float:
    """F(z)^n; beyond N_CAP, F(z - (c(n) - c(N_CAP)))^N_CAP: value >= threshold iff z >= c(n)."""
    if n <= N_CAP:
        return _cdf(jb, z) ** n
    return _cdf(jb, z - (bar(jb, n) - bar(jb, N_CAP))) ** N_CAP


# ---------------------------------------------------------------- the verdicts

@dataclass
class Trial:
    """One series the holdout returned: its moments on all T, and over ex-ante risk."""
    r: np.ndarray
    m: Moments
    t_eff: int | None = None
    active: Moments | None = None
    x: np.ndarray | None = None      # the active steps' r / risk: what the trial's own bar is built from

    @property
    def tstat(self) -> float | None:
        return None if self.active is None else self.active.sr * self.active.T ** 0.5


def trial_of_weights(W: np.ndarray, R: np.ndarray, cov: tuple) -> Trial:
    r = (W * R).sum(1)
    if isinstance(cov, BoundedCov):
        risk = risks_of(W, cov)
        idx = bounded_steps(W, risk, cov)
        try:
            return Trial(r, moments(r), len(idx), moments(bounded_returns(r[idx], risk[idx], cov)))
        except ValueError:
            return Trial(r, moments(r), len(idx), None)
    risk = risks_of(W, cov)
    t_eff, active = active_moments(r, risk)
    return Trial(r, moments(r), t_eff, active, active_series(r, risk) if active is not None else None)


def trial_of_returns(r) -> Trial:
    """A series with no weights (the DSR's evaluation needs no more): every step active."""
    r = np.asarray(r, dtype=float)
    m = moments(r)
    return Trial(r, m, m.T, m)


def scale(tstats) -> float:
    """max(1, the sample sd of the other trials' t-statistics); 1 with fewer than two."""
    t = [x for x in tstats if x is not None]
    return max(1.0, sharpe_variance(t) ** 0.5) if len(t) >= 2 else 1.0


@dataclass
class Verdict:
    passed: bool
    values: dict
    z: float | None = None
    bar: float | None = None
    scales: dict | None = None
    t_eff: int | None = None


FAMILIES = ("value", "value_excl", "value_without", "value_without_excl", "value_without_excl_zt_flags")


class Holdout:
    """A researcher's openings of one holdout: the series returned (each its own config), failed openings'
    partial returns zero-padded to T (in N and the "with" families, never promotable), failed openings with
    no valid series (in N only), and fresh verifications among the openings (in N, not in the bar's n)."""

    def __init__(self, trials: list[Trial], padded: list[Trial] = (), n_zero: int = 0, verifications: int = 0):
        self.trials, self.padded = list(trials), list(padded)
        self.N = len(self.trials) + len(self.padded) + n_zero
        self.verifications = verifications
        self._flags = None

    def flags(self) -> tuple[Flags, Flags]:
        if self._flags is None:
            series = [t.r for t in self.trials]
            self._flags = flag(series + [t.r for t in self.padded]), flag(series)
        return self._flags

    def _families(self, me: int, of) -> tuple[list, list, list, list, list]:
        """The five families' trials, by `of` (a Sharpe or a t-statistic), candidate in or out as the caller filters."""
        with_zt, wo = self.flags()
        xs = [of(t) for t in self.trials]
        zs = [of(t) for t in self.padded]
        kept = [x for i, x in enumerate(xs) if i not in with_zt.flagged or i == me]
        kept_wo = [x for i, x in enumerate(xs) if i not in wo.flagged or i == me]
        return xs + zs, kept + zs, xs, kept_wo, kept

    def before(self, me: int, min_t: int, threshold: float = 0.95, reserved: int = 1) -> Verdict:
        m = self.trials[me].m
        if m.T < min_t:
            return Verdict(False, {})
        n = self.N + reserved
        values = {f: deflated_value(m, srs, n) for f, srs in zip(FAMILIES, self._families(me, lambda t: t.m.sr))}
        return Verdict(min(values.values()) >= threshold, values)

    def joint(self, me: int, jb: dict, min_t: int, threshold: float = 0.95, stat: str = DEFAULT_STAT) -> Verdict:
        t = self.trials[me]
        if t.active is None or t.t_eff < min_t or t.t_eff <= 3:
            return Verdict(False, {}, t_eff=t.t_eff or 0)
        with_zt, wo = self.flags()
        ts = [x.tstat for x in self.trials]
        zt_ts = [x.tstat for x in self.padded]
        kept_t = [x for i, x in enumerate(ts) if i not in with_zt.flagged and i != me]
        kept_wo_t = [x for i, x in enumerate(ts) if i not in wo.flagged and i != me]
        ts = [x for i, x in enumerate(ts) if i != me]
        scales = dict(zip(FAMILIES, map(scale, (ts + zt_ts, kept_t + zt_ts, ts, kept_wo_t, kept_t))))
        n_bar = self.N - self.verifications
        z = t.tstat if stat == "t" else psr_z(t.active)
        values = {f: value(jb, z / s, n_bar) for f, s in scales.items()}
        return Verdict(min(values.values()) >= threshold, values, z, bar(jb, n_bar), scales, t.t_eff)
