#!/usr/bin/env python3
"""Inserta (o actualiza) una sección en detalle[unidad] de una copia de la web, detrás de otra.
Uso: python3 insertar_seccion.py <index.html> <ud> "<título nuevo>" <fichero.html> "<título anterior>"
"""
import json, sys
from pathlib import Path
f, ud, titulo, src, tras = sys.argv[1:6]
p = Path(f); s = p.read_text(encoding="utf-8")
j = s.find("window.DATA=") + len("window.DATA=")
D, e = json.JSONDecoder().raw_decode(s[j:])
secs = D["detalle"][ud]
html = Path(src).read_text(encoding="utf-8").strip()
nuevo = {"h": titulo, "html": html}
ya = [i for i, x in enumerate(secs) if x["h"] == titulo]
if ya:
    secs[ya[0]] = nuevo
else:
    k = [i for i, x in enumerate(secs) if x["h"] == tras][0]
    secs.insert(k + 1, nuevo)
p.write_text(s[:j] + json.dumps(D, ensure_ascii=False) + s[j + e:], encoding="utf-8")
print(f"{p}: {ud} → {len(secs)} secciones")
