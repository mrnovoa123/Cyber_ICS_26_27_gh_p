---
title: "Actividad 2.3 · Detectives con OSINT — guion de resolución (profesorado)"
modulo: "MP5021 Incidentes de Ciberseguridade · UD2 · CA2.4"
entorno: "Equipos del aula con Internet (no el laboratorio aislado) + Kali para las herramientas"
alcance: "Solo la identidad ficticia sembrada por el docente. Nada sobre personas ni empresas reales (RGPD)."
---

# Actividad 2.3 · Detectives con OSINT

**Objetivo:** investigar en fuentes abiertas la huella de **TecnoMariña S.L.** (ficticia) y de una persona
ficticia de su plantilla, correlacionar los hallazgos y redactar un informe que distinga lo **probado** de lo
**supuesto**. Ampliación: usar una credencial filtrada como alerta temprana en Wazuh.

> **Alcance firmado antes de empezar.** Objetivo único: lo sembrado por el docente (dominio, perfiles, documentos).
> Prohibido: personas reales, empresas reales, iniciar sesión con credenciales encontradas fuera del laboratorio,
> interactuar con perfiles (seguir, escribir). Si alguien se sale del alcance: se para, se borra lo recopilado
> y se comenta en clase.

---

## 0. Preparación del docente: sembrar la identidad (una vez por curso)

El OSINT necesita algo que encontrar. Un montaje mínimo, todo bajo vuestro control:

| Semilla | Dónde | Qué deja encontrar |
|---|---|---|
| Microsite de TecnoMariña | GitHub Pages (p. ej. `tecnomarina-lab.github.io`) | Página «Equipo» con nombres, cargos y patrón de correo `nombre.apellido@…` |
| PDF corporativo | Enlazado en el microsite | Metadatos: autor `lpena` (su usuario de Windows), programa, fecha |
| `robots.txt` | Microsite | `Disallow: /intranet-antigua/` → página olvidada con un organigrama |
| Repo público | GitHub (cuenta del docente para el curso) | Commit antiguo con `config.php` y una credencial: `lpena / Marina2026!` |
| Perfil ficticio | Página «sobre mí» en el microsite | Aficiones y fechas que sirven para adivinar contraseñas |

Preparar el PDF con metadatos controlados:

```bash
exiftool -Author="lpena" -Creator="Microsoft Word" -Title="Memoria TecnoMariña 2026" memoria.pdf
exiftool memoria.pdf | grep -Ei 'author|creator|title|create date'
```

Para la ampliación (alerta temprana), crear en srvweb el usuario de la credencial filtrada:

```bash
# srvweb (docente)
sudo useradd -m -s /bin/bash lpena && echo 'lpena:Marina2026!' | sudo chpasswd
```

---

## 1. Fase 1 · Plan de investigación

El alumnado pide a la IA el **plan por fases** (prompt de la web) y lo ajusta: qué buscar, en qué fuente, en qué orden
y qué hallazgo justifica pasar a la siguiente fase. La ejecución es **manual**.

Plan esperado (resumido): dominio y subdominios → personas y cargos → correos y patrón → documentos y metadatos →
repositorios y filtraciones → correlación y grafo → conclusiones con nivel de confianza.

## 2. Fase 2 · Dominio y servicios

```bash
# kali (con salida a Internet desde el aula, o desde el equipo del aula)
whois github.io | head -20                         # en GitHub Pages no aporta: anotarlo como límite
dig +short tecnomarina-lab.github.io
curl -s https://tecnomarina-lab.github.io/robots.txt
curl -s https://tecnomarina-lab.github.io/sitemap.xml | head
theHarvester -d tecnomarina-lab.github.io -b duckduckgo,crtsh,bing -l 200
```

theHarvester depende de fuentes externas que cambian: si una no responde, anotarlo y seguir con otra.
Búsquedas manuales (*dorks*):

```
site:tecnomarina-lab.github.io
site:tecnomarina-lab.github.io filetype:pdf
"tecnomarina" "@tecnomarina"
"Lucía Pena" "TecnoMariña"
```

## 3. Fase 3 · Documentos y metadatos

```bash
mkdir -p ~/osint/docs && cd ~/osint/docs
wget -r -l2 -nd -A pdf,docx,xlsx https://tecnomarina-lab.github.io/
exiftool * | grep -Ei 'file name|author|creator|producer|last modified by|create date'
strings memoria.pdf | grep -Ei 'users\\|@tecnomarina'    # rutas y correos en claro (si el PDF no comprime esos campos)
```

**Hallazgo esperado:** autor `lpena` = usuario interno de Lucía Pena (se cruza con la página «Equipo»), programa y fecha de creación.

## 4. Fase 4 · Repositorios y filtraciones

```bash
git clone https://github.com/<cuenta-del-curso>/tecnomarina-web.git && cd tecnomarina-web
git log --oneline | head
git log -p | grep -nEi 'pass(word)?|user|secret|token' | head
git show <commit>:config.php
```

**Hallazgo esperado:** credencial `lpena / Marina2026!` en un commit borrado después. Lección: borrar en un
commit nuevo no borra el historial.

## 5. Fase 5 · Correlación (SpiderFoot y Maltego)

```bash
spiderfoot -l 127.0.0.1:5001          # Kali; abrir http://127.0.0.1:5001
```

*New Scan* → objetivo `tecnomarina-lab.github.io` → perfil *Passive* (no toca el objetivo). Exportar a CSV.

Maltego CE (cuenta gratuita): entidades *Domain* → *Person* → *Email address* → *Document*; enlazar a mano lo
que las transformadas no encuentren. Captura del grafo para el informe.

## 6. Informe OSINT (entregable)

1. **Alcance y autorización** (firmado).
2. **Metodología** (fases y herramientas).
3. **Hallazgos**, cada uno con **fuente**, **fecha y hora de consulta**, **evidencia** (captura o comando) y
   **nivel de confianza**:

   | # | Hallazgo | Fuente | Evidencia | Confianza |
   |---|---|---|---|---|
   | H1 | Patrón de correo `nombre.apellido@tecnomarina.local` | Página «Equipo» | captura | Alta (3 ejemplos) |
   | H2 | Usuario Windows `lpena` | Metadatos del PDF | `exiftool` | Alta |
   | H3 | Credencial `lpena / Marina2026!` | Historial del repo | `git show` | Alta (existe), no comprobada fuera del laboratorio |
   | H4 | «Lucía es la responsable de TI» | Organigrama de la intranet antigua | captura | **Media**: página antigua, puede estar desactualizada |

4. **Conclusiones que NO se sostienen** con la evidencia (lo que la IA o el grupo supusieron sin prueba).
5. **Riesgos para TecnoMariña** y **medidas**: limpiar metadatos (`exiftool -all= *.pdf`), rotar la credencial y
   reescribir el historial, formación sobre exposición en redes, retirar páginas olvidadas.
6. **Lista de fuentes** completa.

## 7. Ampliación · OSINT como alerta temprana en Wazuh

La credencial encontrada se prueba **solo contra el laboratorio** (srvweb), simulando lo que haría un atacante:

```bash
# kali
ssh lpena@172.21.10.30            # contraseña Marina2026!
```

En Wazuh: **5715** (login SSH correcto) del usuario `lpena` desde 172.21.10.100. Con la ampliación de la 2.2
(regla 100210) sube a nivel 13. Conclusión para el informe: una filtración OSINT no detectada a tiempo termina
siendo un acceso válido que **no** dispara alertas de fuerza bruta. Medidas: vigilar filtraciones de la propia
organización, MFA, alerta por login desde orígenes no habituales.

## 8. Rúbrica rápida

| Se valora | Penaliza |
|---|---|
| Cada hallazgo con fuente, fecha y evidencia | Afirmaciones sin fuente |
| Niveles de confianza y conclusiones descartadas | Mezclar hechos y suposiciones |
| Medidas concretas para la organización | Cualquier dato de personas reales (fuera del alcance) |
| Grafo de correlación legible | Usar credenciales fuera del laboratorio |
