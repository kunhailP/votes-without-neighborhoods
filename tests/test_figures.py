"""A failed figure must stop the build before stale artwork reaches a paper."""
import pytest
from analysis.output import make_figures


def test_missing_result_stops_figure_build(monkeypatch):
    called = []
    def missing_result():
        raise FileNotFoundError('missing slope results')
    monkeypatch.setattr(make_figures, 'fig_flow', lambda: called.append('flow'))
    monkeypatch.setattr(make_figures, 'fig_ladder', missing_result)
    monkeypatch.setattr(make_figures, 'fig_map', lambda: called.append('map'))
    with pytest.raises(FileNotFoundError, match='missing slope results'):
        make_figures.build_figures()
    assert called == ['flow']
