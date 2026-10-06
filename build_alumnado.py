#!/usr/bin/env python3
"""Genera alumnado/index.html a partir de index.html (profesorado).

Uso:  python3 build_alumnado.py

Se edita SOLO index.html; después se ejecuta este script. La versión de alumnado
no solo oculta lo docente: lo ELIMINA del fichero (no queda en el código fuente).

Qué se elimina:
- Datos: soluciones (sols), prácticas de aula de Moodle (prac), resumen operativo
  (resumen), «claves» de los resúmenes por unidad, correcciones (fixes) y notas
  docentes (q) de las actividades, y el desarrollo detallado de las unidades no publicadas
  (ver PUBLICADAS). Las actividades y tareas de esas unidades se listan en el menú
  con enlace, pero su contenido se muestra como «no publicado».
- Motor JS: todas las ramas D.role==='profe' (notas «profe», secciones «Uso
  indebido de la IA» y «Resumen operativo», enlaces del menú a ellas).
- Cabecera: verja de contraseña, título y rótulos de profesorado.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC, DST = ROOT / "index.html", ROOT / "alumnado" / "index.html"
PUBLICADAS = ["ud1"]          # unidades cuyo desarrollo detallado ve el alumnado
ROLE = "D.role==='profe'"


# ---------------------------------------------------------------- utilidades JS
def skip_string(s, i):
    q = s[i]; i += 1
    while s[i] != q:
        i += 2 if s[i] == "\\" else 1
    return i + 1

def match(s, i):
    """Índice del cierre que empareja el ( [ { de s[i], saltando literales de cadena."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack = []
    while True:
        c = s[i]
        if c in "'\"`":
            i = skip_string(s, i); continue
        if c in pairs:
            stack.append(pairs[c])
        elif stack and c == stack[-1]:
            stack.pop()
            if not stack:
                return i
        i += 1

def stmt_end(s, i):
    """Índice del ';' que cierra la sentencia que empieza en i (profundidad 0)."""
    while True:
        c = s[i]
        if c in "'\"`":
            i = skip_string(s, i); continue
        if c in "([{":
            i = match(s, i) + 1; continue
        if c == ";":
            return i
        i += 1

def strip_profe(eng):
    n = 0
    while True:
        k = eng.find(ROLE)
        if k < 0:
            return eng, n
        n += 1
        if eng.startswith("(" + ROLE + "?", k - 1):                 # (D.role==='profe'?A:B)
            p = k - 1; eng = eng[:p] + "''" + eng[match(eng, p) + 1:]
        elif eng.startswith("((" + ROLE + "&&", k - 2):             # ((D.role==='profe'&&x)?A:B)
            p = k - 2; eng = eng[:p] + "''" + eng[match(eng, p) + 1:]
        elif eng.startswith("=(" + ROLE + "&&", k - 2):             # var x=(D.role==='profe'&&y)?A:B;
            p = k - 1; eng = eng[:p] + "''" + eng[stmt_end(eng, p):]
        elif eng.startswith("if(PR&&" + ROLE + "){", k - 7):        # if(PR&&D.role==='profe'){...}
            p = k - 7; b = eng.index("{", p); eng = eng[:p] + eng[match(eng, b) + 1:]
        elif eng.startswith("if(" + ROLE + "){", k - 3):            # if(D.role==='profe'){...}
            p = k - 3; b = eng.index("{", p); eng = eng[:p] + eng[match(eng, b) + 1:]
        else:
            sys.exit("Patrón D.role==='profe' no previsto:\n" + eng[k - 120:k + 160])

def stub_function(eng, name):
    k = eng.find("function " + name + "(")
    if k < 0:
        return eng
    b = eng.index("{", k)
    return eng[:b] + "{return el('div');}" + eng[match(eng, b) + 1:]


# ---------------------------------------------------------------- construcción
s = SRC.read_text(encoding="utf-8")

# 1) cabecera
s, n = re.subn(r"\s*<script>\s*// Reemplaza.*?</script>", "", s, count=1, flags=re.S)
assert n == 1, "no se encontró la verja de contraseña"
for old, new in [
    ("<title>MP5021 · Incidentes de Ciberseguridad (profesorado)</title>", "<title>MP5021 · Incidentes de Ciberseguridad</title>"),
    ('<body data-role="profe">', '<body data-role="alumno">'),
    ("<b>MP5021 · Profesorado</b>", "<b>MP5021 · Incidentes CIB</b>"),
    ("Versión <b>Profesorado</b>", "Versión <b>Alumnado</b>"),
]:
    assert s.count(old) == 1, old
    s = s.replace(old, new)

# 2) datos
j = s.find("window.DATA=") + len("window.DATA=")
D, end = json.JSONDecoder().raw_decode(s[j:])
head, eng = s[:j], s[j + end:]

# quitar de alumnado el bloque «Incidentes reales provocados por IA» (catálogo,
# mapa por unidad y actividades sugeridas) del motor; en profesorado se conserva
_a = eng.find('+"<h3 id=\\"incidentes-ia')
_marker = '(repertorio para ampliar)</a>.</p>"'
_b = eng.find(_marker)
assert _a != -1 and _b != -1, "no se localizó el bloque incidentes-ia"
eng = eng[:_a] + eng[_b + len(_marker):]        # conserva el ';' que cierra la sentencia
D["role"] = "alumno"
for k in ("sols", "prac", "resumen"):
    D.pop(k, None)
for r in D.get("resumenes", {}).values():
    r.pop("claves", None)
for u in D["units"]:
    for a in u["acts"]:
        a.pop("fixes", None); a.pop("q", None)
D["detalle"] = {k: v for k, v in D.get("detalle", {}).items() if k in PUBLICADAS}
D["publicadas"] = PUBLICADAS              # el motor oculta el contenido de actividades/tareas
                                          # de las unidades no publicadas (pero las deja listadas)

# quitar de alumnado la teoría «Incidentes reales con IA» repartida por unidad
for u in D["units"]:
    teo = u.get("teoria", [])
    keep_idx = [i for i, t in enumerate(teo) if "Incidentes reales con IA" not in t.get("h", "")]
    if len(keep_idx) != len(teo):
        u["teoria"] = [teo[i] for i in keep_idx]
        r = D.get("resumenes", {}).get(u["id"])
        if r and isinstance(r.get("teoria"), list) and len(r["teoria"]) == len(teo):
            r["teoria"] = [r["teoria"][i] for i in keep_idx]

# 2b) quitar de alumnado el escenario de aula (Proxmox); se conserva solo el
# escenario local VirtualBox + Vagrant. En profesorado se mantiene Proxmox.
_f = D["lab"]["fuentes"][0]
_old = " En aula: plantilla Proxmox clonada por alumno/a."
assert _old in _f[1], "fuentes: no se halló la nota de Proxmox"
_f[1] = _f[1].replace(_old, "")

_vl_old = '<span class="c"># Casa: mismo plan de IPs que el aula (Proxmox). Red interna aislada.</span>'
_vl_new = '<span class="c"># Laboratorio local aislado: VirtualBox + Vagrant, red interna 172.21.10.0/24.</span>'
assert D["lab"]["vagrant"]["lines"].count(_vl_old) == 1, "vagrant.lines: comentario Proxmox no hallado"
D["lab"]["vagrant"]["lines"] = D["lab"]["vagrant"]["lines"].replace(_vl_old, _vl_new)

for _old, _new in [
    ('<div><b>Aula: Proxmox VE</b> (un segmento aislado por alumno/a) · <b>casa: VirtualBox + Vagrant</b> · red interna aislada ',
     '<div><b>Laboratorio: VirtualBox + Vagrant</b> · red interna aislada '),
    ('El escenario de aula corre sobre un <b>servidor Proxmox VE</b> con un <b>segmento por alumno/a</b> (VLAN, plantillas y clones enlazados); en casa el alumnado puede montar lo mismo con <b>VirtualBox + Vagrant</b>. Ambos comparten el direccionamiento <span class="mono ip">172.21.10.0/24</span>, así que los apuntes valen en los dos.</p>',
     'El escenario se monta con <b>VirtualBox + Vagrant</b> sobre una <b>red interna aislada</b> <span class="mono ip">172.21.10.0/24</span> que no sale al exterior, así que se puede reproducir en cualquier equipo.</p>'),
    ('de VirtualBox/Proxmox llamada', 'de VirtualBox llamada'),
]:
    assert eng.count(_old) == 1, "motor: fragmento Proxmox no hallado: " + _old[:50]
    eng = eng.replace(_old, _new)

# 3) motor
eng, n = strip_profe(eng)
for f in ("usoSection", "resumenSection", "solBlock"):
    eng = stub_function(eng, f)

out = head + json.dumps(D, ensure_ascii=False) + eng

# 4) comprobaciones: no debe quedar contenido docente
data_txt = json.dumps(D, ensure_ascii=False)
for needle in ["D.role==='profe'", '"sols"', '"prac"', '"fixes"', '"claves"', "Corregido respecto", "Notas para plantear",
               "Casos y cifras para ampliar", "Uso indebido de la IA", "Prácticas de aula", "Armando"]:
    assert needle not in out, "queda en alumnado: " + needle
assert "pbadge\">profe" not in out and "pbadge'>profe" not in out, "queda una marca 'profe'"
assert "Proxmox" not in out, "queda Proxmox en alumnado"

DST.write_text(out, encoding="utf-8")
print(f"alumnado/index.html generado · {n} ramas de profesorado eliminadas · "
      f"{len(out)//1024} KB (profesorado: {len(s)//1024} KB)")
