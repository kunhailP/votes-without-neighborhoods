"""Repository paths. Inputs live in data/ (raw sources in data/raw/), computed inputs in data/derived/,
every computed result in results/, and paper tables and figures in paper/."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
DERIVED = DATA / "derived"
RES = ROOT / "results"
FIG = ROOT / "paper" / "figures"
TAB = ROOT / "paper" / "tables"
for _p in (DERIVED, RES, FIG, TAB):
    _p.mkdir(parents=True, exist_ok=True)
