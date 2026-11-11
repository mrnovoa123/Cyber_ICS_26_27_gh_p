---
title: "Actividad 2.1 · Cartografiando as ameazas — guion de resolución (profesorado)"
modulo: "MP5021 Incidentes de Ciberseguridade · UD2 · CA2.1"
tareas: "Tarea 2.1 (Otras taxonomías) · Tarea 2.2 (Taxonomía para la organización)"
entorno: "Sin laboratorio: trabajo documental. MITRE ATT&CK Navigator en el navegador."
---

# Actividad 2.1 · Cartografiando as ameazas

**Objetivo:** clasificar incidentes con una taxonomía profesional, compararla con otras y construir una
taxonomía propia de TecnoMariña a dos niveles. Termina con el mural de amenazas.

| Paso | Qué se hace | Tarea que sale |
|---|---|---|
| 1 | Conocer la taxonomía de referencia y clasificar casos | — |
| 2 | Comparar con otras taxonomías | **Tarea 2.1** (PDF) |
| 3 | Taxonomía propia a dos niveles con ejemplos | **Tarea 2.2** (PDF, por parejas) |
| 4 | Mural de amenazas + mapeo ATT&CK | Entregable de la actividad |

Orden fijo de la capa de IA: **producir → contrastar → decidir**. La taxonomía propia se hace sin IA y
se entrega también la versión anterior a la crítica de la IA.

---

## 1. Taxonomía de referencia

La referencia en España es la de la **Guía Nacional de Notificación y Gestión de Ciberincidentes**
(la usan INCIBE-CERT y CCN-CERT; deriva de la *Reference Security Incident Taxonomy* de ENISA / eCSIRT.net).
Tiene dos niveles: **clasificación** y **tipo de incidente**.

| Clasificación | Tipos (resumen) |
|---|---|
| Contenido abusivo | Spam · delito de odio · contenido sexual o violento inadecuado |
| Contenido dañino | Sistema infectado · servidor C&C · distribución de malware · configuración de malware |
| Obtención de información | Escaneo de red · análisis de paquetes (*sniffing*) · ingeniería social |
| Intento de intrusión | Explotación de vulnerabilidad conocida · intento de acceso con credenciales · ataque desconocido |
| Intrusión | Compromiso de cuenta con privilegios · sin privilegios · compromiso de aplicaciones · robo |
| Disponibilidad | DoS · DDoS · mala configuración · sabotaje · interrupción |
| Compromiso de la información | Acceso no autorizado · modificación no autorizada · pérdida de datos |
| Fraude | Uso no autorizado de recursos · derechos de autor · suplantación · phishing |
| Vulnerable | Criptografía débil · amplificador DDoS · servicio expuesto · revelación de información · sistema vulnerable |
| Otros | Otros · APT · ciberterrorismo · daños a infraestructuras críticas |

> Comprobad la versión vigente de la guía al empezar el curso (INCIBE-CERT / CCN-CERT). Los nombres de los tipos
> pueden variar ligeramente entre ediciones.

### Ejercicio de clasificación (respuesta orientativa)

| Caso | Clasificación → tipo | ATT&CK (táctica → técnica) |
|---|---|---|
| Correo que suplanta al banco y pide credenciales | Fraude → phishing | Initial Access → T1566 Phishing |
| `nmap -sS` desde una IP desconocida contra el servidor web | Obtención de información → escaneo | Reconnaissance → T1595 Active Scanning |
| 500 intentos SSH fallidos en 2 minutos | Intento de intrusión → acceso con credenciales | Credential Access → T1110 Brute Force |
| Login SSH correcto tras la fuerza bruta | Intrusión → compromiso de cuenta sin privilegios | Initial Access → T1078 Valid Accounts |
| Ficheros del servidor cifrados con nota de rescate | Contenido dañino → sistema infectado (+ Disponibilidad) | Impact → T1486 Data Encrypted for Impact |
| Web caída por inundación SYN | Disponibilidad → DoS | Impact → T1498 Network DoS |
| Portátil robado sin cifrar | Intrusión → robo (+ Compromiso de la información) | — (físico) |

**Clave:** un incidente puede tocar varias categorías. Se clasifica por la **principal** y se anota la secundaria
(el ransomware es «contenido dañino», pero su impacto es de disponibilidad).

---

## 2. Tarea 2.1 · Otras taxonomías

**Enunciado:** buscar otras taxonomías o catálogos de incidentes y compararlos con la de referencia.

Fuentes recomendadas (todas públicas):

| Taxonomía | Quién | Qué la caracteriza |
|---|---|---|
| RSIT (eCSIRT.net mkVI) | ENISA / comunidad CSIRT | Origen de la Guía Nacional; casi idénticas |
| VERIS | Verizon (base del DBIR) | Clasifica por **acciones** (hacking, malware, social, misuse, physical, error, environmental) y actores, activos y atributos (modelo A4) |
| NIST SP 800-61 | NIST | Gestión de incidentes; la rev. 2 clasificaba por **vector de ataque** (web, email, medios extraíbles, suplantación, uso indebido, pérdida o robo de equipo…). La rev. 3 (2025) se alinea con el CSF 2.0 |
| MITRE ATT&CK (v19, 2026) | MITRE | No es una taxonomía de incidentes sino de **técnicas del atacante** (15 tácticas Enterprise → técnicas); complementa a las demás |
| CCN-STIC 817 | CCN-CERT | Gestión de ciberincidentes en el ENS; usa la misma clasificación que la Guía Nacional y añade niveles de peligrosidad e impacto |

**Tabla de comparación que se pide** (mínimo dos taxonomías frente a la de referencia):

| Criterio | Guía Nacional | VERIS | ATT&CK |
|---|---|---|---|
| Unidad que clasifica | El incidente | La acción del incidente | La técnica del atacante |
| Niveles | 2 | Varios (acción → variedad) | Táctica → técnica → subtécnica |
| ¿Incluye errores humanos y desastres? | Parcial («Otros», mala configuración) | Sí (error, environmental) | No |
| ¿Incluye seguridad física? | Robo | Physical | No |
| ¿Sirve para notificar a un CSIRT español? | Sí (obligatoria) | No | No |
| Uso típico | Notificación y estadísticas | Estadística y análisis de brechas | Detección, *threat hunting*, mapeo de defensas |

**Corrección:** se valora que comparen **granularidad, ámbito y finalidad**, no que copien listas. Debe aparecer
al menos un incidente que encaja mal en una taxonomía y bien en otra (p. ej. un error de configuración que
expone datos: en VERIS es *error*, en la Guía Nacional queda entre «Vulnerable» y «Compromiso de la información»).

---

## 3. Tarea 2.2 · Taxonomía para la organización

**Enunciado:** por parejas, taxonomía adaptada a los incidentes posibles de TecnoMariña (30 empleados, da servicio
a un ayuntamiento), a dos niveles (categoría → tipo), con un ejemplo de cada tipo.

### Solución modelo (resumida)

| Categoría | Tipo | Ejemplo en TecnoMariña |
|---|---|---|
| **Fraude e ingeniería social** | Phishing de credenciales | Correo «verifica tu acceso al portal del ayuntamiento» |
| | Fraude del CEO / factura falsa | Petición urgente de cambio de cuenta bancaria de un proveedor |
| **Malware** | Ransomware | Cifrado del servidor de ficheros compartidos |
| | Robo de información (*stealer*) | Navegador del comercial con contraseñas guardadas exfiltradas |
| **Acceso no autorizado** | Fuerza bruta / credenciales robadas | Intentos SSH masivos contra srvweb |
| | Abuso de privilegios interno | Empleado que descarga el padrón municipal sin necesidad |
| **Ataque a aplicaciones web** | Inyección (SQLi, XSS) | Inyección SQL en el formulario de citas del portal |
| | Defacement | Página de inicio modificada |
| **Disponibilidad** | DoS / saturación | Inundación SYN contra la web de citas |
| | Fallo o mala configuración | Certificado caducado que corta el servicio |
| **Fuga o pérdida de datos** | Exfiltración | Envío de la base de datos a un servidor externo |
| | Pérdida o robo de soporte | Pendrive con datos de vecinos extraviado |
| **Reconocimiento** | Escaneo de red | `nmap` desde una IP desconocida |
| | OSINT sobre la plantilla | Recopilación de correos y cargos en redes sociales |
| **Seguridad física** | Acceso físico no autorizado | Entrada al CPD con una tarjeta ajena |
| | Daño o sabotaje | Corte del suministro eléctrico del rack |

**Criterios de corrección:**

- Dos niveles reales (no una lista plana) y un ejemplo **plausible para TecnoMariña** por tipo.
- Cobertura mínima: contenido malicioso, intrusión/acceso, disponibilidad, compromiso de la información,
  fraude y obtención de información (como pide la solución de referencia).
- Mapeo a la Guía Nacional: cada categoría propia indica a qué clasificación oficial corresponde
  (necesario para notificar en la UD5).
- Incluye seguridad física (enlaza con CA2.3 de la 2.5) y el factor interno.

---

## 4. Mural de amenazas y ATT&CK Navigator

> **ATT&CK v19 (28/04/2026):** *Defense Evasion* (TA0005) se dividió en **Stealth (TA0005)** y **Defense Impairment
> (TA0112)**; Enterprise tiene ahora **15 tácticas** y la técnica **T1562 Impair Defenses ya no existe** (p. ej. pasa a
> **T1685 Disable or Modify Tools**). El panel MITRE de Wazuh puede seguir mostrando la versión antigua: en los informes se usan
> los nombres e ID de attack.mitre.org. Corregir como error cualquier entrega que use T1562 sin indicar versión.

1. Abrir <https://mitre-attack.github.io/attack-navigator/> → *Create New Layer* → *Enterprise* (versión **v19 o posterior**:
   si aparecen 14 tácticas con *Defense Evasion*, la capa es antigua).
2. Marcar (color + puntuación) las técnicas de los ataques que se lanzarán en la 2.2 y la 2.5:

   | Ataque del laboratorio | Técnica |
   |---|---|
   | `nmap -sS` | T1595 Active Scanning / T1046 Network Service Discovery |
   | `hydra` contra SSH | T1110.001 Password Guessing |
   | Login con la credencial obtenida | T1078 Valid Accounts |
   | SQLi en DVWA | T1190 Exploit Public-Facing Application |
   | PowerShell desde Office (purple) | T1059.001 PowerShell |
   | Exfiltración por HTTP | T1048 Exfiltration Over Alternative Protocol |
   | `hping3` inundación | T1498 Network Denial of Service |

3. **Capa de cobertura** (ampliación): segunda capa con lo que el laboratorio detecta: verde = Wazuh/Suricata alertan,
   amarillo = queda en el log sin alerta, gris = sin visibilidad. Las técnicas del incidente que caen en gris o amarillo son
   las reglas que faltan. Respuesta orientativa: T1595, T1110.001 y T1059.001 en verde; T1078 (login con credencial válida)
   en amarillo (solo 5715, nivel 3, salvo la regla 100210); T1048 en gris hasta añadir la regla de Suricata de la 2.5.
4. *Layer → Export → SVG/JSON* y pegarlo en el mural (draw.io) junto a la taxonomía propia.
5. En el mural, cada amenaza lleva su impacto **C/I/D** (confidencialidad, integridad, disponibilidad).

## 5. Capa de IA (control)

- La IA **critica** la taxonomía propia (prompt de la web), no la reescribe.
- Tabla de objeciones: aceptada / rechazada / motivo. Se entrega junto a la versión previa.
- Riesgo: si la IA va primero, el alumnado reconoce en vez de clasificar.

## 6. Entregables y rúbrica rápida

| Entregable | Se valora |
|---|---|
| Tarea 2.1 (PDF) | ≥ 2 taxonomías, tabla comparativa por criterios, ejemplo de incidente que encaja mal |
| Tarea 2.2 (PDF) | 2 niveles, ejemplos plausibles, cobertura mínima, mapeo a la Guía Nacional |
| Mural | Tipos frecuentes, impacto CIA, capa ATT&CK de los ataques del laboratorio |
