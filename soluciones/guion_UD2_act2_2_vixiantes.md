---
title: "Actividad 2.2 · Vixiantes dixitais — guion de resolución (profesorado)"
modulo: "MP5021 Incidentes de Ciberseguridade · UD2 · CA2.2"
tareas: "Tarea 2.3 (Reglas de Suricata) · Tarea 2.4 (Splunk y Suricata) · Tarea 2.5 (Splunk y Apache)"
entorno: "labcyber · aula 172.21.10.0/24 · casa 10.10.10.0/24 (panel Wazuh en 192.168.56.10)"
---

# Actividad 2.2 · Vixiantes dixitais

**Objetivo:** montar y operar la detección, del log a la alerta: Wazuh + Suricata + Sysmon, ataques desde
Kali, reglas propias y explotación de los datos con Splunk (SPL).

| VM | Papel | Aula | Casa |
|---|---|---|---|
| siem | Wazuh (manager, indexer, dashboard) + Suricata + Splunk 10.6 | 172.21.10.10 | 10.10.10.10 |
| win10 | Víctima Windows (agente Wazuh + Sysmon) | 172.21.10.20 | 10.10.10.20 |
| srvweb | Víctima Linux: Apache + DVWA + usuario débil `empleado` | 172.21.10.30 | 10.10.10.30 |
| kali | Atacante (fuera de HOME_NET) | 172.21.10.100 | 10.10.10.100 |

Los comandos usan la red del **aula**. En casa, cambiad `172.21.10.` por `10.10.10.`.

| Bloque | Contenido | Tarea |
|---|---|---|
| 0 | Comprobaciones previas | — |
| 1 | Sysmon → Wazuh y Suricata → Wazuh | — |
| 2 | Ataques desde Kali y qué alerta sale | Informe de 3–4 alertas |
| 3 | Reglas de Suricata | **Tarea 2.3** |
| 4 | Splunk: instalación e ingesta | — |
| 5 | Búsquedas y alertas sobre Suricata | **Tarea 2.4** |
| 6 | Búsquedas sobre Apache | **Tarea 2.5** |
| 7 | Ampliación: regla de Wazuh, correo y ELK | Ampliación |

---

## 0. Comprobaciones previas

```bash
# siem
sudo systemctl is-active wazuh-manager wazuh-indexer wazuh-dashboard suricata
sudo /var/ossec/bin/agent_control -l                 # win10 y srvweb: Active
grep -nE '^\s*(HOME_NET|EXTERNAL_NET):' /etc/suricata/suricata.yaml
#   HOME_NET: "[172.21.10.10,172.21.10.20,172.21.10.30]"   EXTERNAL_NET: "!$HOME_NET"
ip -o -4 addr | grep 172.21.10.                       # interfaz de la LAN (p. ej. enp0s8)
grep -E 'interface:' /etc/suricata/suricata.yaml | head -3   # debe ser la interfaz de la LAN
timedatectl | grep -E 'synchronized|Time zone'        # hora correcta: imprescindible para correlacionar
```

> **HOME_NET.** Si `HOME_NET` contiene toda la red /24, Kali es «interna» y las reglas ET y las de la tarea 2.3
> escritas con `$EXTERNAL_NET` **no saltan** con sus ataques. Solución: `sudo bash /vagrant/provision/suricata-homenet.sh activos`
> (volver atrás: `... red`). En OVA del aula, copiar antes el script a la VM.

Snapshots antes de empezar (desde el anfitrión): `vagrant snapshot save <vm> base-2-2` o *Instantánea* en VirtualBox.

---

## 1. Integrar las fuentes en Wazuh

### 1.1 Sysmon → Wazuh (win10)

El aprovisionamiento ya instala Sysmon (configuración de SwiftOnSecurity) y añade el canal. Comprobar:

```powershell
Get-Service Sysmon64                                         # Running
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 3 | Format-List Id,Message
Select-String "Sysmon/Operational" "C:\Program Files (x86)\ossec-agent\ossec.conf"
```

Si falta, añadir al `ossec.conf` del agente y reiniciar:

```xml
<localfile>
  <location>Microsoft-Windows-Sysmon/Operational</location>
  <log_format>eventchannel</log_format>
</localfile>
```

```powershell
Restart-Service WazuhSvc
```

Prueba: abrir `notepad.exe` y `powershell -enc ...` en win10 → en el panel, `rule.groups:sysmon` y
`data.win.system.eventID:1` (creación de proceso).

### 1.2 Suricata → Wazuh (siem)

```bash
grep -A3 'suricata/eve.json' /var/ossec/etc/ossec.conf     # bloque <localfile> json ya presente
sudo tail -f /var/log/suricata/fast.log                    # en otra terminal, durante los ataques
```

En el panel: `rule.groups:suricata`. Campos: `data.alert.signature`, `data.src_ip`, `data.dest_ip`,
`data.alert.severity` (1 = más grave). **Nivel 3** en Wazuh por defecto.

---

## 2. Ataques desde Kali y detección esperada

```bash
# kali (rockyou ya descomprimido por el aprovisionamiento; si no: sudo gunzip -k /usr/share/wordlists/rockyou.txt.gz)
nmap -sS -p- 172.21.10.30                                   # A1 escaneo
hydra -l empleado -P /usr/share/wordlists/rockyou.txt -t 4 ssh://172.21.10.30   # A2 fuerza bruta (usuario del laboratorio: empleado)
ssh empleado@172.21.10.30                                   # A3 acceso con la credencial encontrada (123456)
sudo hping3 --icmp --fast -c 150 172.21.10.30               # A4 ráfaga ICMP (dos guiones en --icmp y --fast)
curl "http://172.21.10.30/dvwa/vulnerabilities/sqli/?id=1'+UNION+SELECT+user,password+FROM+users--+&Submit=Submit"  # A5 SQLi en la URL
```

| Ataque | Suricata (fast.log / eve.json) | Wazuh |
|---|---|---|
| A1 escaneo | Firmas `ET SCAN …` (con HOME_NET correcto) | `rule.groups:suricata` |
| A2 fuerza bruta | Regla local `LAB intento de conexion SSH` (sid 1000002) | **5760** fallos → **5763** fuerza bruta (nivel 10); 5710/5712 si el usuario no existe |
| A3 acceso | — | **5715** login correcto: si llega justo después de 5763 → **verdadero positivo grave** |
| A4 ICMP | `LAB ICMP echo hacia la LAN` (sid 1000001) | `rule.groups:suricata` |
| A5 SQLi | Firmas ET de SQL injection (si las reglas ET están cargadas) | Reglas web de Wazuh sobre `access.log` (`rule.groups:web` y `attack`) |

### Informe de interpretación (3–4 alertas)

Para cada alerta: **qué regla** (ID y descripción), **qué evento** la produjo (línea de log original),
**origen → destino**, **veredicto** (VP / FP / necesita contexto) y **qué dato adicional** pedirías.
Ejemplo:

> **Alerta 5763 · nivel 10 · 08/11 10:12:31 UTC** — sshd: fuerza bruta contra `empleado` en srvweb desde
> 172.21.10.100. Se apoya en 8 eventos 5760 en 2 minutos. **VP**: la IP es externa a los activos y a los 40 s hay
> un 5715 (login correcto) del mismo origen. Siguiente paso: revisar `last`/`auth.log` en srvweb y abrir caso (2.4).

---

## 3. Tarea 2.3 · Reglas de Suricata

**Enunciado real:** cuatro alertas:
1. *priority 4* · SSH hacia la red interna.
2. *priority 1* · salida de la red interna hacia 85.91.64.65, 82.146.39.249, 5.196.213.99, 212.118.8.147.
3. *priority 4* · UDP/53 hacia una red que no sea la interna.
4. *priority 2* · más de 100 ICMP por minuto de la red interna hacia el exterior.

```bash
sudo nano /etc/suricata/rules/custom.rules
```

```
alert tcp $EXTERNAL_NET any -> $HOME_NET 22 (msg:"SSH hacia red interna"; flow:to_server; flags:S; priority:4; sid:1000020; rev:1;)
alert ip $HOME_NET any -> [85.91.64.65,82.146.39.249,5.196.213.99,212.118.8.147] any (msg:"Salida a IP marcada"; priority:1; sid:1000021; rev:1;)
alert udp $HOME_NET any -> $EXTERNAL_NET 53 (msg:"DNS a red externa"; priority:4; sid:1000022; rev:1;)
alert icmp $HOME_NET any -> $EXTERNAL_NET any (msg:"Exceso ICMP saliente"; itype:8; threshold:type threshold, track by_src, count 100, seconds 60; priority:2; sid:1000023; rev:1;)
```

- `flags:S` en la 1 evita una alerta por cada paquete de la sesión: una por intento de conexión.
- `threshold: type threshold` alerta **cada vez** que se cumplen 100 en 60 s; `type both` alertaría una sola vez por ventana.
- Alternativa a `priority`: `classtype:` (definido en `classification.config`, que ya fija una prioridad).

**Validar y cargar:**

```bash
# validar SOLO este fichero (-S carga en exclusiva el fichero indicado)
sudo suricata -T -c /etc/suricata/suricata.yaml -S /etc/suricata/rules/custom.rules -v
# añadirlo a la configuración (rule-files) y validar todo
sudo sed -i 's|^\(\s*\)- /etc/suricata/rules/local.rules|&\n\1- /etc/suricata/rules/custom.rules|' /etc/suricata/suricata.yaml
sudo suricata -T -c /etc/suricata/suricata.yaml && sudo systemctl restart suricata
grep -E 'custom.rules|rules loaded|error' /var/log/suricata/suricata.log | tail
```

### Cómo probar cada regla en un laboratorio aislado

Suricata escucha solo la interfaz de **labcyber**. El tráfico de una VM hacia IP de Internet sale por su NAT
(eth0) y **Suricata no lo ve**. Para las pruebas 2–4 hay dos opciones:

- **Kali como «exterior»:** con HOME_NET correcto, Kali ya es `$EXTERNAL_NET`.
- **Ruta temporal por labcyber:** forzar que el paquete a una IP «externa» salga por la LAN hacia el siem
  (el siem no reenvía: no sale nada del laboratorio).

```bash
# srvweb · averiguar la interfaz de la LAN
LANIF=$(ip -o -4 addr | awk '/172\.21\.10\./{print $2; exit}')

# Regla 1 · SSH hacia la red interna (desde kali)
ssh empleado@172.21.10.30                       # kali → srvweb:22

# Regla 2 · IP marcadas (srvweb), con ruta temporal
sudo ip route add 85.91.64.65/32 via 172.21.10.10 dev "$LANIF"
ping -c 3 85.91.64.65 ; nc -zv -w2 85.91.64.65 443
sudo ip route del 85.91.64.65/32

# Regla 3 · DNS a red externa (srvweb → kali como DNS)
dig @172.21.10.100 example.com +tries=1 +time=1

# Regla 4 · más de 100 ICMP/min hacia el exterior (srvweb → kali)
sudo apt-get install -y hping3     # si no está (instalar fuera del aula)
sudo hping3 --icmp --fast -c 150 172.21.10.100
```

```bash
# siem · comprobar
sudo grep -E 'sid:?10000(20|21|22|23)|SSH hacia red interna|IP marcada|DNS a red externa|Exceso ICMP' /var/log/suricata/fast.log | tail
sudo jq -c 'select(.event_type=="alert" and .alert.signature_id>=1000020 and .alert.signature_id<=1000023) | [.timestamp,.src_ip,.dest_ip,.alert.signature,.alert.severity]' /var/log/suricata/eve.json | tail
```

**Entrega:** `custom.rules` + captura de `suricata -T` sin errores + una línea de `fast.log` por regla.

---

## 4. Splunk en el laboratorio

Splunk no viene en el aprovisionamiento. Se instala **Splunk Enterprise 10.6.1.1** (paquete `.deb`) directamente en el
siem, leyendo `eve.json` en local, y el Apache de srvweb se envía con el **Universal Forwarder 10.6.1.1** (o se sube a mano).

> **Versión:** 10.6 tiene soporte hasta el 30/09/2028; la 9.4 lo pierde el 16/12/2026. El forwarder, igual o anterior al indexador.
> **RAM:** Wazuh + Splunk en la misma VM. Para la 2.2, subid la memoria del siem a 9–10 GB (el puesto tiene 32 GB).
> **Licencia:** una instalación nueva arranca en **Enterprise Trial (60 días)**. Las **alertas no existen en
> Splunk Free**: si caduca la prueba, desinstalar y reinstalar (4.5).
> **Descargas** (cuenta gratuita de splunk.com, fuera del aula): `splunk-10.6.1.1-b2ae2962645c-linux-amd64.deb` y
> `splunkforwarder-10.6.1.1-…-linux-amd64.deb`.

### 4.1 Splunk en el siem

```bash
sudo dpkg -i splunk-10.6.1.1-b2ae2962645c-linux-amd64.deb       # /opt/splunk + usuario splunk
sudo chown -R splunk:splunk /opt/splunk
sudo -u splunk /opt/splunk/bin/splunk start --accept-license --accept-sgt-current-at-splunk-com \
     --answer-yes --no-prompt --seed-passwd 'Cambia_Esta_2026'
sudo -u splunk /opt/splunk/bin/splunk stop
sudo /opt/splunk/bin/splunk enable boot-start -user splunk -systemd-managed 1
sudo systemctl start Splunkd && systemctl is-active Splunkd
```

Interfaz: `http://172.21.10.10:8000` (desde el anfitrión, reenvío NAT del puerto 8000), usuario `admin`.
Si el primer arranque no reconoce `--accept-sgt-current-at-splunk-com`, quitarlo y aceptar los términos cuando los pida.

### 4.2 Índices, entrada de Suricata y recepción del forwarder

```bash
S="sudo -u splunk /opt/splunk/bin/splunk"; A="-auth admin:Cambia_Esta_2026"
$S add index suricata $A
$S add monitor /var/log/suricata/eve.json -index suricata -sourcetype _json $A
$S enable listen 9997 $A
# lectura para el usuario splunk, también en los ficheros nuevos tras la rotación
sudo setfacl -m u:splunk:rx /var/log/suricata
sudo setfacl -d -m u:splunk:r /var/log/suricata
sudo setfacl -m u:splunk:r /var/log/suricata/eve.json
sudo -u splunk head -c 200 /var/log/suricata/eve.json
```

Comprobación en Splunk: `index=suricata | head 5`.

### 4.3 Apache de srvweb → Splunk (índice main)

**Opción A · Universal Forwarder 10.6.1.1** (paquete `.deb` descargado de splunk.com fuera del aula):

```bash
# srvweb
sudo dpkg -i splunkforwarder-10.6.1.1-*-linux-amd64.deb
sudo /opt/splunkforwarder/bin/splunk start --accept-license --accept-sgt-current-at-splunk-com --answer-yes --no-prompt --seed-passwd 'Cambia_Esta_2026'
sudo usermod -aG adm splunkfwd          # el forwarder corre como splunkfwd y Apache escribe con grupo adm
sudo /opt/splunkforwarder/bin/splunk add forward-server 172.21.10.10:9997 -auth admin:'Cambia_Esta_2026'
sudo /opt/splunkforwarder/bin/splunk add monitor /var/log/apache2/access.log -index main -sourcetype access_combined -auth admin:'Cambia_Esta_2026'
sudo /opt/splunkforwarder/bin/splunk restart
```

**Opción B · subir el fichero:** copiar `access.log` (`scp vagrant@172.21.10.30:/var/log/apache2/access.log .`)
y en Splunk *Settings → Add Data → Upload*, *sourcetype* `access_combined`, índice `main`.

### 4.4 Correo de las alertas de Splunk a MailHog

*Settings → Server settings → Email settings*: *Mail host* `172.21.10.10:1025`, sin TLS ni autenticación,
*Send emails as* `splunk@tecnomarina.local`. Las acciones de alerta *Send email* van a `soc@tecnomarina.local`
y se ven en `http://172.21.10.10:8025`.

### 4.5 Reiniciar la prueba de 60 días

```bash
sudo systemctl stop Splunkd
sudo dpkg -P splunk && sudo rm -rf /opt/splunk
# repetir 4.1 y 4.2 (las búsquedas y alertas guardadas se pierden: exportadlas antes si hacen falta)
```

### Campos de `eve.json` en Splunk

Con `sourcetype=_json` los campos anidados llevan prefijo: **`alert.signature`**, **`alert.category`**,
`alert.severity`, `alert.signature_id`. Las búsquedas que escriben `signature=` o `category=` sin prefijo
**no devuelven nada** (solo funcionan con el add-on de Suricata para Splunk, que renombra campos).

---

## 5. Tarea 2.4 · Splunk y Suricata

**Enunciado real:** (1.1) eventos con `src_ip` = tu IP, rango *All time*; (1.2) eventos de estadísticas de
Suricata; (1.3) ataque DoS en los últimos 5 minutos con IP y puerto origen; (2) alerta programada si hay más de
100 «Outbound ICMP detected» en 24 h, ejecutada cada hora, una sola vez; (3) alerta en tiempo real de salida hacia
89.45.235.21 y su regla de Suricata.

### Reglas de Suricata que necesitan las búsquedas

```
# /etc/suricata/rules/custom.rules (añadir)
alert icmp $HOME_NET any -> $EXTERNAL_NET any (msg:"Outbound ICMP detected"; itype:8; classtype:misc-activity; sid:1000025; rev:1;)
alert tcp $EXTERNAL_NET any -> $HOME_NET 80 (msg:"LAB posible inundacion SYN"; flags:S; flow:to_server; threshold:type both, track by_dst, count 500, seconds 5; classtype:attempted-dos; sid:1000026; rev:1;)
alert ip $HOME_NET any -> 89.45.235.21 any (msg:"Salida a IP sospechosa 89.45.235.21"; priority:1; sid:1000024; rev:1;)
```

`classtype:attempted-dos` hace que `alert.category` sea «Attempted Denial of Service», que es lo que busca el apartado 1.3.
`sudo suricata -T -c /etc/suricata/suricata.yaml && sudo systemctl restart suricata`.

**Generar los eventos:**

```bash
# srvweb → kali: >100 ICMP salientes (para la alerta programada)
sudo hping3 --icmp --fast -c 150 172.21.10.100
# kali → srvweb: inundación SYN de 20 s (solo en labcyber)
sudo timeout 20 hping3 -S -p 80 --flood 172.21.10.30
# srvweb → 89.45.235.21 por la LAN (ruta temporal, ver bloque 3)
LANIF=$(ip -o -4 addr | awk '/172\.21\.10\./{print $2; exit}')
sudo ip route add 89.45.235.21/32 via 172.21.10.10 dev "$LANIF"; ping -c 3 89.45.235.21; sudo ip route del 89.45.235.21/32
```

### Búsquedas SPL

```spl
# 1.1 · eventos con origen en mi IP (rango: All time)
index=suricata src_ip="172.21.10.30"

# 1.2 · estadísticas de Suricata
index=suricata event_type=stats
| table _time stats.capture.kernel_packets stats.capture.kernel_drops stats.decoder.pkts

# 1.3 · DoS en los últimos 5 minutos (rango: Last 5 minutes) con IP y puerto origen
index=suricata event_type=alert alert.category="Attempted Denial of Service"
| table _time src_ip src_port dest_ip dest_port alert.signature

# 2 · base de la alerta programada
index=suricata event_type=alert alert.signature="Outbound ICMP detected"

# 3 · base de la alerta en tiempo real
index=suricata event_type=alert dest_ip="89.45.235.21"
```

> En 1.1, «tu IP» es la de la máquina que hace de origen en vuestras pruebas (srvweb o win10). Con la inundación SYN,
> `src_port` varía en cada paquete: la tabla muestra uno por alerta.

### Crear las alertas (*Save As → Alert*)

| | Alerta programada (apartado 2) | Alerta en tiempo real (apartado 3) |
|---|---|---|
| Título | `ICMP saliente masivo` | `Salida a 89.45.235.21` |
| Alert type | *Scheduled* · *Run on Cron Schedule* `0 * * * *` (cada hora) | *Real-time* |
| Time range | *Last 24 hours* | — |
| Trigger | *Number of Results* · *is greater than* `100` | *Per-Result* |
| Trigger … | *Once* | *Throttle* 60 s (no inundar) |
| Acción | *Add to Triggered Alerts* (+ *Send email* a MailHog) | *Add to Triggered Alerts* (+ correo) |

Comprobar en *Activity → Triggered Alerts*. La programada se puede forzar con *Run* desde *Searches, reports
and alerts* sin esperar a la hora.

**Equivalentes en Wazuh** (para comparar SPL con el panel):
`rule.groups:suricata and data.src_ip:172.21.10.30` · `data.alert.category:"Attempted Denial of Service"` ·
`data.dest_ip:89.45.235.21`.

**Entrega:** PDF con captura de cada búsqueda (con el rango visible) y de la configuración y disparo de las dos alertas.

---

## 6. Tarea 2.5 · Splunk y Apache

**Enunciado real:** sobre logs de Apache: (1.1) peticiones que no sean GET ni POST; (1.2) errores 5xx con
timestamp, URI y código; (1.3) lista de IP origen sin repetir; (1.4) peticiones cuya URI contenga «SQL», con
timestamp, URI e IP; (2) ingerir el log público de `almhuette-raith.at/apache-log/access.log` y repetir,
buscando además inyección SQL.

### Generar tráfico variado (kali → srvweb)

```bash
for m in PUT DELETE OPTIONS PATCH; do curl -s -o /dev/null -X $m http://172.21.10.30/; done
curl -sI http://172.21.10.30/                                         # HEAD
curl -s "http://172.21.10.30/dvwa/vulnerabilities/sqli/?id=1'+OR+'1'='1&Submit=Submit" -o /dev/null
curl -s "http://172.21.10.30/dvwa/vulnerabilities/sqli/?id=1'+UNION+SELECT+user,password+FROM+users--+&Submit=Submit" -o /dev/null
nikto -h http://172.21.10.30 -maxtime 60s                             # ruido realista
```

Las URI quedan en el log aunque DVWA redirija al login (302): para esta tarea no hace falta iniciar sesión.
Para tener **5xx** reales, una página de error en srvweb:

```bash
# srvweb
echo '<?php http_response_code(500); echo "error de prueba";' | sudo tee /var/www/html/error500.php
curl -s -o /dev/null -w '%{http_code}\n' http://172.21.10.30/error500.php     # 500
```

### Búsquedas SPL (sourcetype `access_combined`)

```spl
# 1.1 · ni GET ni POST
index=main sourcetype=access_combined NOT method IN (GET, POST)
| stats count by method

# 1.2 · errores 5xx
index=main sourcetype=access_combined status>=500 status<=599
| table _time uri status

# 1.3 · IP de origen sin repetir
index=main sourcetype=access_combined
| dedup clientip | table clientip

# 1.4 · URI que contiene "SQL" (la búsqueda de valores no distingue mayúsculas: casa con /sqli/)
index=main sourcetype=access_combined uri="*SQL*"
| table _time uri clientip

# 2 · inyección SQL en el log público (y en el propio)
index=main sourcetype=access_combined ("*SELECT*FROM*" OR "*UNION*" OR "*1=1*" OR "*DROP*")
| table _time clientip method uri status
```

- `method!=GET method!=POST` también funciona, pero descarta los eventos sin campo `method`; `NOT method IN (…)` es más explícito.
- Las cadenas pueden ir **codificadas** (`%27`, `%20`, `+`). Versión más robusta para el apartado 2:
  `| regex uri="(?i)(union(\+|%20|\s)+select|select.+from|%27|'\s*or\s*'?1'?\s*=\s*'?1|drop(\+|%20)table)"`.
- Lo enviado por **POST** no queda en `access.log`: una inyección por formulario POST no se ve aquí (sí en
  Suricata si inspecciona el cuerpo). Buen punto para el informe.

### Log público (apartado 2)

Descargar `http://www.almhuette-raith.at/apache-log/access.log` **fuera del aula** (son varios cientos de MB;
basta con un trozo: `head -n 200000 access.log > almhuette.log`), subirlo con *Add Data → Upload*,
*sourcetype* `access_combined`, índice `main` (o un índice `publico` para no mezclarlo con el del laboratorio:
entonces cambiar `index=` en las búsquedas).

**Equivalentes en Wazuh** sobre `access.log` de srvweb: `rule.groups:web and rule.groups:attack`, y
`data.protocol:PUT` / `data.id:5*` en las alertas web.

**Entrega:** PDF con una captura por apartado (búsqueda + resultados).

---

## 7. Ampliaciones

### 7.1 Regla propia de Wazuh

```xml
<!-- /var/ossec/etc/rules/local_rules.xml (siem) — 100100–100120 los usa la práctica purple y 100150/100160 la web; usar 1002xx -->
<group name="local,sshd,">
  <rule id="100210" level="13">
    <if_sid>5715</if_sid>
    <srcip>172.21.10.100</srcip>
    <description>Login SSH correcto desde el equipo atacante del laboratorio ($(srcip)) — posible compromiso</description>
    <mitre><id>T1078</id></mitre>
  </rule>
</group>
```

```bash
sudo /var/ossec/bin/wazuh-logtest      # pegar una línea "Accepted password for empleado from 172.21.10.100 ..."
sudo systemctl restart wazuh-manager
```

### 7.2 Alerta por correo (MailHog)

Ver la sección «Alertas por correo con MailHog» de la web (Wazuh → Postfix → MailHog, `email_alert_level` 10).
La regla 100210 (nivel 13) y la 5763 (nivel 10) llegan al buzón.

### 7.3 Práctica paralela ELK

Filebeat con el módulo `suricata` → Elasticsearch → Kibana (bloque «Práctica paralela» de la actividad en la web).
Tabla KQL ↔ SPL de tres consultas equivalentes:

| Consulta | SPL | KQL |
|---|---|---|
| Alertas de Kali | `index=suricata event_type=alert src_ip=172.21.10.100` | `suricata.eve.event_type:alert and source.ip:"172.21.10.100"` |
| SSH | `index=suricata dest_port=22` | `destination.port:22` |
| Top firmas | `… \| stats count by alert.signature` | Visualización *Top values* de `rule.name` |

No arrancar ELK y Wazuh completos a la vez.

---

## 8. Problemas típicos

| Síntoma | Causa | Solución |
|---|---|---|
| Ataques de Kali sin alertas ET | Kali dentro de HOME_NET | `suricata-homenet.sh activos` |
| Reglas 2.3 (2–4) no saltan | Tráfico saliendo por la NAT | Ruta temporal por la LAN o Kali como destino |
| `suricata -T` falla | Comillas o `;` que faltan; sid repetido | Leer la línea que indica; sids 1000020–1000026 únicos |
| Splunk no ve eve.json | Permisos del usuario `splunk` | `setfacl` del bloque 4.2 |
| `signature=` sin resultados | Campo anidado | `alert.signature=` |
| Alertas de Splunk desactivadas | Licencia Free | Trial o licencia de desarrollador |
| hping3 «unrecognized option» | Raya larga copiada (`—fast`) | Escribir `--icmp --fast` |
| hydra no encuentra rockyou | Comprimido | `sudo gunzip -k /usr/share/wordlists/rockyou.txt.gz` |

## 9. Rúbrica rápida

| Entregable | Se valora |
|---|---|
| Tarea 2.3 | 4 reglas correctas (prioridad, direcciones, umbral), `suricata -T` limpio, evidencia de cada disparo |
| Tarea 2.4 | Búsquedas con rango correcto, campos con prefijo `alert.`, dos alertas configuradas y disparadas |
| Tarea 2.5 | Cinco búsquedas con resultados, `dedup`, detección de SQLi codificada, comentario sobre POST |
| Informe de alertas | 3–4 alertas con regla, evento, veredicto justificado y siguiente paso |
