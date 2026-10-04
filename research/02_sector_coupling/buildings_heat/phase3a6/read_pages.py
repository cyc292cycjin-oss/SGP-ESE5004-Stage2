"""Read explicit PDF pages with bounded text output (one-based physical PDF pages)."""
from pathlib import Path
from pypdf import PdfReader
import sys
sys.stdout.reconfigure(encoding='utf8')
p=Path(sys.argv[1]);d=PdfReader(p)
for n in map(int,sys.argv[2:]):
    print(f'\nFILE={p.name} PDF_PAGE={n}\n'+d.pages[n-1].extract_text())
