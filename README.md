# MP5021 · Incidentes de Ciberseguridad — web del módulo

Web didáctica del módulo **MP5021 Incidentes de Ciberseguridade** (Curso de Especialización, IES Chan do Monte, 2026/2027). Dos versiones generadas de una misma fuente, en HTML autocontenido (sin dependencias que compilar).

| Fichero | Versión | URL al desplegar |
|---|---|---|
| `index.html` | **Profesorado** — todo + correcciones, decisiones, soluciones, prácticas y resumen operativo (con verja de contraseña) | `/` |
| `alumnado/index.html` | **Alumnado** — sin soluciones ni notas docentes; de momento solo la UD1 desarrollada | `/alumnado/` |

Ambas versiones salen de la **misma fuente** (`window.DATA` + motor JS). **Solo se edita `index.html`** (profesorado) y después se regenera la de alumnado:

```bash
python3 build_alumnado.py
```

El script **elimina del fichero** (no solo oculta) todo lo docente: soluciones, correcciones y notas de profesorado, prácticas de aula de Moodle, resumen operativo, la sección «Uso indebido de la IA», la verja de contraseña y el desarrollo detallado de las unidades no publicadas (hoy solo se publica la UD1; se cambia en `PUBLICADAS`). Si encuentra contenido docente que no sabe quitar, se detiene con un error en vez de generar el fichero.

Incluye laboratorio (Proxmox en aula + Vagrant en casa, red `172.21.10.0/24`, Debian 12), teoría por unidad, las 26 actividades con su capa de IA (ruta · riesgo · control) y la evaluación. Interruptor de "Capa IA" y tema claro/oscuro incorporados.

## Desplegar en Netlify (rápido)
1. Entra en app.netlify.com → **Add new site → Deploy manually**.
2. Arrastra **esta carpeta** (o el .zip). Home = profesorado (con contraseña); alumnado en `/alumnado/`.

## Desplegar con GitHub + Netlify (auto-despliegue)
1. Crea un repositorio (recomendado **privado**) y sube estos ficheros.
2. En Netlify: **Add new site → Import an existing project → GitHub**, elige el repo.
   - Build command: *(vacío)* · Publish directory: `.`
3. Cada `git push` vuelve a desplegar solo.

> **Nota de privacidad:** la raíz (profesorado) lleva una verja de contraseña por JavaScript, que **no es seguridad real** (el contenido viaja en el HTML). Para proteger de verdad las soluciones y notas docentes: entregar al alumnado solo `alumnado/`, o publicar el profesorado en un sitio/repo aparte no enlazado, o usar contraseña de sitio de Netlify (plan de pago).
