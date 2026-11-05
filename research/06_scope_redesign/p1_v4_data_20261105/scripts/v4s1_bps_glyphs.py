"""V4 S1 section 4.1 (step 2): glyph-level text of the BPS IBS 2019 table pages and tokens with positions.

    %USERPROFILE%/miniconda3/python.exe -I scripts/v4s1_bps_glyphs.py --work <work dir> [--pages 109-152]

The printed page is a Form XObject (/TPLn) of simple TrueType fonts with ToUnicode maps. pypdf's text extraction joins a row into one
run and turns kerning gaps into spaces ("9 798 41 8"), and some rows are drawn twice with a 0.12 pt offset (simulated bold), so a
table cannot be split reliably from the text. Here the content stream of the form is interpreted directly (q/Q, cm, BT/ET, Tf, Tm,
Td, TD, T*, TL, Tc, Tw, Tz, TJ, Tj, ', ") and every glyph gets its user-space box from the font widths. Then:
  * duplicates (same character within 0.6 pt in x and y) are dropped (simulated bold);
  * glyphs are grouped into lines (|dy| <= 2 pt) and, inside a line, into tokens: a new token starts where the gap between two
    non-space glyphs exceeds GAP_PT (thousands separators and kerning gaps are about 1.6-2.3 pt; column gaps are >= 5 pt);
Output extracted/12_bps_indonesia/bps_tokens/pNNN.csv: line_y, x0, x1, font, text (spaces removed inside numeric tokens are kept in
raw_text). Column assignment, number parsing and the reconciliation against printed totals are in v4s1_bps_parse.py (WSL).
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from pypdf import PdfReader
from pypdf.generic import ContentStream

PDF = "downloads/12_bps_indonesia/BPS0000-statistik_industri_manufaktur_indonesia_2019.pdf"
GAP_PT = 3.5
DUP_PT = 0.6


def mat(a, b):
    """Product a x b of PDF matrices [a b c d e f] (row-vector convention)."""
    return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3], a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
            a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]


def apply(m, x, y):
    return x * m[0] + y * m[2] + m[4], x * m[1] + y * m[3] + m[5]


def tounicode(font) -> dict:
    tu = font.get("/ToUnicode")
    out = {}
    if not tu:
        return out
    s = tu.get_object().get_data().decode("latin-1")
    for blk in re.findall(r"beginbfchar(.*?)endbfchar", s, re.S):
        for src, dst in re.findall(r"<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>", blk):
            out[int(src, 16)] = bytes.fromhex(dst).decode("utf-16-be", errors="replace")
    for blk in re.findall(r"beginbfrange(.*?)endbfrange", s, re.S):
        for lo, hi, dst in re.findall(r"<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>", blk):
            lo, hi, d = int(lo, 16), int(hi, 16), int(dst, 16)
            for k in range(lo, hi + 1):
                out[k] = chr(d + k - lo)
    return out


class Font:
    def __init__(self, f):
        f = f.get_object()
        self.name = str(f.get("/BaseFont", ""))
        self.fc = int(f.get("/FirstChar", 0))
        self.w = [float(x) for x in f.get("/Widths", [])]
        fd = f.get("/FontDescriptor")
        self.mw = float(fd.get_object().get("/MissingWidth", 0)) if fd else 0.0
        self.map = tounicode(f)

    def width(self, code):
        i = code - self.fc
        return (self.w[i] if 0 <= i < len(self.w) else self.mw) / 1000.0


def glyphs_of_form(form, reader):
    res = form.get("/Resources", {})
    fonts = {k: Font(v) for k, v in (res.get("/Font", {}) or {}).items()}
    fm = [float(x) for x in form.get("/Matrix", [1, 0, 0, 1, 0, 0])]
    ctm, stack = fm[:], []
    tm = tlm = [1, 0, 0, 1, 0, 0]
    font, size, tc, tw, tz, tl, out = None, 0.0, 0.0, 0.0, 1.0, 0.0, []

    def show(s):
        nonlocal tm
        if hasattr(s, "original_bytes"):   # TextStringObject: pypdf decoded it with PDFDocEncoding; codes 0x18-0x1f do not round-trip
            s = s.original_bytes
        for b in (s if isinstance(s, (bytes, bytearray)) else s.encode("latin-1", errors="replace")):
            w = font.width(b) if font else 0.0
            ch = font.map.get(b, "?") if font else "?"
            trm = mat(tm, ctm)
            x0, y0 = apply(trm, 0, 0)
            x1, _ = apply(trm, w * size, 0)
            out.append((ch, x0, x1, y0, font.name if font else "", size * trm[3] / (tm[3] or 1.0)))
            tx = (w * size + tc + (tw if b == 32 else 0.0)) * tz
            tm = mat([1, 0, 0, 1, tx, 0], tm)

    for operands, op in ContentStream(form, reader).operations:
        op = op.decode() if isinstance(op, bytes) else op
        if op == "q":
            stack.append(ctm[:])
        elif op == "Q":
            ctm = stack.pop() if stack else fm[:]
        elif op == "cm":
            ctm = mat([float(x) for x in operands], ctm)
        elif op == "BT":
            tm = tlm = [1, 0, 0, 1, 0, 0]
        elif op == "Tf":
            font = fonts.get(operands[0]); size = float(operands[1])
        elif op == "Tm":
            tm = tlm = [float(x) for x in operands]
        elif op in ("Td", "TD"):
            tx, ty = float(operands[0]), float(operands[1])
            if op == "TD":
                tl = -ty
            tlm = mat([1, 0, 0, 1, tx, ty], tlm); tm = tlm[:]
        elif op == "T*":
            tlm = mat([1, 0, 0, 1, 0, -tl], tlm); tm = tlm[:]
        elif op == "TL":
            tl = float(operands[0])
        elif op == "Tc":
            tc = float(operands[0])
        elif op == "Tw":
            tw = float(operands[0])
        elif op == "Tz":
            tz = float(operands[0]) / 100.0
        elif op == "Tj":
            show(operands[0])
        elif op in ("'", '"'):
            if op == '"':
                tw, tc = float(operands[0]), float(operands[1])
            tlm = mat([1, 0, 0, 1, 0, -tl], tlm); tm = tlm[:]
            show(operands[-1])
        elif op == "TJ":
            for e in operands[0]:
                if isinstance(e, (bytes, bytearray)) or hasattr(e, "original_bytes"):
                    show(e.original_bytes if hasattr(e, "original_bytes") else e)
                else:
                    tm = mat([1, 0, 0, 1, -float(e) / 1000.0 * size * tz, 0], tm)
    return out


def tokens(gl):
    # drop simulated-bold duplicates
    keep, grid = [], {}
    for g in gl:
        gx, gy = int(g[1] // DUP_PT), int(g[3] // DUP_PT)
        near = [k for dx in (-1, 0, 1) for dy in (-1, 0, 1) for k in grid.get((g[0], gx + dx, gy + dy), [])]
        if any(abs(k[1] - g[1]) <= DUP_PT and abs(k[3] - g[3]) <= DUP_PT for k in near):
            continue
        keep.append(g); grid.setdefault((g[0], gx, gy), []).append(g)
    lines = []
    for g in sorted(keep, key=lambda t: -t[3]):
        if lines and abs(lines[-1][0] - g[3]) <= 2.0:
            lines[-1][1].append(g)
        else:
            lines.append([g[3], [g]])
    out = []
    for y, gs in lines:
        gs = sorted(gs, key=lambda t: t[1])
        cur, last_x1 = [], None
        for g in gs:
            if g[0] == " ":
                continue
            if cur and g[1] - last_x1 > GAP_PT:
                out.append((y, cur)); cur = []
            cur.append(g); last_x1 = g[2]
        if cur:
            out.append((y, cur))
    rows = []
    for y, cur in out:
        fonts = sorted({g[4] for g in cur})
        rows.append(dict(line_y=round(y, 2), x0=round(cur[0][1], 2), x1=round(cur[-1][2], 2), font=";".join(fonts),
                         size=round(cur[0][5], 2), text="".join(g[0] for g in cur)))
    return rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); ap.add_argument("--pages", default="109-152")
    a = ap.parse_args()
    r = PdfReader(str(a.work / PDF))
    out = a.work / "extracted/12_bps_indonesia/bps_tokens"; out.mkdir(parents=True, exist_ok=True)
    pages = []
    for part in a.pages.split(","):
        lo, _, hi = part.partition("-"); pages += list(range(int(lo), int(hi or lo) + 1))
    gaps = {}
    for p in pages:
        page = r.pages[p - 1]
        used = [u.decode() for u in re.findall(rb"/(TPL\d+) Do", page.get_contents().get_data())]
        gl = []
        for u in used:
            gl += glyphs_of_form(page["/Resources"]["/XObject"]["/" + u].get_object(), r)
        rows = tokens(gl)
        with (out / f"p{p:03d}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["line_y", "x0", "x1", "font", "size", "text"]); w.writeheader(); w.writerows(rows)
        gaps[p] = len(rows)
    print({k: v for k, v in list(gaps.items())[:6]}, "... pages", len(gaps))


if __name__ == "__main__":
    main()
