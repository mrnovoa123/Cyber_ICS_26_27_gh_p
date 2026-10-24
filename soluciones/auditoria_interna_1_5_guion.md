---
title: "Actividad 1.5 · Auditoría interna de cumplimiento — guion de profesorado"
modulo: "MP5021 Incidentes de Ciberseguridade · UD1 · CA1.5"
tipo: "Guion detallado / solución orientativa (profesorado)"
entorno: "Laboratorio labcyber aislado (172.21.10.0/24 en aula · 10.10.10.0/24 en casa)"
caracter: "Auditoría defensiva de cumplimiento: solo comprobación de configuración, sin ataques"
---

# Actividad 1.5 · Detectives da seguridade — auditoría interna

**Objetivo:** verificar, con evidencia objetiva, si el puesto de trabajo y el servidor
cumplen la **normativa del puesto** redactada en la actividad 1.2, usando una **auditoría
manual** (lista de comprobación) + una **auditoría automática** con el módulo **SCA de
Wazuh**, y entregar un **informe** con hallazgos, riesgo y mejoras priorizadas.

> **Carácter de la actividad.** Es una auditoría de *cumplimiento* (blue team): todo lo que
> se hace es **leer y comprobar configuración**. No se ataca ni se explota nada; no hace falta
> Kali para esta actividad. Las máquinas implicadas son **win10** (puesto) y **srvweb**
> (servidor), con el **SIEM** recogiendo el resultado del SCA.

Las direcciones de este guion usan el plan del **aula (172.21.10.x)**. Si se monta en casa
con Vagrant, el plan es 10.10.10.x y el panel de Wazuh está en `https://192.168.56.10`.

| VM | Rol en la auditoría | IP aula | IP casa |
|---|---|---|---|
| siem | Recoge el SCA de los agentes; panel de Wazuh | 172.21.10.10 | 10.10.10.10 (panel 192.168.56.10) |
| win10 | Puesto auditado (agente Wazuh + Sysmon) | 172.21.10.20 | 10.10.10.20 |
| srvweb | Servidor auditado (agente Wazuh) | 172.21.10.30 | 10.10.10.30 |

---

## 0. Comprobaciones previas del laboratorio

Antes de auditar hay que confirmar que las máquinas están **arriba, conectadas y con una
línea base que medir**. Todas estas comprobaciones son de **verificación (solo lectura)**. Se
usa el plan del **aula (172.21.10.x)**; entre paréntesis, el equivalente de **casa**
(10.10.10.x, panel en `192.168.56.10`).

### 0.1 SIEM (siem) — el recolector

```bash
# Servicios del stack Wazuh arriba
sudo systemctl is-active wazuh-manager wazuh-indexer wazuh-dashboard
# Suricata operativo (para otras UD; en la 1.5 no es imprescindible)
sudo systemctl is-active suricata
# Agentes dados de alta y su estado (se esperan win10 y srvweb como 'Active')
sudo /var/ossec/bin/agent_control -l
```

- Panel accesible: `https://172.21.10.10` (casa: `https://192.168.56.10`), login `admin`;
  contraseña en `labcyber/wazuh-passwords.txt` (Vagrant) o en `wazuh-install-files.tar`.
- Si un agente sale `Disconnected` / `Never connected`, arréglalo en su VM (0.3) antes de auditar.

### 0.2 Red del laboratorio — aislada y con visibilidad

```bash
# Desde siem: las dos víctimas responden
ping -c2 172.21.10.20     # win10
ping -c2 172.21.10.30     # srvweb
# Confirmar aislamiento: NO debe haber salida a Internet desde el segmento
ping -c2 8.8.8.8          # debe fallar (100% packet loss)
```

Si win10 no responde al ping, revisa que su regla de firewall de laboratorio (ICMP entrante
desde la LAN) esté activa.

### 0.3 Agentes en las víctimas — conectados y reportando

**srvweb (Linux):**

```bash
sudo systemctl is-active wazuh-agent                   # active
sudo grep -E '<address>' /var/ossec/etc/ossec.conf     # apunta a 172.21.10.10 (casa: 10.10.10.10)
sudo tail -n 5 /var/ossec/logs/ossec.log               # sin errores de conexión
```

**win10 (PowerShell como administrador):**

```powershell
Get-Service WazuhSvc              # Status Running
Get-Content "C:\Program Files (x86)\ossec-agent\ossec.conf" | Select-String "<address>"
```

En el panel -> **Agents**, ambos deben verse **Active** y con *last keep alive* reciente.

### 0.4 Módulo SCA — listo para dar el % de cumplimiento

- En el panel -> **Security Configuration Assessment**, selecciona **win10** y **srvweb**.
- Comprueba que **ya aparece un escaneo** (política del CIS Benchmark del SO correspondiente)
  con su **Score** y el desglose Passed / Failed.
- Si todavía no hay resultados, fuerza un escaneo reiniciando el agente y espera unos minutos:

  ```bash
  sudo systemctl restart wazuh-agent       # srvweb
  ```

  ```powershell
  Restart-Service WazuhSvc                 # win10
  ```

### 0.5 Línea base auditable — que haya algo que medir

La auditoría compara contra la **normativa de la actividad 1.2**, así que confirma que el puesto
y el servidor tienen configuración que comprobar:

**win10:**

```powershell
net accounts                 # política de contraseñas/bloqueo definida
manage-bde -status C:        # estado de BitLocker (cifrado sí/no)
```

**srvweb:**

```bash
getent passwd empleado                       # existe el usuario de ejemplo
systemctl is-enabled unattended-upgrades     # estado (enabled/disabled: dará hallazgo si procede)
sudo sshd -T | grep -i passwordauthentication
```

> No hace falta que todo "cumpla": precisamente los incumplimientos son los hallazgos del
> informe. Lo que importa es que los comandos **devuelvan datos** para poder evidenciarlos.

### 0.6 Hora sincronizada (clave para correlacionar logs)

```bash
timedatectl | grep -Ei 'synchronized|time zone'   # en siem y srvweb
```

```powershell
w32tm /query /status            # en win10
```

### 0.7 Red de seguridad antes de empezar

Toma un **snapshot** de cada VM en estado limpio, para poder revertir si durante el ejercicio
se cambia configuración:

```bash
# desde el host, entorno Vagrant
vagrant snapshot save siem base-1-5
vagrant snapshot save srvweb base-1-5
vagrant snapshot save win10 base-1-5
```

### 0.8 Documento de referencia

La **normativa del puesto** y el **decálogo** de la actividad 1.2: de ahí salen las cláusulas
que se auditan.

> **Resumen de "todo correcto":** stack Wazuh arriba y panel accesible · win10 y srvweb
> **Active** en el panel · segmento aislado (sin Internet) y víctimas alcanzables desde siem ·
> SCA con escaneo y Score por máquina · comandos de la línea base devolviendo datos · hora
> sincronizada · snapshots hechos.

---

## 1. Entregable A · Construir el checklist (CIS Controls / ENS)

La lista de comprobación es una **tabla con una fila por cláusula** de la normativa. Cada fila
debe ser **auditable**: si no se puede señalar qué evidencia la demuestra y con qué comando se
obtiene, la fila se reescribe o se elimina.

Columnas recomendadas:

| # | Cláusula de la normativa | Control de referencia | Evidencia esperada | Método / comando | Equipo |
|---|---|---|---|---|---|
| C-01 | Contraseña ≥ 12 caracteres | CIS 5.2 · ENS `op.acc` | Longitud mínima = 12 | `net accounts` / `secpol.msc` | win10 |
| C-02 | Bloqueo de cuenta tras 5 intentos | CIS 6.2 · ENS `op.acc` | Umbral de bloqueo = 5 | `net accounts` | win10 |
| C-03 | Bloqueo de pantalla a 5 min | ENS `mp.eq.2` | Inactividad = 300 s | `secpol.msc` + captura | win10 |
| C-04 | Disco del sistema cifrado | CIS 3.6 | BitLocker: *Protección activada* | `manage-bde -status C:` | win10 |
| C-05 | Bloqueo de USB por directiva | CIS 10.3 · ENS `mp.si` | Directiva de instalación de dispositivos aplicada | `gpresult /h` | win10 |
| C-06 | Actualizaciones al día | CIS 7.3 · ENS `op.exp` | Sin paquetes pendientes; `unattended-upgrades` activo | `apt list --upgradable` | srvweb |
| C-07 | SSH sin login por contraseña débil / política | ENS `op.acc` | Política de acceso revisada | `sshd -T` (lectura de config) | srvweb |
| C-08 | Antimalware / FIM operativo | CIS 10 · ENS `op.mon` | Agente Wazuh activo, FIM configurado | panel Wazuh | ambos |

> El número exacto de filas lo marca la normativa de cada grupo. Lo importante es la
> **trazabilidad cláusula → control → evidencia → método**.

---

## 2. Entregable B · Auditoría manual (solo lectura de configuración)

Se recorre el checklist máquina a máquina y se marca cada fila como
**cumple / no cumple / no aplica**, guardando la evidencia (salida de comando o captura, con
fecha y nombre del equipo). **Todos los comandos siguientes son de consulta**: muestran el
estado actual, no lo modifican.

### 2.1 Puesto win10 (PowerShell / símbolo del sistema como administrador)

```powershell
# C-01 y C-02 — política de contraseñas y bloqueo de cuenta
net accounts
#   Longitud mínima de contraseña .......: 12
#   Umbral de bloqueo de la cuenta ......: 5

# Exportar la directiva de seguridad local completa (contraseñas, bloqueo, auditoría)
secedit /export /cfg C:\lab\politica_actual.inf
notepad C:\lab\politica_actual.inf   # revisar MinimumPasswordLength, LockoutBadCount...

# C-03 — bloqueo de pantalla por inactividad (segundos)
#   Revisar en secpol.msc: Directivas locales > Opciones de seguridad >
#   "Inicio de sesión interactivo: límite de inactividad de la máquina"
#   (lectura; se acompaña de captura)

# C-04 — cifrado de disco
manage-bde -status C:
#   Estado de conversión .....: Totalmente cifrado
#   Protección ................: Activada

# C-05 — bloqueo de USB y resumen de directivas aplicadas
gpresult /h C:\lab\gpresult.html   # informe HTML de todas las GPO en vigor
start C:\lab\gpresult.html

# Evidencia de apoyo: ¿hay alguna restricción de instalación de dispositivos?
reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeviceInstall\Restrictions"
```

### 2.2 Servidor srvweb (shell, con sudo donde haga falta)

```bash
# C-06 — actualizaciones pendientes y actualizaciones automáticas
apt list --upgradable 2>/dev/null          # lista vacía = al día
systemctl is-enabled unattended-upgrades    # 'enabled' = actualizaciones automáticas on
cat /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null

# C-07 — política SSH efectiva (solo lectura de la configuración resuelta)
sudo sshd -T | grep -Ei 'passwordauthentication|permitrootlogin|maxauthtries'

# Usuarios locales y última vez que cambiaron la contraseña (revisión de cuentas)
sudo chage -l empleado        # fecha de caducidad / último cambio
awk -F: '$3>=1000 && $3<65534 {print $1}' /etc/passwd   # cuentas de usuario reales

# C-08 — agente de seguridad operativo
systemctl is-active wazuh-agent
```

> **Regla de método:** una respuesta verbal del "auditado" ("sí, eso lo tenemos") solo vale si
> se puede contrastar con una de estas salidas. Si la directiva no está aplicada, el hallazgo
> se registra aunque la respuesta fuera afirmativa.

---

## 3. Entregable C · Auditoría automática con Wazuh SCA

El módulo **SCA (Security Configuration Assessment)** de Wazuh ejecuta, en cada agente, una
política basada en los **CIS Benchmarks** del sistema operativo y devuelve, por comprobación,
el resultado **passed / failed / not applicable** y un **porcentaje de cumplimiento**.

### 3.1 Ver el resultado en el panel

1. Entrar en el panel de Wazuh → menú **Security configuration assessment**.
2. Seleccionar el agente **win10** y luego **srvweb**.
3. Anotar, por cada uno: **Score (%)**, número de **Passed / Failed / Not applicable** y la
   política aplicada (p. ej. *CIS Benchmark for Ubuntu Linux 22.04*).
4. Abrir varias comprobaciones **Failed** y leer el campo **Rationale** y **Remediation**:
   describen qué falla y cómo corregirlo.

### 3.2 Forzar un escaneo y leerlo por línea de comandos (opcional)

```bash
# En el agente (srvweb), relanzar el análisis SCA sin esperar al intervalo
sudo systemctl restart wazuh-agent         # dispara un SCA al reconectar
# Resumen local del último SCA (políticas, aprobadas/falladas, score)
sudo /var/ossec/bin/wazuh-control info 2>/dev/null
sudo grep -A3 '"type":"summary"' /var/ossec/logs/ossec.log | tail -n 20
```

### 3.3 Cruce con el checklist manual

Para cada comprobación **Failed** del SCA, buscar la **fila equivalente** del checklist manual
y anotar si coinciden. Lo que el SCA **no ve** (p. ej. *mesa limpia*, carteles, procedimientos)
se audita **solo a mano**: es el motivo de tener las dos vías.

> **Alternativa para Windows:** [CIS-CAT Lite](https://learn.cisecurity.org/cis-cat-lite)
> genera un informe HTML con la puntuación frente al benchmark, útil si se quiere un segundo
> dato de contraste al del agente Wazuh.

---

## 4. Entregable D · Informe de auditoría

Estructura recomendada (misma lógica **hallazgo → riesgo → mejora** de todo el módulo):

1. **Alcance:** equipos auditados (win10, srvweb), fecha, auditor/a.
2. **Criterios:** normativa del puesto (1.2), CIS Controls v8, ENS (RD 311/2022).
3. **Metodología:** auditoría manual (lista de comprobación) + SCA de Wazuh.
4. **Resumen ejecutivo:** % de cumplimiento manual y % de SCA por máquina.
5. **Hallazgos**, cada uno con esta ficha:

   | Campo | Ejemplo |
   |---|---|
   | ID | H-03 |
   | Descripción | srvweb no tiene actualizaciones automáticas activas |
   | Evidencia | `systemctl is-enabled unattended-upgrades` → `disabled` |
   | Criterio incumplido | CIS 7.3 · ENS `op.exp` |
   | Riesgo | **Alto** (probabilidad media × impacto alto) |
   | Recomendación | Activar `unattended-upgrades` y revisar semanalmente |
   | Responsable | Técnico de sistemas |
   | Plazo | 1 semana |

6. **Conclusión y plan de mejora priorizado** (alto → medio → bajo).

**Matriz de riesgo** sugerida para clasificar cada hallazgo:

| Impacto \ Probabilidad | Baja | Media | Alta |
|---|---|---|---|
| **Alto** | Medio | Alto | Alto |
| **Medio** | Bajo | Medio | Alto |
| **Bajo** | Bajo | Bajo | Medio |

### Ampliación — cerrar el ciclo PDCA

Aplicar una de las mejoras (p. ej. activar `unattended-upgrades` en srvweb), **relanzar el
SCA** y comparar el porcentaje **antes y después**. Documentar la subida: es la evidencia de
que la auditoría sirve para mejorar, no solo para medir.

```bash
# Ejemplo de cierre del ciclo en srvweb (ya es una acción correctiva, con permiso del docente)
sudo apt-get install -y unattended-upgrades
sudo systemctl enable --now unattended-upgrades
sudo systemctl restart wazuh-agent    # nuevo SCA → el score debería subir
```

---

## 5. Capa de IA (cómo se integra en la actividad)

- **Borrador de checklist con IA, validado a mano.** La IA convierte la normativa de la 1.2 en
  un primer checklist, pero **cada fila se valida** contra el SCA de Wazuh y contra la fuente
  (CIS o BOE). Si la IA cita un control que no existe (*alucinación normativa*) o una fila no
  indica evidencia, se descarta.
- **Rol del "auditado evasivo".** En una segunda fase la IA interpreta a alguien que responde
  con evasivas ("eso lo tenemos todo controlado"); se evalúa la capacidad del alumnado de
  **repreguntar y exigir la evidencia concreta** en vez de dar por bueno lo que se afirma.

---

## 6. Clave de corrección (profesorado)

- El checklist tiene **toda fila auditable** (evidencia + método). Penaliza ítems que "suenan
  bien" pero no se pueden comprobar.
- Cada **hallazgo se apoya en una evidencia concreta** (salida de comando o captura), no en una
  impresión.
- Coherencia **1.2 → 1.5**: lo que se audita son las cláusulas de la normativa real del grupo.
- El informe **prioriza por riesgo** y propone mejoras con responsable y plazo.
- Valorable: cruce explícito **manual ↔ SCA** y, como ampliación, el **cierre PDCA** con el
  porcentaje antes/después.
