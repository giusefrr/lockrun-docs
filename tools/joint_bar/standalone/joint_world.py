"""The null worlds and the adversaries, self-contained: numpy and joint_rule only.

Ported from tests/adversary_world.py (the first table: iid N(0, 1%) assets) and tests/risk_world.py (the
rest: volatilities from 0.1% to 2%, the last two assets twins). A strategy is a weight matrix whose step t
uses only what is known before period t; a PASS under the null is a false positive, nominal 1 - threshold.
Every draw is seeded by the seed, the trial and the stream, so the markets and strategies are those of the
package's worlds.
"""
from __future__ import annotations

import functools

import numpy as np

import joint_rule as jr

T, MIN_T, THRESHOLD = 250, 100, 0.95
P = jr.EXPOSURE
PATHS, SEED = 500_000, 20261027
GRID = [(c, k0) for c in (1.5, 2.0, 2.5, 3.0, 3.5) for k0 in (2, 3, 20, 100)]
REGIME = (125, 5, 0.1)    # asset 5's volatility a tenth of itself from period 125: the window lags it
# The README's first table: its grid of (c, k0), and the smaller one of the two evasions.
FINDING_GRID = [(c, k0) for c in (1.5, 2.0, 2.5, 3.0, 4.0, 6.0) for k0 in (2, 3, 5, 10, 20)]
EVASION_GRID = [(2.0, 2), (2.5, 3), (2.0, 20), (3.0, 2)]


def joint_bar() -> dict:
    """The bar of the implementation checks: normal tail, the df fit of this market."""
    return jr.calibrate(T, MIN_T, float(jr.NORMAL_DF), THRESHOLD, PATHS, SEED)


def t4_joint_bar() -> dict:
    """The bar at the fitted df of the Student-t(4) market."""
    R = market(0, tail=4)
    used, _ = jr.fit_df(jr.residuals({a: R[:, a] for a in range(R.shape[1])}))
    return jr.calibrate(T, MIN_T, float(used), THRESHOLD, PATHS, SEED)


# ---------------------------------------------------------------- the first table's world

def iid_market(seed: int, assets: int = 8) -> np.ndarray:
    return np.random.default_rng([seed, 0]).normal(0.0, 0.01, (T, assets))


def random_weights(seed: int, i: int, assets: int = 8) -> np.ndarray:
    return np.random.default_rng([seed, i, 1]).normal(size=(T, assets))


def running_t(x: np.ndarray) -> np.ndarray:
    """t[k-1]: the t-statistic of x[:k], what the strategy can compute after period k (NaN for k < 2)."""
    k = np.arange(1, len(x) + 1)
    s, q = np.cumsum(x), np.cumsum(x * x)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(k >= 2, (s / k) / np.sqrt((q - s * s / k) / (k - 1) / k), np.nan)


def first_crossing(t: np.ndarray, c: float, k0: int) -> int | None:
    """The number of periods after which t, one value per period, first reaches c, from period k0."""
    hit = np.flatnonzero((np.arange(1, len(t) + 1) >= k0) & (t >= c))
    return int(hit[0]) + 1 if hit.size else None


def stopped_returns(r: np.ndarray, k: int | None, mode: str, par=None) -> np.ndarray:
    """What the first table's strategies do to their returns once ahead: flat, flat and trading again for
    the last par periods, or scaled by par."""
    if k is None:
        return r
    r = r.copy()
    if mode == "flat":
        r[k:] = 0.0
    elif mode == "resume":
        r[k:T - par] = 0.0
    elif mode == "tiny":
        r[k:] *= par
    return r


def best_run(trials: list) -> int:
    """The trial a researcher promotes: the highest Sharpe it was shown."""
    return max(range(len(trials)), key=lambda i: trials[i].r.mean() / trials[i].r.std(ddof=1))


# ---------------------------------------------------------------- the world with weights

def market(seed: int, A: int = 8, tail: float | None = None, drift: float | None = None,
           regime: tuple | None = None) -> np.ndarray:
    """T x A asset returns. drift: asset 3's per-period Sharpe. regime (period, asset, factor): that
    asset's volatility times factor from that period on."""
    rng = np.random.default_rng([seed, 0])
    vol = np.geomspace(0.001, 0.02, A)
    vol[-2] = vol[-1] = 0.01
    z = rng.standard_t(tail, (T, A)) / np.sqrt(tail / (tail - 2)) if tail else rng.normal(size=(T, A))
    R = z * vol
    R[:, -1] = R[:, -2] + np.random.default_rng([seed, 5]).normal(0, 1e-4, T)
    if drift is not None:
        R[:, 3] += drift * vol[3]
    if regime is not None:
        p, a, f = regime
        R[p:, a] *= f
    return R


def base_weights(seed: int, i: int, A: int) -> np.ndarray:
    """Random directions, gross exposure 1 every period: an honest null strategy."""
    W = np.random.default_rng([seed, i, 1]).normal(size=(T, A))
    return W / np.abs(W).sum(1, keepdims=True)


def normalized_t(W: np.ndarray, R: np.ndarray, cov: tuple) -> tuple[np.ndarray, np.ndarray]:
    """(the running t-statistic of the strategy's normalized returns, the periods it is at)."""
    risk = jr.risks_of(W, cov)
    idx = jr.active_steps(risk)
    if not idx.size:
        return np.array([]), idx
    return running_t((W * R).sum(1)[idx] / risk[idx]), idx


def first_ahead(W: np.ndarray, R: np.ndarray, cov: tuple, c: float, k0: int) -> int | None:
    """The first period (1-based count) after which the strategy's normalized t is at least c, from k0."""
    t, idx = normalized_t(W, R, cov)
    hit = np.flatnonzero((idx >= k0 - 1) & (t >= c))
    return int(idx[hit[0]]) + 1 if hit.size else None


def after_stop(W: np.ndarray, k: int, variant: tuple, seed: int, i: int) -> np.ndarray:
    """What the strategy does from period k on, once ahead."""
    kind, par = variant
    A = W.shape[1]
    if kind == "flat":
        W[k:] = 0.0
    elif kind == "resume":                        # flat, then trading again for the last par periods
        W[k:T - par] = 0.0
    elif kind == "tiny":                          # weights times par instead of zero
        W[k:] *= par
    elif kind == "diversify":                     # the same gross spread over every asset
        W[k:] = 1.0 / A
    elif kind == "hedge":                         # long one twin, short the other: gross 2, little risk
        W[k:] = 0.0
        W[k:, -2], W[k:, -1] = 1.0, -1.0
    elif kind == "hedge-drift":                   # the hedge's ratio a slow random walk from 1
        beta = 1 + np.cumsum(np.random.default_rng([seed, i, 7]).normal(0, 0.002, T - k))
        W[k:] = 0.0
        W[k:, -2], W[k:, -1] = 1.0, -beta
    elif kind == "lowvar":                        # only the lowest-variance asset
        W[k:] = 0.0
        W[k:, 0] = 1.0
    return W


def honest_flat_days(W: np.ndarray, seed: int, i: int) -> np.ndarray:
    """10% of days flat, at random: no terminal run."""
    W[np.random.default_rng([seed, i, 9]).random(T) < 0.10] = 0.0
    return W


def regime_weights(W: np.ndarray, k: int | None) -> np.ndarray:
    """Once ahead, and once the regime has shifted, only the asset whose volatility just fell: the rolling
    window still sees its old risk for up to `window` periods."""
    if k is None:
        return W
    W = W.copy()
    W[k:] = 0.0
    W[k:, REGIME[1]] = 1.0
    return W


def nullspace_weights(seed: int, i: int, R: np.ndarray, c: float, k0: int, nulls: dict | None = None,
                      p: dict = P) -> np.ndarray:
    """In a universe larger than the window, the window's covariance is singular. After a losing active
    period the strategy holds a portfolio in its null space for one period (estimated risk zero: a pause the
    rule does not count); otherwise random weights; flat once ahead (running t of its active returns at
    least c, from k0). nulls: the null space per step, kept across the seed's trials (the market's alone)."""
    rng = np.random.default_rng([seed, i, 11])
    A = R.shape[1]
    W = np.zeros((T, A))
    active: list[float] = []
    paused = False
    nulls = {} if nulls is None else nulls
    for t in range(T):
        rows = R[max(0, t - p["window"]):t]
        ahead = len(active) >= 2 and np.std(active, ddof=1) > 0 and \
            np.mean(active) / (np.std(active, ddof=1) / np.sqrt(len(active)))
        if active and t + 1 > k0 and ahead is not False and ahead >= c:
            break                                          # flat from here on
        if len(rows) >= p["warmup"] and active and active[-1] < 0 and not paused:
            if t not in nulls:
                X = rows - rows.mean(0)
                nulls[t] = np.linalg.svd(X)[2][np.linalg.matrix_rank(X):]
            null = nulls[t]
            w = null.T @ rng.normal(size=len(null))
            W[t] = w / np.abs(w).sum()
            paused = True
            continue                                       # inactive: not in the running t
        w = rng.normal(size=A)
        W[t] = w / np.abs(w).sum()
        paused = False
        if len(rows) >= p["warmup"]:
            active.append(float(W[t] @ R[t]))
    return W


def strategy(seed: int, i: int, R: np.ndarray, cov: tuple, variant: tuple, c: float | None, k0: int | None,
             watch: str = "norm") -> np.ndarray:
    """The weights of one trial, its stop decided on `watch`: "norm" (the rule's statistic) or "raw" (the
    t-statistic of its returns, what it would watch under the DSR)."""
    W = base_weights(seed, i, R.shape[1])
    if variant[0] == "honest":
        return W
    if variant[0] == "honest-flat-days":
        return honest_flat_days(W, seed, i)
    k = first_ahead(W, R, cov, c, k0) if watch == "norm" else first_crossing(running_t((W * R).sum(1)), c, k0)
    return W if k is None else after_stop(W.copy(), k, variant, seed, i)


# ---------------------------------------------------------------- the assumptions the table varies

GARCH_ALPHA, GARCH_BETA = 0.1, 0.85
GARCH_BURN = 200


def market_vols(A: int) -> np.ndarray:
    vol = np.geomspace(0.001, 0.02, A)
    vol[-2] = vol[-1] = 0.01
    return vol


@functools.lru_cache(maxsize=1)
def garch_df() -> float:
    """The innovations' df: what the rule fits on the Student-t(4) market, its fat-tailed holdout."""
    R = market(0, tail=4)
    return float(jr.fit_df(jr.residuals({a: R[:, a] for a in range(R.shape[1])}))[0])


def garch_market(seed: int, A: int = 8, df: float | None = None, regime: tuple | None = None) -> tuple:
    """(returns, sigma): each asset an independent GARCH(1,1), h_t = (1 - alpha - beta) + alpha e_{t-1}^2 +
    beta h_{t-1} on unit unconditional variance, Student-t(df) innovations of unit variance, times its
    volatility; the last two assets twins, as in market(). sigma[t] is known before period t."""
    df = garch_df() if df is None else df
    rng = np.random.default_rng([seed, 20])
    z = rng.standard_t(df, (T + GARCH_BURN, A)) / np.sqrt(df / (df - 2))
    h, hs = np.ones(A), np.empty((T + GARCH_BURN, A))
    for t in range(T + GARCH_BURN):
        hs[t] = h
        h = (1 - GARCH_ALPHA - GARCH_BETA) + GARCH_ALPHA * h * z[t] ** 2 + GARCH_BETA * h
    vol = market_vols(A)
    sigma = np.sqrt(hs[GARCH_BURN:]) * vol
    R = z[GARCH_BURN:] * sigma
    R[:, -1] = R[:, -2] + np.random.default_rng([seed, 5]).normal(0, 1e-4, T)
    sigma[:, -1] = sigma[:, -2]
    if regime is not None:
        p, a, f = regime
        R[p:, a] *= f
        sigma[p:, a] *= f
    return R, sigma


def garch_joint_bar() -> dict:
    """The bar at the df the rule fits on this market's holdout (seed 0, as t4_joint_bar)."""
    R = garch_market(0)[0]
    used, _ = jr.fit_df(jr.residuals({a: R[:, a] for a in range(R.shape[1])}))
    return jr.calibrate(T, MIN_T, float(used), THRESHOLD, PATHS, SEED)


def correlated_weights(seed: int, i: int, A: int, rho: float) -> np.ndarray:
    """Trial i of a researcher whose trials share one latent signal: the weights' correlation across trials,
    so their returns', is rho. Gross exposure 1 on average: per step, as base_weights, it would lower rho."""
    latent = np.random.default_rng([seed, 13]).normal(size=(T, A))
    own = np.random.default_rng([seed, i, 14]).normal(size=(T, A))
    return (np.sqrt(rho) * latent + np.sqrt(1 - rho) * own) / (A * np.sqrt(2 / np.pi))


def risk_aware_weights(kind: str, seed: int, i: int, R: np.ndarray, sigma: np.ndarray, cov: tuple) -> np.ndarray:
    """An exposure rule that knows the risk estimator and the true risk (both known before period t):
    scale   base_weights times true / estimated risk: as asked, though a normalized return does not move
            with the size of w; it acts only through the 10% floor
    select  the normalized return's variance is largest where the window most underestimates: all weight, a
            random sign, on the asset with the largest true / estimated risk
    pause   select, flat on the steps whose largest ratio is below the median of the ratios before them, so
            that the steps counted are those where the window underestimates most."""
    W = base_weights(seed, i, R.shape[1])
    S, ok = cov
    steps = np.flatnonzero(ok)
    if kind == "scale":
        true = (W[steps] ** 2 * sigma[steps] ** 2).sum(1) + 2 * W[steps, -2] * W[steps, -1] * sigma[steps, -2] ** 2
        est = np.einsum("ti,tij,tj->t", W[steps], S, W[steps])
        W[steps] *= np.sqrt(np.maximum(true, 0) / est)[:, None]
        return W
    ratio = sigma[steps] / np.sqrt(np.einsum("tii->ti", S))
    best = ratio.argmax(1)
    signs = np.random.default_rng([seed, i, 15]).choice([-1.0, 1.0], len(steps))
    W[steps] = 0.0
    W[steps, best] = signs
    if kind == "pause":
        top = ratio.max(1)
        for j in range(1, len(steps)):
            if top[j] < np.median(top[:j]):
                W[steps[j]] = 0.0
    return W


class SeedWorld:
    """One seed's market, with what its cells share: the window covariances, each base strategy's first
    crossings and every distinct strategy's trial. Decisions are those of building each cell from nothing.
    R: another market than market()'s; base(seed, i, A): another strategy than base_weights; p: another
    window and warm-up."""

    def __init__(self, seed: int, A: int = 8, R: np.ndarray | None = None, base=None, p: dict = P, **market_kw):
        self.seed, self.A, self.p = seed, A, p
        self.R = market(seed, A, **market_kw) if R is None else R
        self.cov = jr.window_covariances(self.R, p)
        self._make = base or base_weights
        self._base, self._trials, self._nulls = {}, {}, {}

    def _watched(self, i: int, watch: str):
        key = (i, watch)
        if key not in self._base:
            W = self._make(self.seed, i, self.A)
            if watch == "norm":
                t, idx = normalized_t(W, self.R, self.cov)
            else:
                t, idx = running_t((W * self.R).sum(1)), np.arange(T)
            self._base[key] = (W, t, idx)
        return self._base[key]

    def crossing(self, i: int, c: float, k0: int, watch: str) -> int | None:
        _, t, idx = self._watched(i, watch)
        hit = np.flatnonzero((idx >= k0 - 1) & (t >= c))
        return int(idx[hit[0]]) + 1 if hit.size else None

    def trial(self, i: int, variant: tuple, c: float | None, k0: int | None, watch: str) -> jr.Trial:
        kind = variant[0]
        if kind.startswith("honest"):
            key = (i, variant)
        elif kind == "nullspace":
            key = (i, variant, c, k0)
        else:
            k = self.crossing(i, c, max(k0, REGIME[0] + 1) if kind == "regime" else k0, watch)
            key = (i, variant if k is not None else None, k)
        if key not in self._trials:
            self._trials[key] = jr.trial_of_weights(self._weights(i, variant, c, k0, watch, key), self.R, self.cov)
        return self._trials[key]

    def _weights(self, i, variant, c, k0, watch, key):
        kind = variant[0]
        if kind == "nullspace":
            return nullspace_weights(self.seed, i, self.R, c, k0, self._nulls, self.p)
        W = self._watched(i, watch)[0]
        if kind == "honest":
            return W
        if kind == "honest-flat-days":
            return honest_flat_days(W.copy(), self.seed, i)
        k = key[-1]
        if k is None:
            return W
        return regime_weights(W, k) if kind == "regime" else after_stop(W.copy(), k, variant, self.seed, i)
