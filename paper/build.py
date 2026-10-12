"""Build the manuscript and online appendix.

  python paper/build.py            # PDF (XeLaTeX) + DOCX for manuscript and appendix, and a word count

Markers in the Markdown sources:
  <!-- table: name -->   replaced by paper/tables/name.tex (PDF) or paper/tables/name.md (DOCX)
Tables and figures are generated from results/ by analysis/output/build_tables.py and analysis/output/make_figures.py."""
import re
import subprocess
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
TAB = P / "tables"; OUT = P / "build"; OUT.mkdir(exist_ok=True)


def inject(text, target, barrier=False):
    """barrier: flush floats after every table, so that floating tables and longtables keep their source order and no
    table drifts into a later section (used for the Online Appendix, where tables follow one another)."""
    def rep(m):
        name = m.group(1).strip()
        f = TAB / f"{name}.{'tex' if target == 'pdf' else 'md'}"
        if not f.exists(): sys.exit(f"missing table {f}")
        body = f.read_text() + ("\\FloatBarrier\n" if barrier else "")
        return f"\n```{{=latex}}\n{body}\n```\n" if target == "pdf" else f"\n{body}\n"
    return re.sub(r"<!--\s*table:\s*([\w\-]+)\s*-->", rep, text)


def wordcount(md):
    """Approximate JJPS count: text, table cells, figure captions, notes and references (math as one token each)."""
    t = re.sub(r"\$\$.*?\$\$", " M ", md, flags=re.S)
    t = re.sub(r"\$[^$]*\$", " M ", t)
    t = re.sub(r"```\{=latex\}.*?```", " ", t, flags=re.S)
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r" \1 ", t)        # keep figure captions
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"^Table: ", "", t, flags=re.M)               # table caption marker
    t = re.sub(r"\\[a-zA-Z]+|[{}|*_#>\-]{1,}", " ", t)
    return len(re.findall(r"[A-Za-z0-9\u00C0-\uFFFF][\w'’\-.,%]*", t))


def build(name, meta):
    src = (P / f"{name}.md").read_text()
    pdf_md = inject(src, "pdf", barrier=(name == "appendix"))
    docx_md = re.sub(r"\(figures/([\w\-]+)\.pdf\)", r"(figures/\1.png)", inject(src, "docx"))   # Word cannot display embedded PDFs
    k = iter(range(1, 1000))                         # pandoc does not number Word figure captions; LaTeX does
    docx_md = re.sub(r"^!\[", lambda m: f"![Figure {next(k)}. ", docx_md, flags=re.M)
    (OUT / f"{name}_pdf.md").write_text(pdf_md); (OUT / f"{name}_docx.md").write_text(docx_md)
    common = ["-f", "markdown+tex_math_dollars+footnotes+raw_tex+raw_attribute+implicit_figures", "--resource-path", str(P)]
    subprocess.run(["pandoc", str(OUT / f"{name}_pdf.md"), *common, "-o", str(OUT / f"{name}.pdf"), "--pdf-engine=xelatex",
                    "-H", str(P / "templates/header.tex"), "-V", "geometry:a4paper,margin=25mm", "-V", "fontsize=11pt",
                    "-V", "documentclass=article", "-V", "colorlinks=true", *meta], check=True, cwd=P)
    subprocess.run(["pandoc", str(OUT / f"{name}_docx.md"), *common, "-o", str(OUT / f"{name}.docx"),
                    "--reference-doc", str(P / "templates/reference.docx"), *meta], check=True, cwd=P)
    tables = "".join((TAB / f"{m}.md").read_text() for m in re.findall(r"<!--\s*table:\s*([\w\-]+)\s*-->", src))
    n = wordcount(src + tables)
    print(f"{name}: {n} words (text + tables + notes + references; approximate)")
    return n


def provenance(counts):
    """Record which commit, tools and inputs produced the files in paper/build/."""
    import datetime, platform, hashlib
    run = lambda *a: subprocess.run(a, capture_output=True, text=True, cwd=P.parent).stdout.strip()
    dirty = run("git", "status", "--porcelain", "--", "vwn", "analysis", "results", "data", "paper/manuscript.md", "paper/appendix.md")
    res = sorted((P.parent / "results").glob("*.csv"))
    h = hashlib.sha256(b"".join(f.read_bytes() for f in res)).hexdigest()[:16]
    lines = [f"built: {datetime.datetime.now().isoformat(timespec='seconds')}",
             f"commit: {run('git', 'rev-parse', 'HEAD')}" + (" (uncommitted changes in sources)" if dirty else ""),
             f"python: {platform.python_version()}; pandoc: {run('pandoc', '--version').splitlines()[0]}",
             f"results: {len(res)} csv files, sha256 prefix {h}"] + [f"words, {k}: {v}" for k, v in counts.items()]
    (OUT / "BUILD_INFO.txt").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    provenance({"manuscript": build("manuscript", []), "appendix": build("appendix", [])})
