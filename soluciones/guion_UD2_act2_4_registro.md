---
title: "Actividad 2.4 · Do caos á orde — guion de resolución (profesorado)"
modulo: "MP5021 Incidentes de Ciberseguridade · UD2 · CA2.5"
entorno: "labcyber · siem 172.21.10.10 (Wazuh + TheHive) · alertas generadas en la actividad 2.2"
---

# Actividad 2.4 · Do caos á orde

**Objetivo:** convertir alertas sueltas en **incidentes gestionados**: plantilla de registro, casos en TheHive
(o hoja de registro), clasificación con la taxonomía de la 2.1, valoración de criticidad y seguimiento inicial.

| Paso | Qué se hace |
|---|---|
| 1 | Exportar las alertas de la 2.2 |
| 2 | Plantilla de registro |
| 3 | Agrupar alertas en incidentes y clasificarlos |
| 4 | Valorar la criticidad |
| 5 | Abrir los casos en TheHive (manual o API) |
| 6 | Seguimiento inicial: responsable, próximos pasos, plazos |
| 7 | Ampliación: Wazuh → TheHive automático |

> **Con poca RAM:** TheHive se sustituye por una hoja de registro con las mismas columnas. El CA se cubre igual.

---

## 1. Exportar las alertas de la 2.2

```bash
# siem · alertas de nivel ≥ 7 de la última sesión, en formato tabla
sudo jq -r 'select(.rule.level>=7) | [.timestamp, .agent.name, .rule.id, .rule.level, .rule.description, (.data.srcip // .data.src_ip // "-")] | @tsv' \
  /var/ossec/logs/alerts/alerts.json | tail -40 > ~/alertas_2_2.tsv
column -t -s $'\t' ~/alertas_2_2.tsv | less -S
# recuento por regla (qué ha pasado, de un vistazo)
cut -f3,5 ~/alertas_2_2.tsv | sort | uniq -c | sort -rn
```

En el panel: *Threat Hunting* → filtro `rule.level >= 7` → *Export formatted* (CSV).

> **Semáforo de datos:** si se pasan alertas a una IA en la nube, solo del laboratorio (IP privadas → ámbar)
> y sin nombres reales.

## 2. Plantilla de registro

| Campo | Ejemplo | De dónde sale |
|---|---|---|
| ID | `INC-2026-007` | Correlativo |
| Fecha/hora de detección (UTC) | 2026-11-08 10:12 | Primera alerta del grupo |
| Detectado por | Wazuh regla 5763 | Alerta |
| Activo afectado | srvweb (172.21.10.30), servicio SSH | Alerta |
| Clasificación / tipo | Intento de intrusión → acceso con credenciales | Taxonomía (2.1) |
| Descripción | 2 340 intentos SSH contra `empleado` desde 172.21.10.100; login correcto a los 40 s | Alertas 5760, 5763, 5715 |
| Impacto · urgencia · **criticidad** | Alto · Alta · **Alta** | Matriz (paso 4) |
| Estado | Abierto → En análisis → Contenido → Cerrado | Seguimiento |
| Responsable | Técnico de sistemas | Seguimiento |
| Próximos pasos | Bloquear IP, cambiar contraseña, revisar `auth.log` y `last` | Seguimiento |
| Plazo (SLA) | 4 h para contención | Tabla de SLA |
| Evidencias | IDs de alerta, capturas, líneas de log | Paso 1 |

**Regla de oro:** cada campo apunta a la alerta o línea de log que lo respalda. Lo que no tiene respaldo se
escribe como «pendiente de confirmar» (control de la capa de IA: la IA tiende a rellenar campos inventados).

## 3. De alertas a incidentes

Varias alertas son **un** incidente si comparten origen, destino y ventana temporal:

| Incidente | Alertas que agrupa | Clasificación (Guía Nacional) |
|---|---|---|
| INC-1 · Reconocimiento | Firmas `ET SCAN`, sid 1000002 | Obtención de información → escaneo |
| INC-2 · Compromiso de cuenta SSH | 5760 ×n, 5763, **5715** | **Intrusión** → compromiso de cuenta sin privilegios (con el 5715; sin él sería «Intento de intrusión») |
| INC-3 · Ráfaga ICMP / SYN | sid 1000001, 1000026 | Disponibilidad → DoS (intento) |
| INC-4 · SQLi contra DVWA | Reglas web de Wazuh + firmas ET | Intento de intrusión → explotación de vulnerabilidad |

## 4. Valorar la criticidad

**Criticidad = impacto × urgencia**, decidida y firmada por el alumnado (la IA solo propone):

| Impacto \ Urgencia | Baja | Media | Alta |
|---|---|---|---|
| **Alto** | Media | Alta | **Crítica** |
| **Medio** | Baja | Media | Alta |
| **Bajo** | Baja | Baja | Media |

- **Impacto**: qué activo y qué dimensión (C/I/D). Datos del ayuntamiento = alto.
- **Urgencia**: ¿sigue activo? ¿puede extenderse? Un login correcto tras fuerza bruta = alta.
- Referencia oficial: la Guía Nacional define **peligrosidad** (bajo, medio, alto, muy alto, crítico) por tipo de
  incidente e **impacto** por consecuencias. Se usará para notificar en la UD5.

Tabla de SLA orientativa: crítica 1 h · alta 4 h · media 24 h · baja 72 h (tiempo hasta la contención).

## 5. Casos en TheHive

Despliegue, filtros y depuración: secciones «TheHive con Wazuh: integración y uso» y «TheHive: despliegue…» de la web.
Acceso `http://172.21.10.10:9000`, organización **TecnoMariña**, usuario analista.

### 5.1 Manual (interfaz)

*Cases → New case*: título, descripción, **Severity** (Low/Medium/High/Critical), **TLP** (Amber), **PAP**, etiquetas
(`ssh`, `fuerza-bruta`, `T1110`). Dentro del caso:

- **Tasks**: «Contener (bloquear IP)», «Erradicar (cambiar contraseña)», «Analizar `auth.log`», «Notificar».
- **Observables**: `ip` 172.21.10.100 (IOC), `hostname` srvweb, `other` usuario `empleado`.
- **Timeline / logs de tarea**: qué se hizo, cuándo y por quién.

### 5.2 Por API (útil para cargar varios casos)

```bash
# siem · API key del analista (perfil → API Key)
KEY='API_KEY_DEL_ANALISTA'
curl -s -X POST http://172.21.10.10:9000/api/v1/case \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"title":"INC-2: compromiso de cuenta SSH en srvweb",
       "description":"Fuerza bruta (5763) y login correcto (5715) de empleado desde 172.21.10.100",
       "severity":3, "tlp":2, "pap":2, "tags":["ssh","fuerza-bruta","T1110","T1078"]}' | jq '{_id,number,title}'

# añadir el IOC al caso
CASE='~123456'    # _id devuelto
curl -s -X POST "http://172.21.10.10:9000/api/v1/case/$CASE/observable" \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"dataType":"ip","data":"172.21.10.100","ioc":true,"tlp":2,"message":"Origen de la fuerza bruta"}' | jq '.[0]._id'
```

`severity`: 1 baja · 2 media · 3 alta · 4 crítica. `tlp`: 0 clear/white · 1 green · 2 amber · 3 red.

## 6. Seguimiento inicial (entregable)

Informe breve por incidente: estado, responsable, acciones ya hechas, próximos pasos con fecha y **SLA cumplido sí/no**.

Ejemplo INC-2:

| Hora (UTC) | Acción | Quién |
|---|---|---|
| 10:12 | Detección (5763 + 5715) | Wazuh |
| 10:20 | Caso abierto en TheHive, criticidad alta | Analista N1 |
| 10:35 | IP 172.21.10.100 bloqueada en srvweb (`sudo nft add rule …` o Active Response, UD3) | Sistemas |
| 10:50 | Contraseña de `empleado` cambiada; sesiones cerradas (`pkill -KILL -u empleado`) | Sistemas |
| Pendiente | Revisar `/home/empleado/.bash_history` y `last -i` para ver qué hizo | Analista N2 |

## 7. Ampliación · Wazuh → TheHive automático (introducción al SOAR)

Integración `custom-w2thive` (script v5 de la web) con dos bloques `<integration>`: nivel ≥ 10, o grupo `suricata`
con `SURICATA_SEV_THRESHOLD = 1`. Prueba: repetir la fuerza bruta → alerta en *Alerts* de TheHive → *Create case from alert*.

```bash
sudo tail -f /var/ossec/logs/integrations.log
```

## 8. Rúbrica rápida

| Se valora | Penaliza |
|---|---|
| Plantilla completa y usada en todos los casos | Campos sin respaldo en alertas |
| Alertas agrupadas en incidentes con criterio (origen, destino, tiempo) | Un caso por alerta sin agrupar |
| Clasificación coherente con la taxonomía de la 2.1 | Criticidad sin justificar o copiada de la IA |
| Seguimiento con responsable, próximos pasos y SLA | Casos sin tareas ni observables |
