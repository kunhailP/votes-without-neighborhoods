"""Anonymized copy of the committed files for double-blind review: python paper/review_package.py OUT.zip

Starts from `git archive HEAD` (so only committed files, and none marked export-ignore in .gitattributes), then removes what links the copy to the public repository: the commit id that git writes as the ZIP
comment and the commit line of paper/build/BUILD_INFO.txt (the hash of results/ is kept, so the copy can still be checked
against the paper)."""
import io
import subprocess
import sys
import zipfile

out = sys.argv[1]
if subprocess.run(["git", "diff", "--quiet", "HEAD"]).returncode:
    sys.exit("commit first: the package is built from HEAD")
raw = subprocess.run(["git", "archive", "--format=zip", "--prefix=replication/", "HEAD"], capture_output=True, check=True).stdout
src = zipfile.ZipFile(io.BytesIO(raw))
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
    for info in src.infolist():
        data = src.read(info)
        if info.filename.endswith("paper/build/BUILD_INFO.txt"):
            data = b"".join(l for l in data.splitlines(True) if not l.startswith(b"commit:"))
        info.comment = b""
        dst.writestr(info, data)
    dst.comment = b""
print(f"wrote {out} ({len(src.infolist())} entries); commit ids removed")
