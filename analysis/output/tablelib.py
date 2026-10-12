"""Formatting helpers: every table is written twice, as LaTeX (PDF) and as Markdown (DOCX, GitHub)."""
import math
import re
import numpy as np
from vwn.paths import TAB

MINUS = "−"


def num(v, d=3, signed=False):
    if v is None or (isinstance(v, float) and (math.isnan(v))): return "–"
    if isinstance(v, str): return v
    if math.isinf(v): return "∞"
    s = f"{v:+.{d}f}" if signed else f"{v:.{d}f}"
    if float(s) == 0: s = s.replace("-", "")
    return s.replace("-", MINUS)


def iv(lo, hi, d=3):
    """Interval; marked (as bold) when it contains zero."""
    if lo is None or hi is None or (isinstance(lo, float) and math.isnan(lo)): return "–"
    s = f"[{num(lo, d)}, {num(hi, d)}]"
    return ("**" + s + "**") if lo <= 0 <= hi else s


def bp(lo, cap=None, d=3, any_label="any"):
    """Breakdown point (lower end of the bisection interval)."""
    if lo is None or (isinstance(lo, float) and math.isnan(lo)): return "–"
    if math.isinf(lo) or (cap is not None and lo >= cap - 1e-9): return any_label
    if lo == 0: return "0"
    return num(lo, d)


GREEK = {"δ": r"\delta", "η": r"\eta", "λ": r"\lambda", "π": r"\pi", "Δ": r"\Delta", "θ": r"\theta", "ρ": r"\rho", "β": r"\beta",
         "γ": r"\gamma", "κ": r"\kappa", "Σ": r"\Sigma", "ω": r"\omega"}
SYM = {"≥": r"\geq", "≤": r"\leq", "×": r"\times", "∞": r"\infty", "x̄": r"\bar x", "ā": r"\bar a", "x̃": r"\tilde x", "±": r"\pm"}


def _math(tok):
    for a, b in {**SYM, **GREEK}.items(): tok = tok.replace(a, b + " " if b[-1].isalpha() else b)
    tok = re.sub(r"\^([A-Za-z0-9]+)", r"^{\1}", tok)
    tok = re.sub(r"_([A-Za-z0-9]+(?:,[A-Za-z0-9]+)?)", lambda m: "_{" + m.group(1) + "}", tok)
    tok = tok.replace("_{min,g}", r"_{\min,g}").replace("_{min}", r"_{\min}")
    return "$" + tok.replace(MINUS, "-") + "$"


TOKEN = re.compile(r"(?:[A-Za-zδηλπΔθρβγκΣωāx̄x̃]|x̄|x̃|ā)+(?:[\^_][A-Za-z0-9ρ]+(?:,[A-Za-z0-9]+)?)+|[δηλπΔθρβγκΣω≥≤×∞±]|x̄|x̃|ā")


def _plain(p):
    """Escape text outside math and wrap symbol tokens as inline math."""
    out = []; pos = 0
    for m in TOKEN.finditer(p):
        out.append(_esc(p[pos:m.start()])); out.append(_math(m.group(0))); pos = m.end()
    out.append(_esc(p[pos:]))
    return "".join(out)


def _esc(t):
    for a, b in {"\\": r"\textbackslash{}", "%": r"\%", "&": r"\&", "#": r"\#", "_": r"\_", "^": r"\^{}", "–": "--"}.items(): t = t.replace(a, b)
    return t.replace(MINUS, "$-$")


def _tex_cell(s):
    s = str(s); out = []
    for k, part in enumerate(s.split("**")):
        segs = part.split("$"); conv = []
        for i, seg in enumerate(segs):
            conv.append(("$" + seg.replace(MINUS, "-") + "$") if i % 2 == 1 else _plain(seg))
        t = "".join(conv)
        out.append(r"\textbf{" + t + "}" if k % 2 == 1 else t)
    return "".join(out)


GU_ROMAN = {"종로구": "Jongno-gu", "중구": "Jung-gu", "용산구": "Yongsan-gu", "성동구": "Seongdong-gu", "광진구": "Gwangjin-gu",
            "동대문구": "Dongdaemun-gu", "중랑구": "Jungnang-gu", "성북구": "Seongbuk-gu", "강북구": "Gangbuk-gu", "도봉구": "Dobong-gu",
            "노원구": "Nowon-gu", "은평구": "Eunpyeong-gu", "서대문구": "Seodaemun-gu", "마포구": "Mapo-gu", "양천구": "Yangcheon-gu",
            "강서구": "Gangseo-gu", "구로구": "Guro-gu", "금천구": "Geumcheon-gu", "영등포구": "Yeongdeungpo-gu", "동작구": "Dongjak-gu",
            "관악구": "Gwanak-gu", "서초구": "Seocho-gu", "강남구": "Gangnam-gu", "송파구": "Songpa-gu", "강동구": "Gangdong-gu"}
ROMAN = [("강남·서초·송파", "Gangnam, Seocho and Songpa"), ("강남, 서초 and 송파", "Gangnam, Seocho and Songpa")] + \
        sorted(GU_ROMAN.items(), key=lambda kv: -len(kv[0])) + [("강남", "Gangnam"), ("서초", "Seocho"), ("송파", "Songpa")]


def romanize(x):
    """English-language tables: Seoul district names in Revised Romanization."""
    if not isinstance(x, str): return x
    for k, v in ROMAN: x = x.replace(k, v)
    return x


TERMS = [("residents' early ballots resemble their neighborhood", "residents' early-vote composition restricted"),
         ("expensive minus cheaper half of neighborhoods", "higher- minus lower-price groups"),
         ("expensive-minus-cheaper contrast", "higher-minus-lower-price contrast"),
         ("Expensive minus cheaper half", "Higher- minus lower-price half"),
         ("city-wide", "citywide"), ("City-wide", "Citywide"), ("Within-gu", "Within-district"), ("within-gu", "within-district"),
         ("gu council", "district-council")]


# 관내/관외 early voting is defined by the statutory early-voting zone, which is the gu only in some elections; the display
# text therefore says in-zone/out-of-zone (the lookbehind keeps "within-district", which refers to the gu)
ZONE_TERMS = [(r"(?<![A-Za-z])In-district", "In-zone"), (r"(?<![A-Za-z])in-district", "in-zone"),
              (r"(?<![A-Za-z])Out-of-district", "Out-of-zone"), (r"(?<![A-Za-z])out-of-district", "out-of-zone"),
              (r"in-zone zone", "early-voting zone")]   # "in-district zone(s)" in the generators names the zone itself


def terms(x):
    """Display terminology used in the text (input keys such as guFE and raw dong names are untouched)."""
    if not isinstance(x, str): return x
    for k, v in TERMS: x = x.replace(k, v)
    for k, v in ZONE_TERMS: x = re.sub(k, v, x)
    return x


def emit(name, title, header, rows, notes="", colspec=None, size="footnotesize", long=False, panels=None, landscape=False):
    """Write paper/tables/<name>.tex and .md.

    rows: list of lists of strings; a row given as ("PANEL", text) starts a panel heading."""
    title, notes, header = romanize(title), romanize(notes), [romanize(h) for h in header]
    rows = [(r[0], romanize(r[1])) if isinstance(r, tuple) and r[0] == "PANEL" else [romanize(c) for c in r] for r in rows]
    title, notes, header = terms(title), terms(notes), [terms(h) for h in header]
    rows = [(r[0], terms(r[1])) if isinstance(r, tuple) and r[0] == "PANEL" else [terms(c) for c in r] for r in rows]
    ncol = len(header)
    colspec = colspec or ("l" + ("c" if long else "C") * (ncol - 1))
    # Markdown
    # a literal | would split the Markdown column; a lone * (t*, s*, δ*) would open an emphasis span, while the
    # **bold** pairs the generators use on purpose are kept
    esc = lambda c: re.sub(r"(?<!\*)\*(?!\*)", r"\\*", str(c).replace("|", "\\|"))
    body = [[esc(c) for c in r] if not (isinstance(r, tuple) and r[0] == "PANEL") else r for r in rows]
    # relative column widths for Word, from the longest cell (capped) and the longest header word
    # (at least the longest header word and 10 characters; the first column also holds the panel headings)
    width = [max([10, max((len(w) for w in str(h).split()), default=0) + 1]
                 + [min(len(str(r[i])), 40) + 1 for r in body if not isinstance(r, tuple) and i < len(r)]
                 + ([min(len(str(r[1])), 16) for r in body if isinstance(r, tuple)] if i == 0 else []))
             for i, h in enumerate(header)]
    # "Table:" makes the title a table caption (kept with its table in Word), not a free paragraph
    md = [f"Table: {esc(title)}", "", "| " + " | ".join(esc(h) for h in header) + " |",
          "|" + "|".join("-" * max(3, w) for w in width) + "|"]
    for r in body:
        if isinstance(r, tuple): md.append("| *" + esc(r[1]) + "* |" + " |" * (ncol - 1))
        else: md.append("| " + " | ".join(r) + " |")
    if notes: md += ["", f"*Notes.* {esc(notes)}"]
    (TAB / f"{name}.md").write_text("\n".join(md) + "\n")
    # LaTeX
    head = " & ".join(_tex_cell(h) for h in header) + r" \\"
    if long:   # longtable cannot use X columns: give every column a wrapping paragraph width
        nl = sum(1 for ch in colspec if ch == "l"); nc = sum(1 for ch in colspec if ch in "cC")
        wl = min(0.2, 0.9 / max(len(colspec), 1) * 1.4); wc = (0.97 - wl * nl) / max(nc, 1)
        # widths are shares of the line minus the inter-column padding (2\tabcolsep per column), so the table never exceeds the margin
        w = lambda f: r"\dimexpr %.3f\linewidth-2\tabcolsep\relax" % f
        colspec = "".join(r">{\raggedright\arraybackslash}p{%s}" % w(wl) if ch == "l" else r">{\centering\arraybackslash}p{%s}" % w(wc) for ch in colspec)
    body = []
    for r in rows:
        if isinstance(r, tuple) and r[0] == "PANEL":
            body.append(r"\addlinespace[3pt]\multicolumn{%d}{l}{\textit{%s}} \\" % (ncol, _tex_cell(r[1])))
        else:
            body.append(" & ".join(_tex_cell(c) for c in r) + r" \\")
    t = title.split(". ", 1)
    cap = r"\textbf{" + _tex_cell(t[0]) + ".} " + (_tex_cell(t[1]) if len(t) > 1 else "")
    note_size = "scriptsize" if size in ("scriptsize", "tiny") else "footnotesize"   # notes no smaller than the table body
    note_tex = (r"\par\vspace{2pt}{\raggedright\%s\textit{Notes.} " % note_size + _tex_cell(notes) + r"\par}") if notes else ""
    if long:
        tex = [r"{\%s" % size, r"\setlength{\tabcolsep}{3.5pt}", r"\begin{longtable}{%s}" % colspec, r"\caption*{%s}\\" % cap, r"\toprule", head, r"\midrule\endfirsthead",
               r"\toprule", head, r"\midrule\endhead", r"\bottomrule\endfoot"] + body + [r"\end{longtable}", note_tex, "}"]
    else:
        tex = [r"\begin{table}[!htbp]", r"\centering", r"\%s" % size, r"\setlength{\tabcolsep}{3.5pt}", r"\caption*{%s}" % cap,
               r"\begin{tabularx}{\linewidth}{%s}" % colspec, r"\toprule", head, r"\midrule"] + body + [r"\bottomrule", r"\end{tabularx}", note_tex, r"\end{table}"]
    (TAB / f"{name}.tex").write_text("\n".join(tex) + "\n")
