# h) Limpieza: cambios que permanecen y su justificación

[Volver al índice](../README.md)

Esta es una descripción del estado comprobado, no un script de purga general. Se administra una VM de profesores por SSH, sin consola de recuperación disponible para el alumno.

## Paso 1. Inventariar antes de retirar

```bash
systemctl list-units --type=service --state=running --no-pager
systemctl list-unit-files --type=service --no-pager
systemd-analyze blame --no-pager
systemd-analyze critical-chain multi-user.target
```

Se decidió prescindir del escritorio porque el uso era por terminal/SSH. Se revisaron paquetes antes de ejecutar el script local de limpieza y después se ejecutó `apt autoremove`. No se reproduce aquí la lista de purga como una orden para cualquier máquina.

## Paso 2. Retirar el escritorio y conservar el sistema necesario

Se retiraron componentes de GNOME/GDM, aplicaciones gráficas, juegos y dependencias. En el inventario posterior constaban también retirados NetworkManager, wpasupplicant, fwupd y otros componentes de escritorio. `networking.service` e ifupdown siguieron configurando las interfaces.

Se conservan SSH, kernel, GRUB, udev, D-Bus, ifupdown, swap, journald, rsyslog, sincronización horaria y herramientas de VMware. `strace` se utilizó para diagnóstico: tenerlo instalado no equivale a tener un servicio suyo ralentizando el arranque.

Se estableció `multi-user.target`. Hubo verificaciones de `dpkg --audit`, nuevas conexiones SSH y reinicios correctos; no se debe inferir que cualquier futura propuesta de autoremove sea segura sin revisar sus paquetes.

## Paso 3. Revisar las máscaras que siguen aplicadas

El informe del 10 de octubre confirma máscaras en:

```text
ModemManager.service
apparmor.service
avahi-daemon.service
avahi-daemon.socket
e2scrub_reap.service
exim4.service
```

También se habían bloqueado NetworkManager y wpasupplicant antes de su retirada. La ausencia de una unidad en `systemd-delta` no acredita por sí sola su estado de ejecución.

| Decisión | Justificación y límite |
| --- | --- |
| ModemManager y descubrimiento Avahi | No se necesitaban para la red estática utilizada |
| Exim | No se utilizaba correo en esta etapa; no equivale a demostrar que no queden tareas relacionadas |
| e2scrub_reap | Se bloqueó en esta VM sin LVM; no se eliminaron por ello todos los mecanismos de comprobación de ext4 |
| AppArmor | Se bloqueó durante la optimización; **reduce protección** y no se demostró una ganancia aislada de tiempo |

No se debe explicar que AppArmor sea «basura» o inútil por ser una VM. El estado actual es una decisión de la práctica, no una recomendación general. No se restauró durante esta limpieza final.

## Paso 4. Conservar el ajuste de espera de red

Archivo `/etc/systemd/system/ifupdown-pre.service.d/90-lsi-red.conf`:

```ini
[Service]
ExecStart=
ExecStart=/bin/sh -c '/bin/udevadm wait --timeout=30 /sys/class/net/ens33 /sys/class/net/ens34 || /bin/udevadm settle --timeout=120'
```

Sustituye la espera general por una espera a ambas interfaces y conserva la espera general como respaldo. El primer `ExecStart=` vacía la definición anterior. El archivo del paquete no se edita directamente.

La activación de ifupdown-pre pasó de unos cuatro segundos a unos 0,08–0,10 s en las salidas comparadas. Eso no implica restar cuatro segundos al arranque total, porque el cuello de botella puede cambiar.

Se apartaron scripts de `/etc/network/if-pre-up.d/` y `/etc/network/if-up.d/` relacionados con wireless-tools, wpasupplicant, ethtool, resolved y avahi-autoipd. Los respaldos permanecen en `/root/lsi-hooks-red-*` y `/root/lsi-hooks-extra-*`. Esta decisión debe revisarse si se cambia a Wi-Fi, DHCP u otra gestión de DNS. La desaparición de la ruta IPv4 link-local fue comprobada; no se aisló un ahorro total debido a esos scripts.

`networking.service` conserva sus órdenes normales de ifup/ifdown y no muestra un override adicional en el inventario final.

## Paso 5. Revisar impresión, regla de disco y módulos

Enlaces confirmados:

```text
/etc/modules-load.d/cups-filters.conf -> /dev/null
/etc/udev/rules.d/85-hdparm.rules -> /dev/null
```

El primero evita la carga estática solicitada por ese archivo para `lp`, `ppdev` y `parport_pc`, vinculados a impresión/puerto paralelo. No se utiliza esa impresión en la VM. No equivale a una prohibición absoluta de cargar esos módulos por cualquier otro medio.

El segundo desactiva la regla homónima de hdparm para el disco virtual. No cambia las particiones ni elimina el controlador SATA.

Contenido final de `/etc/modprobe.d/90-lsi-vm.conf`:

```text
blacklist intel_uncore
blacklist intel_cstate
blacklist sb_edac
```

Se habían observado problemas al cargar esos módulos de monitorización del hardware físico en la VM. `blacklist` afecta a su carga automática por alias; no es una desactivación universal. No hay una medición que aísle el ahorro de ese archivo.

Se regeneró el initramfs con `update-initramfs -u -k "$(uname -r)"` y se comprobaron `ahci`, `sd_mod` y `ext4` dentro de la imagen. El inventario final de `/etc/initramfs-tools/modules` contiene solo sus comentarios originales, sin cargas forzadas añadidas.

## Paso 6. Confirmar swap y logs

```bash
cat /etc/fstab
swapon --show
systemd-analyze cat-config systemd/journald.conf --no-pager
```

La swap conserva `/dev/sda5 none swap sw 0 0`, aproximadamente 1,5 GiB, activa. Journal mantiene almacenamiento persistente observado en `/var/log/journal`; no consta `Storage=volatile` aplicado en la configuración final. La configuración del proveedor incluye `ForwardToSyslog=yes` y rsyslog se conserva.

Los archivos de journal dieron `PASS` al verificarse. No se justifica borrarlos por una corrupción que no se detectó. La corrección de CUPS/logrotate está en [e)](e-errores.md).

El informe también muestra un override `/etc/tmpfiles.d/tmp.conf` y otros cambios del sistema. No se atribuyen a nuestra limpieza ni se borran automáticamente: no se ha determinado su procedencia.

## Paso 7. Eliminar copias sobrantes, no archivos de arranque

Con el initramfs principal existente y el nuevo bot activo, se proporcionó una limpieza de rutas exactas. El alumno confirmó su ejecución y que el bot seguía funcionando. Entre los archivos retirados estaban dos copias antiguas de initramfs bajo `/root`, de unos 53 MB cada una, y copias de fstab/módulos de pruebas ya cerradas. También se retiraron instaladores del bot y archivos archivados del proyecto anterior.

**El ahorro aproximado de 106 MB procede de las dos copias, no de una medición de `df` posterior publicada.** No se borró el initramfs de `/boot`, kernels activos, credenciales del bot ni claves SSH. Borrar copias que no se cargan al arrancar libera espacio, no reduce por sí mismo segundos de arranque.

Se conservaron respaldos que aún pueden servir para recuperar configuraciones modificadas: `lsi-hooks-*`, `lsi-limpieza`, `lsi-respaldo-impresion` y `respaldo-logrotate`. No se publican sus contenidos privados.

## Para la defensa

Explicar por separado: paquetes retirados, servicios bloqueados, archivos de configuración que permanecen y copias sobrantes borradas. Distinguir una mejora comprobada de una hipótesis. El estado final sigue arrancando y permite SSH; no se alcanzó el objetivo personal de 10–12 s.
