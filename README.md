# LSI · Práctica 1 · Guía paso a paso para la defensa

UDC · Curso 2026 · Actualizado el **10 de octubre de 2026**.

Esta guía recoge lo realizado en la VM de laboratorio y las comprobaciones aportadas. Cada apartado separa los pasos, su explicación, los resultados y lo que sigue pendiente. Las IP corresponden a esta máquina: otro alumno debe usar las asignadas por el profesor.

## Cómo usar la guía

1. Abre el apartado que te pida el profesor.
2. Explica su objetivo y los archivos implicados.
3. Muestra los comandos de consulta y relaciona la salida con los resultados documentados.
4. Utiliza «Para la defensa» para justificar las decisiones.

**No ejecutes todos los bloques de forma seguida.** Los cambios de repositorios, borrados y modificaciones de red describen operaciones ya realizadas; no son tareas pendientes para volver a aplicar. `su -` permite entrar como root. La configuración y comprobación de `sudo` con el usuario normal siguen pendientes.

## Primera parte: índice por apartados

| Apartado | Guía | Estado y límite de lo comprobado |
| --- | --- | --- |
| a | [Configuración básica: red, nombres, DNS, APT y sudo](guia/a-configuracion.md) | Red/DNS trabajados; sudo pendiente |
| b | [Actualización de Debian](guia/b-actualizacion.md) | Saltos 10 → 11 → 12 → 13 comprobados |
| c | [Arranque, targets, servicios y unidades](guia/c-systemd.md) | Estudiado; incidencia de ssa sin resolver ni modificar |
| d | [Medición del arranque](guia/d-tiempos.md) | Medidas iniciales y actuales; última: 17,356 s |
| e | [Errores del journal y contraste de la IA](guia/e-errores.md) | Diagnóstico y corrección de logrotate comprobados |
| f | [Segunda interfaz y dirección lógica](guia/f-interfaces.md) | Dirección adicional creada, probada y eliminada; revisar amplitud del enunciado |
| g | [Rutas y ruta estática](guia/g-rutas.md) | Alta y selección de ruta comprobadas; no persistente |
| h | [Limpieza y configuración que permanece](guia/h-limpieza.md) | Estado revisado; copias sobrantes eliminadas según confirmación del alumno |
| i | [Bot de Telegram al arrancar](guia/i-bot.md) | Bot definitivo operativo, habilitado y comparado con cron |
| j | [Conexiones abiertas](guia/j-conexiones.md) | Inventario e interpretación incorporados desde las salidas de k) y l) |
| k | [Monitorización en tiempo real](guia/k-monitorizacion.md) | top, free y watch con ss comprobados |
| l | [TCP Wrappers y registro de denegaciones](guia/l-tcp-wrappers.md) | Pruebas verificadas; política permanente confirmada por el alumno, falta comprobación final y ampliar orígenes |
| m | [Logs locales: rsyslog y journald](guia/m-logs-locales.md) | Mismo mensaje recuperado por ambas vías |

## Estado final que hay que saber explicar

| Elemento | Estado documentado |
| --- | --- |
| Sistema | Debian 13.7, amd64; kernel `6.12.111+deb13-amd64` |
| Inicio | `multi-user.target`, sin escritorio |
| Interfaz principal | `ens33`: `10.11.49.56/23`; gateway `10.11.48.1` |
| Segunda interfaz | `ens34`: `10.11.51.56/23` |
| Administración | SSH habitual por el puerto 22; sin aprobación Telegram |
| Control de acceso SSH | TCP Wrappers permite `10.30.13.239` y `10.11.49.57`, deniega los demás; aplicación final confirmada por el alumno |
| Bot definitivo | `lsi-companion.service`: curiosidad al arrancar y consultas de recursos |
| Curiosidades | Fuente externa Useless Facts; traducción automática MyMemory; no lista fija ni generación con LLM en ejecución |
| Logs | Journal persistente; rsyslog y registro específico `/var/log/denegados` verificados |
| Swap | Partición `/dev/sda5`, unos 1,5 GiB, activación normal |
| Tiempo de arranque | Último informe: 6,891 s + 10,465 s = 17,356 s |
| Recuperación | El alumno no dispone de consola de recuperación; la gestionan los profesores |

La meta personal de 10–12 segundos **no se alcanzó** y no es un requisito literal del enunciado. Se dejó esa optimización para el final. Las duraciones varían entre reinicios: no se atribuye todo el ahorro a un único servicio.

## Código y evidencias

- [Código del bot definitivo](companion/bot.py).
- [Unidad de systemd utilizada](companion/lsi-companion.service).
- [Pruebas locales del bot](companion/test_bot.py).
- [Guion de demostración para la defensa](guia/defensa.md).

Los resultados escritos provienen de las salidas compartidas y de las confirmaciones del alumno. No se publican tokens, contraseñas, archivos privados de vinculación ni registros personales completos. Los archivos de configuración nuevos respetan la instrucción del enunciado de no añadir comentarios; las explicaciones están en Markdown.

La actualización adicional del 10/10/2026 integra `bitacora_lsi_p1.md`: conexiones, monitorización, logs locales y TCP Wrappers. Se han consolidado sus entradas cronológicas para distinguir el estado final de los ensayos intermedios. La IP de la VM compañera está identificada; siguen pendientes su IP de VPN y el origen autorizado desde Wi-Fi UDC. La última aplicación de la política de acceso fue confirmada verbalmente, sin nueva salida de los archivos. Consulta [los pendientes actualizados](guia/pendientes.md).

Se documenta el estado definitivo, sin reinstalar ni convertir las pruebas abandonadas en pasos de la guía. El historial de Git conserva las versiones anteriores de los apuntes.

## Segunda parte

NTPSec con un compañero, rsyslog cliente/servidor, auditoría con IA, espacio en disco y Splunk están en [el listado de pendientes](guia/pendientes.md). La limpieza ya realizada servirá como antecedente, pero no acredita por sí sola que esa segunda parte esté completada.
