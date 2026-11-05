"""V4 W11: the APEC Energy Statistics 2022 table 'Average net calorific values of energy products for 2022' (PDF p.197, printed 183) has no text
layer; this writes the embedded image (/Image18, FlateDecode RGB + SMask) composited over white as PNG files for reading:
extracted/apec_img/apec2022_p197_{full,top,bottom}.png. Pure Python PNG writer (no Pillow on this machine). Not committed (third-party content).

    %USERPROFILE%/miniconda3/python.exe -I scripts/v4ncv_apec_image.py --work <work dir>
"""
from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

from pypdf import PdfReader

PDF = "D:/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102/01_industry/225_ewg_apec-energy-statistics-2022.pdf"


def chunk(t: bytes, d: bytes) -> bytes:
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)


def save(path: Path, data: bytes, w: int, x0: int, x1: int, y0: int, y1: int) -> None:
    rows = b"".join(b"\x00" + bytes(data[(y * w + x0) * 3:(y * w + x1) * 3]) for y in range(y0, y1))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", x1 - x0, y1 - y0, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))
    path.write_bytes(png)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    o = PdfReader(PDF).pages[196]["/Resources"]["/XObject"].get_object()["/Image18"].get_object()
    w, h = int(o["/Width"]), int(o["/Height"])
    rgb, al = o.get_data(), o["/SMask"].get_object().get_data()
    out = bytearray(w * h * 3)
    for i in range(w * h):
        for c in range(3):
            out[3 * i + c] = (rgb[3 * i + c] * al[i] + 255 * (255 - al[i])) // 255
    d = a.work / "extracted/apec_img"
    d.mkdir(parents=True, exist_ok=True)
    save(d / "apec2022_p197_full.png", out, w, 0, w, 0, h)
    save(d / "apec2022_p197_top.png", out, w, 0, w, 0, 700)
    save(d / "apec2022_p197_bottom.png", out, w, 0, w, 650, h)
    print("written", w, h)


if __name__ == "__main__":
    main()
