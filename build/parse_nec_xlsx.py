"""Parse NEC Election Statistics System xlsx "개표단위별 개표결과" (returns by counting unit) directly from the XML.
The files carry broken drawing references, so openpyxl cannot open them."""
import zipfile, re, sys, glob, unicodedata
import xml.etree.ElementTree as ET
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
def col2n(c):
    n = 0
    for ch in c: n = n * 26 + ord(ch) - 64
    return n - 1
def read_xlsx(path):
    z = zipfile.ZipFile(path); ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            ss.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    sheet = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/[Ss]heet\d+\.xml", n))[0]
    rows = []
    for row in ET.fromstring(z.read(sheet)).iter("{%s}row" % NS["m"]):
        cells = {}
        for c in row.findall("m:c", NS):
            ref = re.match(r"([A-Z]+)", c.get("r")).group(1); v = c.find("m:v", NS); t = c.get("t")
            if t == "inlineStr": val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
            elif v is None: val = None
            elif t == "s": val = ss[int(v.text)]
            else: val = v.text
            cells[col2n(ref)] = val
        if cells: rows.append([cells.get(i) for i in range(max(cells) + 1)])
    return rows
if __name__ == "__main__":
    for f in sorted(glob.glob(sys.argv[1] + "/*.xlsx")):
        rows = read_xlsx(f)
        title = " ".join(str(c) for r in rows[:5] for c in r if c)[:110]
        dongs = [r[0] for r in rows if len(r) > 1 and r[0] and r[1] == "계"][:2]
        print(unicodedata.normalize("NFC", f)[-14:], "|", title, "|", dongs, len(rows))
