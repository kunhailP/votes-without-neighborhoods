"""Check disclosure bounds against a fully enumerable integer example."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from vwn.lp import CANDS, JointLP

path = Path(__file__).parents[1] / 'analysis/reporting/disclosure_guarantee.py'
spec = importlib.util.spec_from_file_location('disclosure_guarantee', path)
reporting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reporting)


def example():
    C = len(CANDS)
    A = np.zeros((2, C)); A[:, :2] = 1
    B = np.zeros(C); B[:2] = 3
    g = dict(A=A, K=np.zeros((2, C)), Avotes=A.sum(1), D=np.full(2, 2.0),
             Bc=B, Gc=np.zeros(C), U=0.0, a_tilde=np.full((2, C), 1/C))
    return JointLP(g, np.full(2, 5.0))


@pytest.mark.parametrize('tolerance, expected', [(0, 0), (1, 0.4), (2, 0.8), (3, 1.2)])
def test_report_tolerance_matches_analytic_width(tolerance, expected):
    # If x of dong 0's three pooled ballots support candidate 1, the slope
    # is (3-2x)/5. Two allocations differ in slope by 2*|x-x'|/5.
    actual = reporting.wmax(example(), np.array([-1.0, 1.0]), 1.0, 1.0, 'P2b', tolerance)
    assert actual == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize('threshold', [1, 2, 3, 4])
def test_primary_suppression_bound_covers_every_integer_report(threshold):
    groups = {}
    for x in range(4):
        counts = (3-x, x, x, 3-x)
        report = tuple(value if value >= threshold else None for value in counts)
        groups.setdefault(report, []).append((3-2*x)/5)
    true_worst_width = max(max(values)-min(values) for values in groups.values())
    outer = reporting.wmax(example(), np.array([-1.0, 1.0]), 1.0, 1.0, 'P2b', threshold-1)
    assert outer >= true_worst_width - 1e-9
    if threshold == 3:
        # The relaxation is deliberately conservative, not claimed sharp.
        assert outer > true_worst_width + 0.1


@pytest.mark.parametrize('tolerance', [-1, float('inf'), float('nan')])
def test_invalid_report_tolerance_rejected(tolerance):
    with pytest.raises(ValueError, match='finite and non-negative'):
        reporting.wmax(example(), np.array([-1.0, 1.0]), 1.0, 1.0, 'P2b', tolerance)
