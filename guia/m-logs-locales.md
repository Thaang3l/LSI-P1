# m) Probar el registro local con rsyslog y journald

[Volver al índice](../README.md)

**Estado:** comprobado el 10/10/2026 mediante el mismo evento recuperado por ambos mecanismos, según las salidas recogidas en la bitácora del alumno. Es registro local; no acredita el reenvío entre dos máquinas de la segunda parte.

## Paso 1. Comprobar los servicios

Como root:

```bash
systemctl status rsyslog --no-pager -l
systemctl status systemd-journald --no-pager -l
dpkg -l rsyslog
ls -l /var/log/syslog
```

Resultados observados:

- `rsyslog.service`: habilitado y `active (running)`; paquete `8.2504.0-1+deb13u2`.
- `systemd-journald.service`: `static` y `active (running)`; static no significa detenido.
- Journal persistente en `/var/log/journal/`, unos 99,7 MB en ese momento.
- `/var/log/syslog` existía, propietario `root:adm`, permisos 0640 y unos 4,75 MB.
- Rsyslog indicó que había recibido de systemd el socket `/run/systemd/journal/syslog`.

La advertencia de que el journal había rotado indicaba que la salida de `status` podía ser incompleta; no demostraba una caída. Que exista syslog tampoco demuestra todavía que haya recibido nuestro evento de prueba.

## Paso 2. Emitir un evento identificado

```bash
logger -t LSI-P1-M -p user.notice "Prueba de registro local del apartado m"
```

`-t` añade la etiqueta `LSI-P1-M`; `-p user.notice` elige facility `user` y severidad `notice`. El texto es un evento artificial deliberado para comprobar el recorrido del mensaje.

## Paso 3. Recuperarlo por las dos vías

```bash
grep 'LSI-P1-M' /var/log/syslog | tail -n 5
journalctl -t LSI-P1-M -n 5 --no-pager
```

Salida del archivo de texto:

```text
2026-10-10T15:23:17.219033+02:00 debian LSI-P1-M: Prueba de registro local del apartado m
```

Salida del journal:

```text
oct 10 15:23:17 debian LSI-P1-M[1267]: Prueba de registro local del apartado m
```

Coinciden hora, máquina, etiqueta y mensaje. El journal también presenta el PID del emisor. Esta correlación verifica la recepción local, sin necesidad de instalar ni reiniciar servicios para la prueba.

## Para la defensa

Journald conserva eventos estructurados consultables con `journalctl`. Rsyslog procesa mensajes y puede escribir archivos o reenviarlos; aquí se verificó su escritura local. Pueden coexistir. El registro de rechazos SSH añadido posteriormente se documenta en [l)](l-tcp-wrappers.md).

Consultas complementarias propuestas, sin nueva salida en esta parte:

```bash
journalctl -b -n 15 --no-pager
journalctl -b -p err --no-pager
journalctl --disk-usage
```

No hace falta repetir instalaciones para mostrar este apartado: basta explicar el evento identificado y recuperar sus registros, o generar otro evento de demostración claramente etiquetado.
