---
title: Entregable B · Simulación de phishing local (aislada)
modulo: MP5021 Incidentes de Ciberseguridade · UD1 · actividad 1.2
tipo: Posible solución (profesorado) · laboratorio aislado
---

# Entregable B · Simulación de phishing local (aislada)

**MP5021 · Incidentes de Ciberseguridade — UD1, actividad 1.2 · Posible solución (profesorado)**

> Entorno 100% aislado: todo corre en una VM del laboratorio, MailHog es el único SMTP (los correos quedan retenidos), servicios en 127.0.0.1, dominios y personas ficticios. Ejercicio de concienciación, nunca contra marcas, dominios o personas reales.

Principio de aislamiento. Todo se ejecuta en una VM del laboratorio sin reenvío de puertos hacia fuera. El SMTP de salida es MailHog (no un servidor real): los correos quedan atrapados en su buzón. Dominios y usuarios ficticios ( tecnomarina.local , @example.test ); nunca dominios, marcas ni personas reales.

## 1. Preparar el entorno

MailHog (buzón trampa; SMTP en 1025 , web en 8025 ):

- Binario: descargar el release de MailHog, chmod +x mailhog && ./mailhog .
- Docker: docker run --rm -p 1025:1025 -p 8025:8025 mailhog/mailhog .
- Bandeja de entrada: http://localhost:8025 .
GoPhish (admin en https://localhost:3333 , servidor de phishing en :80 ): Descargar y descomprimir el release; ejecutar ./gophish . En el primer arranque imprime el usuario admin y una contraseña temporal: entrar y cambiarla (acepta el certificado autofirmado).

- Aislamiento: en config.json , poner admin_server y phish_server en 127.0.0.1 .
## 2. Sending Profile → apuntar a MailHog

Sending Profiles → New Profile:

- Name: MailHog-lab
- From: Soporte TI <soporte@tecnomarina.local>
- Host: localhost:1025 — Username/Password vacíos, sin TLS.
Send Test Email y comprobar que aparece en http://localhost:8025 (circuito de envío aislado y verificado).

## 3. Grupo de usuarios ficticios

Users & Groups → New Group → Plantilla-TecnoMarina : Nombre               Apellido             Email                               Posición Marisa               Gómez                marisa@example.test                 Administración Diego                Rial                 diego@example.test                  Técnico Lucía                Pena                 lucia@example.test                  Dirección

Usa los perfiles de la actividad 1.3 para que el resultado alimente el plan.

## 4. Plantilla de correo (el pretexto)

- Subject: «Acción requerida: verifica tu acceso al Portal de TecnoMariña».
- Pretexto: aviso de mantenimiento del portal interno que pide reconfirmar la contraseña
antes de 24 h (urgencia + autoridad). Insertar el enlace con {{.URL}} y el pixel {{.Tracker}} ; marcar Add Tracking Image.

## 5. Landing Page (servicio ficticio)

Landing Pages → New Page → Portal-TecnoMarina : login ficticio (usuario/contraseña). Activar Capture Submitted Data (y Capture Passwords solo con fin didáctico) para medir cuántos envían credenciales.

- Redirect to: una página de aviso educativo («esto era un simulacro de concienciación»).
- No copiar ninguna web real: diseño de portal genérico inventado.
## 6. Crear y lanzar la campaña

Campaigns → New Campaign → Simulacro-UD1 .

- Email Template: Aviso-portal · Landing Page: Portal-TecnoMarina.
- URL: http://localhost (servidor de phishing de GoPhish).
- Sending Profile: MailHog-lab · Groups: Plantilla-TecnoMarina · Launch.
## 7. Seguir el flujo (como “víctima” de prueba)

1. Abrir http://localhost:8025 (MailHog): los correos están retenidos.
2. Abrir el correo y pulsar el enlace → llega a la landing de GoPhish.
3. Introducir credenciales ficticias y enviar → GoPhish registra «Submitted Data» y redirige al
aviso educativo.

4. Repetir con otro usuario para generar datos.
## 8. Resultados y KPIs (en GoPhish)

En Campaigns → Simulacro-UD1: Email Sent , Opened , Clicked Link , Submitted Data , Reported .

Tasa de apertura = abiertos / enviados. Tasa de clic = clics / enviados → KPI línea base del plan de la actividad 1.3. Tasa de envío de credenciales = submitted / enviados (el más grave). Export CSV para el informe.

## 9. El informe (estructura del entregable)

1. Pretexto: asunto, gancho de urgencia/autoridad, remitente ficticio.
2. Página anzuelo: captura de la landing, datos capturados y redirección.
3. Usuarios objetivo: lista ficticia y perfiles (dirección/técnicos/administración).
4. Resultados: tabla enviados/abiertos/clics/credenciales + las tres tasas; capturas de
GoPhish y MailHog.

5. Medidas de concienciación derivadas: una acción por debilidad (p. ej. clic alto en
administración → píldora sobre remitentes y MFA; envío de credenciales → taller de gestor de contraseñas), enlazadas al plan de la 1.3.

## 10. Verificación de aislamiento y limpieza

Todos los correos en MailHog y ninguno hacia fuera (MailHog es el único SMTP).

- Servicios en 127.0.0.1 : ss -ltnp | grep -E '1025|8025|3333|:80' .
- Al terminar: detener GoPhish y MailHog (con Docker --rm el contenedor se borra solo).
Errores que invalidan el ejercicio (útiles para la rúbrica): usar dominio o logotipo reales; From con un dominio existente; apuntar el Sending Profile a un SMTP real; publicar la landing fuera de localhost .

en entorno de laboratorio aislado.

---

*Documento interno de profesorado · solo versión con soluciones.*
