#!/usr/bin/env python3
"""Inserta/actualiza la sección «Recursos de ciberseguridad» en una web del módulo.

Uso:
    python3 sync_recursos.py                 # actualiza index.html (profesorado)
    python3 sync_recursos.py ruta/index.html # cualquier otra copia (p. ej. la réplica de mrnovoa-dev)

Fuente única: recursos.json (aquí se añaden los recursos nuevos; los que llevan
"alta" de los últimos 60 días salen marcados como «nuevo»). El script:
  1) escribe D.recursos dentro de window.DATA;
  2) la primera vez, añade al motor la función recursosSection(), su entrada en el
     menú lateral y el CSS (idempotente: si ya está, no lo duplica).
La sección es pública: build_alumnado.py la conserva en la versión de alumnado.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "index.html"
R = json.loads((ROOT / "recursos.json").read_text(encoding="utf-8"))

MARK = "function recursosSection("

CSS = """
/* --- recursos --- */
.recctl{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:12px}
#recQ{flex:1 1 240px;font:14px var(--sans);padding:7px 14px;border:1px solid var(--border);border-radius:99px;background:var(--surface);color:var(--ink)}
#recQ:focus{outline:2px solid var(--udc);outline-offset:1px}
.rcfs{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.rcf{font:600 12px var(--sans);color:var(--muted);background:var(--surface);border:1px solid var(--border);border-radius:99px;padding:4px 11px;cursor:pointer}
.rcf:hover{border-color:var(--udc);color:var(--udc)}.rcf.on{background:var(--udc);color:#fff;border-color:var(--udc)}
.rec-cnt{font:12px var(--sans);color:var(--muted)}
.rec-warn{font-size:13px;color:var(--muted);border-left:3px solid var(--attack);padding:4px 10px;margin-top:10px}
.rcgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px;margin-top:6px}
.rc{display:flex;flex-direction:column;gap:5px;padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface-2);color:var(--ink);text-decoration:none}
.rc:hover{border-color:var(--udc);transform:translateY(-1px)}
.rc-top{display:flex;gap:6px;align-items:center;font:600 10.5px var(--sans);color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.rc-new{background:var(--udc);color:#fff;border-radius:99px;padding:1px 7px;text-transform:none;letter-spacing:0}
.rc-n{font-size:14px;line-height:1.3}.rc-d{font-size:13px;color:var(--muted);line-height:1.45}
.rc-uds{display:flex;gap:4px;flex-wrap:wrap;margin-top:auto}.rc-ud{font:600 10.5px var(--sans);border:1px solid var(--border);border-radius:4px;padding:0 5px;color:var(--muted)}
.rc-or{font-size:12.5px;color:var(--muted);font-style:italic;margin:0 0 6px}
.rc-cd{font-size:13.5px;color:var(--muted);margin:0 0 8px}
.stars{color:var(--udc);letter-spacing:1px;white-space:nowrap}
.rec-hide{display:none!important}
.rec-profe{border-left-color:var(--attack)!important}
.ab-h .cnt{color:var(--muted);font-weight:500;font-size:.8em;margin-left:4px}
"""

ENGINE_FN = r"""function recursosSection(){var R=D.recursos,s=el('section','unit ampunit recunit');s.id='recursos';s.style.setProperty('--udc','var(--defend)');
 var TL={agencia:'Organismo',norma:'Normativa',marco:'Marco',herramienta:'Herramienta',repo:'Repositorio',web:'Web',plataforma:'Plataforma',curso:'Curso',cert:'Certificación',video:'Vídeo',evento:'Congreso',noticias:'Noticias',empresa:'Empresa'};
 var hoy=new Date();function esc(x){return String(x==null?'':x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');}
 function nuevo(it){if(!it.alta)return false;var d=(hoy-new Date(it.alta))/864e5;return d>=0&&d<=60;}
 function q(it){return esc([it.n,it.d,TL[it.t]||'',it.emisor||'',it.enfoque||'',(it.ud||[]).join(' ')].join(' ').toLowerCase());}
 function card(it){var uds=(it.ud||[]).map(function(u){return '<span class="rc-ud">'+u+'</span>';}).join('');
  return '<a class="rc rec-it" href="'+esc(it.u)+'" target="_blank" rel="noopener" data-t="'+it.t+'" data-q="'+q(it)+'"><span class="rc-top"><span>'+(TL[it.t]||it.t)+'</span><span>· '+it.l+'</span>'+(nuevo(it)?'<span class="rc-new">nuevo</span>':'')+'</span><b class="rc-n">'+esc(it.n)+'</b><span class="rc-d">'+esc(it.d)+'</span>'+(uds?'<span class="rc-uds">'+uds+'</span>':'')+'</a>';}
 function stars(n){var o='';for(var i=0;i<5;i++)o+=i<n?'★':'☆';return '<span class="stars" title="Encaje con MP5021: '+n+'/5">'+o+'</span>';}
 function tabla(c){var rows=c.items.map(function(it){return '<tr class="rec-it" data-t="'+it.t+'" data-q="'+q(it)+'"><td>'+stars(it.encaje)+'</td><td><a href="'+esc(it.u)+'" target="_blank" rel="noopener"><b>'+esc(it.n)+'</b></a>'+(nuevo(it)?' <span class="rc-new">nuevo</span>':'')+'<br><span class="rc-d">'+esc(it.emisor)+' · '+esc(it.nivel)+'</span></td><td>'+esc(it.enfoque)+'</td><td>'+esc(it.formato)+'</td><td>'+esc(it.precio)+'</td><td>'+esc(it.nota)+'</td><td style="text-align:center">'+(it.foto||'—')+'</td></tr>';}).join('');
  return '<div class="tbl-wrap"><table><thead><tr><th>Encaje</th><th>Certificación</th><th>Enfoque</th><th>Formato</th><th>Precio aprox.</th><th>Valoración para MP5021</th><th>Foto</th></tr></thead><tbody>'+rows+'</tbody></table></div>'+(c.ruta||'');}
 var tipos={};R.cats.forEach(function(c){c.items.forEach(function(it){tipos[it.t]=(tipos[it.t]||0)+1;});});
 var total=R.cats.reduce(function(a,c){return a+c.items.length;},0);
 var chips='<button type="button" class="rcf on" data-f="">Todos</button>'+Object.keys(TL).filter(function(k){return tipos[k];}).map(function(k){return '<button type="button" class="rcf" data-f="'+k+'">'+TL[k]+' <span class="cnt">'+tipos[k]+'</span></button>';}).join('');
 var blocks=R.cats.map(function(c){var body=(c.d?'<p class="rc-cd">'+c.d+'</p>':'')+(c.origen?'<p class="rc-or">'+esc(c.origen)+'</p>':'')+(c.tabla?tabla(c):'<div class="rcgrid">'+c.items.map(card).join('')+'</div>');
  return '<details class="ampblk'+(c.profe?' rec-profe':'')+'" id="recursos-'+c.id+'"><summary><span class="ab-h">'+c.h+' <span class="cnt">'+c.items.length+'</span></span><span class="chev">'+ICON.chev+'</span></summary><div class="ab-body">'+body+'</div></details>';}).join('');
 s.innerHTML='<div class="uhead"><div class="sec-head"><span class="tag" style="background:var(--defend)">REC</span><h2>Recursos de ciberseguridad</h2></div><p class="lead">'+R.intro+'</p><p class="sec-meta amp-src"><b>'+total+' recursos</b> en '+R.cats.length+' grupos · actualizado '+R.actualizado.split('-').reverse().join('/')+'</p>'
  +'<div class="recctl"><input id="recQ" type="search" placeholder="Buscar: wazuh, forense, gratis, UD3…" aria-label="Buscar recursos"><span class="rec-cnt" id="recCnt"></span><button type="button" class="ampall" data-act="open">Abrir todo</button><button type="button" class="ampall" data-act="close">Cerrar todo</button></div>'
  +'<div class="rcfs">'+chips+'</div><p class="rec-warn">'+R.aviso+'</p></div>'+blocks;
 var f='';function run(){var qq=(s.querySelector('#recQ').value||'').trim().toLowerCase(),n=0;
  s.querySelectorAll('.rec-it').forEach(function(e){var ok=(!f||e.getAttribute('data-t')===f)&&(!qq||e.getAttribute('data-q').indexOf(qq)>-1);e.classList.toggle('rec-hide',!ok);if(ok)n++;});
  s.querySelectorAll('details.ampblk').forEach(function(d){var v=d.querySelectorAll('.rec-it:not(.rec-hide)').length;d.classList.toggle('rec-hide',!v);if(qq||f)d.open=v>0;});
  s.querySelector('#recCnt').textContent=(qq||f)?n+' resultado'+(n===1?'':'s'):'';}
 s.addEventListener('input',function(e){if(e.target.id==='recQ')run();});
 s.addEventListener('click',function(e){var b=e.target.closest('.rcf');if(!b)return;f=b.getAttribute('data-f');s.querySelectorAll('.rcf').forEach(function(x){x.classList.toggle('on',x===b);});run();});
 return s;}
"""

NAV_OLD = "h+='<li class=\"grp\">Cierre</li>';"
NAV_NEW = ("if(D.recursos){h+='<li class=\"grp\">Recursos</li>';var rsub=D.recursos.cats.map(function(c){return '<li class=\"l2\">'+nl('recursos-'+c.id,'\\u00b7',c.h,'var(--defend)')+'</li>';}).join('');"
           "h+='<li class=\"unit\" data-u=\"recursos\"><div class=\"row\">'+nl('recursos','REC','Recursos de ciberseguridad','var(--defend)','udh')+TG+'</div><ul class=\"l2s\">'+rsub+'</ul></li>';}"
           + NAV_OLD)
MAIN_OLD = "if(D.role==='profe'){main.appendChild(usoSection());"
MAIN_ALT = "main.appendChild(evalSection());main.appendChild(footer());"   # alumnado: ya sin la rama profe
MAIN_ADD = "if(D.recursos){main.appendChild(recursosSection());}\n"

s = target.read_text(encoding="utf-8")
j = s.find("window.DATA=") + len("window.DATA=")
D, end = json.JSONDecoder().raw_decode(s[j:])
head, eng = s[:j], s[j + end:]
def publico(R):
    """Quita lo marcado como solo-profesorado (categorías o fichas con "profe": true)."""
    R = json.loads(json.dumps(R))
    cats = []
    for c in R["cats"]:
        if c.get("profe"):
            continue
        c["items"] = [it for it in c["items"] if not it.get("profe")]
        if c["items"]:
            cats.append(c)
    R["cats"] = cats
    return R

D["recursos"] = R if D.get("role") == "profe" else publico(R)

if MARK in eng:   # actualiza la función si ya existía
    k = eng.index(MARK); e = eng.index(" return s;}\n", k) + len(" return s;}\n")
    eng = eng[:k] + ENGINE_FN + eng[e:]
else:
    k = eng.index("function evalSection(")
    eng = eng[:k] + ENGINE_FN + eng[k:]
    assert eng.count(NAV_OLD) == 1, "menú: no se halló el grupo Cierre"
    eng = eng.replace(NAV_OLD, NAV_NEW)
    anchor = MAIN_OLD if eng.count(MAIN_OLD) == 1 else MAIN_ALT
    assert eng.count(anchor) == 1, "main: punto de inserción no hallado"
    eng = eng.replace(anchor, MAIN_ADD + anchor, 1)
    assert head.count("</style>") == 1
    head = head.replace("</style>", CSS + "</style>")
    print("motor y CSS de recursos añadidos")

out = head + json.dumps(D, ensure_ascii=False) + eng
target.write_text(out, encoding="utf-8")
n = sum(len(c["items"]) for c in D["recursos"]["cats"])
print(f"{target.name}: {n} recursos en {len(D["recursos"]["cats"])} grupos")
