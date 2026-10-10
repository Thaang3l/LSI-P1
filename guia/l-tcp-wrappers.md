# l) Filtrado SSH con TCP Wrappers y registro de denegaciones

[Volver al índice](../README.md) · [Registro local](m-logs-locales.md)

**Estado final comunicado el 10/10/2026:** política permanente aplicada según la respuesta «listo» del alumno recogida al final de `bitacora_lsi_p1.md`. No se aportó una nueva captura de los archivos después de esa última aplicación. La compatibilidad, las simulaciones, el registro y un rechazo real sí cuentan con salidas previas. Faltan la comprobación posterior de la política final y las direcciones adicionales de VPN/Wi-Fi.

Este capítulo documenta lo hecho. **No ejecutar todos los bloques otra vez:** la VM se administra por SSH y la recuperación depende de los profesores. La política descrita permite dos IP concretas; si cambia la dirección VPN, puede impedir nuevas conexiones. No se ha modificado el acceso mediante Telegram: el bot sigue siendo independiente.

## Paso 1. Verificar la compatibilidad real

```bash
ldd /usr/sbin/sshd | grep -i libwrap
ldd /usr/lib/openssh/sshd-session | grep -i libwrap
dpkg -l openssh-server libwrap0
```

La primera consulta no devolvió nada. La segunda mostró:

```text
libwrap.so.0 => /lib/x86_64-linux-gnu/libwrap.so.0
```

El paquete informado en esta sesión fue `openssh-server 1:10.0p1-7+deb13u4`, y `libwrap0 7.6.q-36`. Es el dato de esa consulta; no se fuerza su coincidencia con otras cadenas de versión antiguas de la conversación.

En esta instalación la integración está en `sshd-session`, aunque las reglas emplean el nombre **`sshd`**. No bastaba inspeccionar el binario principal para descartar TCP Wrappers. La evidencia funcional más fuerte fue el rechazo real posterior.

## Paso 2. Respaldar e instalar las herramientas

Se crearon copias de los archivos originales:

```bash
mkdir -p /root/lsi-tcpwrappers-respaldo
cp -a /etc/hosts.allow /etc/hosts.deny /root/lsi-tcpwrappers-respaldo/
```

En ese momento solo tenían comentarios originales. No repetir esa copia sobre el mismo respaldo después de instalar reglas restrictivas: se perdería el estado anterior.

`command -v tcpdmatch` y `command -v tcpdchk` inicialmente no devolvieron rutas. Se comprobó el candidato y se instaló:

```bash
apt-cache policy tcpd
apt install tcpd
command -v tcpdmatch
command -v tcpdchk
```

Se instaló `tcpd 7.6.q-36`; aparecieron `/usr/sbin/tcpdmatch` y `/usr/sbin/tcpdchk`. Son herramientas, no un nuevo servidor escuchando.

## Incidencia: libwrap estaba vacía

Al ejecutar `tcpdchk -d -v` apareció:

```text
error while loading shared libraries: /lib/x86_64-linux-gnu/libwrap.so.0: file too short
```

Diagnóstico realizado:

```bash
ls -l /lib/x86_64-linux-gnu/libwrap.so.0*
readlink -f /lib/x86_64-linux-gnu/libwrap.so.0
file -L /lib/x86_64-linux-gnu/libwrap.so.0
dpkg -V libwrap0
df -h / /usr /var
df -i /
```

El enlace apuntaba a `libwrap.so.0.7.6`, que tenía **0 bytes**; `file` respondió `empty` y `dpkg -V` mostró `??5??????`, discrepancia del checksum. Había 8,5 GB disponibles y 10 % de inodos usados: no se observó agotamiento de almacenamiento. El error precedía al análisis de reglas. No se determinó qué había truncado el archivo.

La reparación indicada fue `apt install --reinstall libwrap0`. No quedó pegada la salida de APT, pero **sí se verificó el resultado**: biblioteca de 47 KB, tipo ELF 64 bits válido y `dpkg -V libwrap0` sin salida. Se pudo continuar con las herramientas. No atribuir el daño a la instalación de tcpd sin pruebas.

## Paso 3. Simular antes de modificar el acceso real

En `/root/lsi-tcpwrappers-prueba`, se probaron archivos locales:

```text
hosts.allow: sshd: 10.30.13.239
hosts.deny:  sshd: ALL
```

Estas dos líneas resumen **dos archivos distintos**, no son un bloque para copiar literalmente. Desde ese directorio:

```bash
tcpdchk -d -v
tcpdmatch -d sshd 10.30.13.239
tcpdmatch -d sshd 192.0.2.10
```

Se obtuvo `granted` para la primera IP y `denied` para la segunda. `-d` usa los archivos del directorio de prueba; no aplica el filtrado al servidor. `192.0.2.10` es una dirección de documentación, no un intruso observado.

La búsqueda consulta primero hosts.allow y después hosts.deny; sin coincidencia en ninguno, permite el acceso. Esta precedencia está descrita en [hosts_access(5) de Debian](https://manpages.debian.org/trixie/libwrap0/hosts_access.5.en.html).

## Paso 4. Crear el registro de rechazos

Archivo instalado `/etc/rsyslog.d/30-lsi-denegados.conf`:

```text
if ($programname == "LSI_TCP_DENEGADO") then {
    action(type="omfile" file="/var/log/denegados" template="RSYSLOG_FileFormat")
}
```

La configuración principal incluía `/etc/rsyslog.d/*.conf`. Se validó antes de reiniciar únicamente rsyslog:

```bash
rsyslogd -N1
systemctl restart rsyslog
systemctl is-active rsyslog
logger -p authpriv.notice -t LSI_TCP_DENEGADO "PRUEBA de registro SSH denegado desde 192.0.2.10"
tail -n 5 /var/log/denegados
```

La validación terminó correctamente, el servicio quedó `active` y apareció la entrada de prueba a las 17:58:54. **Era un mensaje artificial**, no una conexión rechazada. Al no incorporar `stop`, el evento puede continuar hacia las reglas generales, incluida auth.log. No se ha acreditado una regla de rotación específica para este archivo nuevo.

## Paso 5. Comprobar un rechazo real

Se ensayó temporalmente una denegación solo para `127.0.0.1`, con `spawn` llamando a `logger` y la etiqueta anterior. Se verificó con `tcpdchk` y `tcpdmatch` que loopback quedaba denegado y la IP VPN permitida.

Se intentó SSH local por IPv4 con un límite de cinco segundos. El cliente indicó un timeout durante el intercambio del banner. Ese error aislado sería ambiguo, pero el registro añadió automáticamente:

```text
2026-10-10T18:22:14.253650+02:00 debian LSI_TCP_DENEGADO: SSH rechazado desde 127.0.0.1
```

Esto aportó evidencia de la integración TCP Wrappers → logger → rsyslog. La regla exclusiva de loopback se retiró al terminar. Se resume esta prueba para justificar el filtrado; no es la configuración vigente ni un paso a repetir ahora.

## Paso 6. Validar la lista autorizada

Se ensayó permitir `10.30.13.239` y denegar el resto para `sshd`, con un respaldo y temporizadores transitorios de recuperación. `tcpdchk -v` enumeró ambas reglas y `tcpdmatch` permitió la IP VPN y denegó `192.0.2.10`.

El alumno confirmó que abrió una **nueva** sesión desde CMD de Windows y restauró los archivos. Las consultas posteriores no mostraron reglas activas ni temporizadores de recuperación tras detener el timer v2. Esto validó el ensayo y su retirada; no demuestra una conexión real desde la IP documental de prueba.

Los temporizadores de ese ensayo ya no estaban pendientes en la última comprobación. No se deben considerar una recuperación activa de la política final.

## Paso 7. Política permanente comunicada

Después del ensayo, el alumno decidió mantener el filtrado y comunicó la VM del compañero `10.11.49.57`. Recibió las reglas y confirmó «listo».

Contenido activo comunicado de **`/etc/hosts.allow`**, conservando sus comentarios originales:

```text
sshd: 10.30.13.239, 10.11.49.57
```

Contenido activo comunicado de **`/etc/hosts.deny`**, conservando sus comentarios originales:

```text
sshd: ALL: spawn /usr/bin/logger -p authpriv.notice -t LSI_TCP_DENEGADO "SSH rechazado desde %a" : deny
```

`%a` se sustituye por la dirección del cliente; `spawn` ejecuta el registro y `deny` deniega. Rsyslog añade fecha, hora y host. Véase [hosts_options(5)](https://manpages.debian.org/trixie/libwrap0/hosts_options.5.en.html).

La autorización es por **IP de origen**, no por identidad de una persona ni por su contraseña. Permitir la VM del compañero no permite automáticamente su portátil por VPN. SSH sigue exigiendo su autenticación normal a los orígenes permitidos. La política no equivale a un firewall y no afecta automáticamente a otros servicios incompatibles con libwrap.

### Qué queda pendiente

- Comprobar con salidas la configuración posterior a la confirmación final, y una conexión nueva con esa política exacta.
- Obtener la IP de VPN del compañero y el origen o rango autorizado del Wi-Fi universitario.
- Revisar qué ocurre cuando cambia la IP VPN del alumno. No se ha demostrado que `10.30.13.239` sea fija.
- Probar desde la VM compañera: su dirección se comunicó, pero no se aportó una sesión real desde ella.
- Revisar la rotación de `/var/log/denegados` si se conserva a largo plazo.

Consultas de verificación propuestas para la defensa; **no se han vuelto a ejecutar después de la aplicación final**:

```bash
grep -vE '^[[:space:]]*(#|$)' /etc/hosts.allow /etc/hosts.deny
tcpdchk -v
tcpdmatch sshd 10.30.13.239
tcpdmatch sshd 10.11.49.57
tcpdmatch sshd 192.0.2.10
tail -n 5 /var/log/denegados
```

## Servicios compatibles y explicación para la defensa

`apt-cache rdepends --installed libwrap0` enumeró openssh-server, tcpd, pulseaudio y libsnmp40t64. Una dependencia de paquete no demuestra un servicio activo ni cobertura de todos sus ejecutables. La muestra de `ss -tulnp` solo mostró sockets de SSH y su sesión. La compatibilidad verificada funcionalmente fue la de SSH.

TCP Wrappers consulta permisos dentro de servicios compatibles. Un firewall, por ejemplo nftables, filtra tráfico en la pila de red sin requerir esa integración. `tcpdmatch` simula una decisión, mientras que la entrada automática del intento real de loopback prueba el registro del rechazo. No confundir el host que escribe el log con la identidad del equipo/persona que intenta acceder.
