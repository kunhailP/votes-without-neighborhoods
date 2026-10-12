"""Unit tests for the allocation polytope. Run: pytest -q"""
import numpy as np
import pytest
from vwn.lp import JointLP, CANDS
from vwn.ytight import CLP
from vwn.intcheck import solve_int

C = len(CANDS)


def two_dong(allow=None):
    """Two dongs; dong 0 has 100 removed residents but its station counted 150 early ballots,
    dong 1 has 100 removed residents and its station counted 50: the roll forces 50 movers from 1 to 0."""
    K = np.zeros((2, C)); K[0, 0] = 150; K[1, 0] = 50
    A = np.zeros((2, C)); A[:, 0] = 100
    g = dict(emds=["a", "b"], A=A, K=K, Avotes=A.sum(1), D=np.array([500.0, 500.0]),
             Bc=np.zeros(C), Gc=np.zeros(C), U=0.0, a_tilde=np.full((2, C), 1 / C))
    if allow is not None: g["allow"] = allow; g["zone"] = np.array([0, 1])
    return g, np.array([600.0, 600.0])


def cross_flow(lp):
    c = np.zeros(lp.nv)
    for k in range(C): c[lp.iF(1, 0, k)] = 1; c[lp.iF(0, 1, k)] = 1
    return c


def test_forced_movement_feasible_without_zones():
    lp = JointLP(*two_dong())
    r = lp.solve(cross_flow(lp), 1.0, 1.0)
    assert r.status == 0 and abs(r.fun - 50) < 1e-6      # the roll forces at least 50 cross-dong ballots


def test_zone_restriction_shared_by_all_solver_paths():
    """Forbidding cross-dong voting makes the problem infeasible in every path (LP, CLP, MILP).
    A path that ignored the zone restriction would return 0."""
    allow = np.eye(2, dtype=bool)
    lp = JointLP(*two_dong(allow))
    assert lp.solve(cross_flow(lp), 1.0, 1.0).status == 2
    clp = CLP(lp)
    assert clp.solve(cross_flow(lp), 1.0, 1.0).status == 2
    assert solve_int(clp, cross_flow(lp), 1.0, 1.0, tl=10).x is None


def test_zone_restriction_binds_minimum():
    """Three dongs, zones {0,1} and {2}: forced inflow at station 0 must come from dong 1."""
    K = np.zeros((3, C)); K[0, 0] = 150; K[1, 0] = 50; K[2, 0] = 100
    A = np.zeros((3, C)); A[:, 0] = 100
    g = dict(emds=list("abc"), A=A, K=K, Avotes=A.sum(1), D=np.full(3, 500.0), Bc=np.zeros(C), Gc=np.zeros(C), U=0.0,
             a_tilde=np.full((3, C), 1 / C), zone=np.array([0, 0, 1]))
    g["allow"] = g["zone"][:, None] == g["zone"][None, :]
    lp = JointLP(g, np.full(3, 600.0))
    c = np.zeros(lp.nv)
    for k in range(C): c[lp.iF(2, 0, k)] = -1        # maximize flow from dong 2 to station 0
    for path in (lp.solve, CLP(lp).solve):
        r = path(c, 1.0, 1.0); assert r.status == 0 and abs(r.fun) < 1e-9


def test_roll_identity_closes():
    lp = JointLP(*two_dong())
    r = lp.solve(np.zeros(lp.nv), 1.0, 1.0)
    F, B, G, U = lp.state(r.x)
    assert np.allclose(F.sum((1, 2)) + B.sum(1) + G.sum(1) + U, lp.E - lp.g["D"])
    assert np.allclose(F.sum(0), lp.g["K"])


def test_clp_does_not_reuse_stale_matrices():
    """A restriction changed after the CLP was built (and used) must reach its constraint matrices."""
    lp = JointLP(*two_dong()); clp = CLP(lp)
    assert clp.solve(cross_flow(lp), 1.0, 1.0).status == 0
    lp.allow = np.eye(2, dtype=bool)
    assert lp.solve(cross_flow(lp), 1.0, 1.0).status == 2
    assert clp.solve(cross_flow(lp), 1.0, 1.0).status == 2


def test_sign_margin_full_disclosure():
    """Reporting the whole allocation always reveals the sign, even when zero-slope allocations are feasible
    (the criterion min theta(l) s.t. theta(l') >= 0 being > 0 would fail this case)."""
    import sys, os, scipy.sparse as sp
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis", "reporting"))
    from sign_guarantee import margin
    lp = JointLP(*two_dong()); Aeq, beq, Aub, bub = lp.cached_constraints(1.0, 1.0)
    c = np.zeros(lp.nv)
    for k in range(C): c[lp.iF(0, 0, k)] = 1.0; c[lp.iF(1, 0, k)] = -1.0     # theta takes both signs and zero on Lambda
    k0 = 0.0                                                                   # theta in [-50, 50]
    t_full = margin([(Aeq, beq, Aub, bub, c, k0, sp.identity(lp.nv))])[0]
    t_none = margin([(Aeq, beq, Aub, bub, c, k0, sp.csr_matrix((0, lp.nv)))])[0]
    assert t_full <= 1e-7 and t_none > 1e-3


def test_calibration_aligned_by_name():
    """Calibrated movement is matched to the LP's dongs by name, whatever the row order of the calibration file."""
    import pandas as pd
    from vwn.data import align_calib
    G = {"u": (dict(emds=["b", "a", "c"]), None)}
    cal = pd.DataFrame(dict(unit="u", emd=["a", "b", "c"], eta_j=[0.1, 0.2, 0.3]))
    assert list(align_calib(cal, G, ["u"])["u"].eta_j) == [0.2, 0.1, 0.3]
    with pytest.raises(ValueError):
        align_calib(cal[cal.emd != "c"], G, ["u"])
