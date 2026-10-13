# Bitácora completa de la práctica 1

Esta es la versión extensa y reproducible de la práctica. Está escrita para poder seguir el trabajo desde el principio y defender por qué se ejecutó cada orden.

## Cómo leerla

- **Ejecutado**: el alumno pegó la orden o confirmó expresamente su ejecución.
- **Resultado observado**: salida real aportada durante la práctica.
- **Propuesto**: orden explicada, pero sin salida que demuestre su ejecución.
- **Prueba temporal**: cambio usado para aprender o diagnosticar y retirado después.
- **Vigente**: cambio confirmado en el último inventario de la VM.
- **Retirado**: no forma parte de la configuración final y no debe repetirse como si siguiera activo.

Las contraseñas, el token de Telegram y otros secretos quedan fuera. En la edición pública, las IP internas y los identificadores de Telegram se sustituyen por nombres como `IP_VM_ENS33` o `TELEGRAM_USER_ID`. Los PID, puertos de cliente y tiempos son históricos: cambiarán en otras ejecuciones.

> Esta bitácora conserva deliberadamente los fallos, las pruebas y sus correcciones. Un comando mostrado dentro de una incidencia no debe copiarse sin leer antes su estado y la explicación posterior.

## Índice

- [a) Configuración básica](#apartado-a-configuracion-basica)

- [b) Actualización de Debian](#apartado-b-actualizacion-de-debian)

- [c) Arranque, targets y unidades](#apartado-c-arranque-targets-y-unidades)

- [d) Medición de tiempos de arranque](#apartado-d-medicion-de-tiempos-de-arranque)

- [e) Errores del journal y logrotate](#apartado-e-errores-del-journal-y-logrotate)

- [f) Segunda interfaz y dirección temporal](#apartado-f-segunda-interfaz-y-direccion-temporal)

- [g) Tabla de rutas y ruta temporal](#apartado-g-tabla-de-rutas-y-ruta-temporal)

- [h) Limpieza y optimización](#apartado-h-limpieza-y-optimizacion)

- [i) Compañero de Telegram](#apartado-i-compañero-de-telegram)

- [j) Puertos y conexiones](#apartado-j-puertos-y-conexiones)

- [k) Monitorización](#apartado-k-monitorizacion)

- [l) TCP Wrappers](#apartado-l-tcp-wrappers)

- [m) Logs locales](#apartado-m-logs-locales)

- [Anexo A: apuntes cronológicos iniciales](#anexo-a-apuntes-cronologicos-iniciales)

- [Anexo B: bitácora aportada por el alumno](#anexo-b-bitacora-aportada-por-el-alumno)


---

## Apartado a) — Configuración básica


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


## Objetivo

Comprender dónde se configura la red, cómo resuelve nombres la máquina y de dónde obtiene sus paquetes. Red y resolución se han trabajado; la configuración de sudo todavía necesita comprobarse.

## Paso 1. Identificar las interfaces y rutas

```bash
ip -br addr
ip route
cat /etc/network/interfaces
```

Se configuró una interfaz hacia la red principal y otra hacia la segunda red. Estado aplicado:

```text
auto lo ens33 ens34

iface lo inet loopback

iface ens33 inet static
    address IP_VM_ENS33
    netmask 255.255.254.0
    broadcast BROADCAST_ENS33
    network RED_ENS33
    gateway GATEWAY_ENS33

iface ens34 inet static
    address IP_VM_ENS34
    netmask 255.255.254.0
    broadcast BROADCAST_ENS34
    network RED_ENS34
```

Se corrigió una errata `addres` → `address`. La asignación de `ens34` se utilizó y se verificó en la máquina; no se aporta una confirmación independiente de la asignación del profesor.

| Dato | Explicación |
| --- | --- |
| `/23` | Equivale a `255.255.254.0`; agrupa dos bloques consecutivos del tercer octeto |
| Red `RED_ENS33/23` | Incluye `10.11.48.x` y `10.11.49.x` |
| IP `IP_VM_ENS33` | Dirección del equipo, distinta de la dirección de red |
| Broadcast `BROADCAST_ENS33` | Última dirección de esa subred |
| Gateway `GATEWAY_ENS33` | Router configurado; no se obtiene automáticamente sumando uno a la red |
| Red `RED_ENS34/23` | Incluye tanto `10.11.50.x` como `10.11.51.x` |

**Respuesta breve:** que `network` termine en `.48.0` no obliga a que todas las IP tengan `.48` en el tercer octeto.

## Paso 2. Aplicar y comprobar la red

Durante la configuración se usaron `ifup --no-act` y el reinicio de networking. Son operaciones históricas: reiniciar la red desde SSH puede cortar la conexión; no hace falta repetirlo para defender la práctica.

Para demostrar el estado sin cambiarlo:

```bash
ip -br addr
ip route
ping -c 3 GATEWAY_ENS33
```

El router respondió sin pérdida. Ambas IP figuraban con `/23`. `UNKNOWN` en una interfaz virtual no significó ausencia de enlace: también se observaron `UP,LOWER_UP` y conectividad en la principal.

La red definitiva se gestiona con **ifupdown**, a través de `networking.service`. NetworkManager fue retirado después, en el apartado h).

## Paso 3. Analizar /etc/hosts

```bash
cat /etc/hosts
getent hosts debian
getent ahostsv4 debian
```

Inicialmente el nombre `debian` estaba asociado a `127.0.1.1`. Se cambió esa asociación a:

```text
IP_VM_ENS33 debian
```

La asociación quedó recogida en el inventario usado en la anterior actualización de los apuntes. Se conservan `localhost` y las entradas IPv6 originales. No se sustituye la palabra `debian` por una IP: el formato es **dirección, seguida de nombre**.

`getent hosts` llegó a mostrar IPv6 locales. No demostraba por sí solo un fallo: consulta las fuentes configuradas en NSS. `getent ahostsv4` permite centrarse en IPv4; STREAM, DGRAM y RAW no son tres máquinas diferentes.

## Paso 4. Reparar DNS

```bash
cat /etc/resolv.conf
host archive.debian.org DNS_AULA_1
host archive.debian.org DNS_AULA_2
host archive.debian.org DNS_AULA_3
host archive.debian.org DNS_UDC_1
host archive.debian.org DNS_UDC_2
```

APT no resolvía nombres. Se probaron los DNS individualmente: los tres `10.8.12.x` agotaron el tiempo; `DNS_UDC_1` y `DNS_UDC_2` sí contestaron consultas DNS. Un ping sin respuesta a un DNS no demuestra que su servicio DNS esté caído.

Se conservaron las cinco direcciones a petición del alumno, poniendo primero las que respondían:

```text
domain udc.pri
search udc.pri
nameserver DNS_UDC_1
nameserver DNS_UDC_2
nameserver DNS_AULA_1
nameserver DNS_AULA_2
nameserver DNS_AULA_3
```

El resolvedor tradicional de glibc usa hasta tres entradas `nameserver`; escribir cinco no hace que consulte las cinco. `domain` y `search` son alternativas del resolvedor: prevalece la última; aquí coinciden. `search` completa nombres cortos con el dominio.

Comprobación que volvió a funcionar:

```bash
getent ahostsv4 archive.debian.org
getent ahostsv4 deb.debian.org
```

Las IP devueltas por esos servidores pueden cambiar. No deben fijarse a mano para solucionar APT.

## Paso 5. Revisar NSS y APT

```bash
cat /etc/nsswitch.conf
cat /etc/apt/sources.list
```

Línea de resolución de hosts del inventario posterior a la limpieza:

```text
hosts: files mdns4_minimal [NOTFOUND=return] dns
```

`files` consulta `/etc/hosts`; el módulo mDNS resuelve su ámbito local; la condición actúa sobre su resultado; `dns` consulta DNS. Inicialmente figuraba también `myhostname`, retirado después junto con su paquete. Las bases `passwd`, `group`, etc. tienen sus propias fuentes: `files` no siempre significa `/etc/hosts`.

`sources.list` define los repositorios. Su evolución y errores se explican en [b)](b-actualizacion.md).

## Paso 6. Sudo: pendiente

Se ha administrado la máquina con `su -`. Eso **no demuestra** que `lsi` tenga sudo configurado. Para retomarlo habrá que revisar, sin asumir que ya está resuelto:

```bash
id lsi
command -v sudo
```

Y desde una sesión normal de `lsi`, si está instalado, comprobar `sudo -l`. No se añade una regla de sudo ni se publica una contraseña en estos apuntes.

## Para la defensa

- Diferenciar IP del host, red, broadcast y gateway.
- Explicar por qué `.49.56` pertenece a la red `.48.0/23`.
- Separar conectividad con el router de resolución DNS.
- Relacionar `hosts`, `resolv.conf` y `nsswitch.conf` sin confundir sus funciones.
- Recordar que las IP de otro compañero deben ser distintas.


---

## Apartado b) — Actualización de Debian


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


**Realizado.** Esta sección relata los saltos que se hicieron. La máquina ya está en Debian 13.7: no se deben volver a aplicar los repositorios de Debian 10, 11 o 12.

## Recorrido paso a paso

1. Identificamos versión, arquitectura y espacio libre.
2. Reparamos DNS y los repositorios de Debian 10; actualizamos primero Buster a 10.13.
3. Cambiamos las fuentes a Bullseye, actualizamos índices y paquetes, completamos con `full-upgrade` y reiniciamos.
4. Repetimos el salto de Bullseye a Bookworm y después a Trixie, corrigiendo los problemas explicados abajo.
5. Tras cada etapa comprobamos versión, kernel, paquetes incompletos y unidades fallidas.

La relación «síntoma → diagnóstico → solución → comprobación» se conserva para poder explicar los errores en la defensa.

## Punto de partida y resultados

Versión inicial confirmada: Debian GNU/Linux 10.4 Buster, arquitectura amd64 (x86 de 64 bits). En la comprobación inicial, /dev/sda1 montado en / tenía 13 GB totales, 3,8 GB usados, 7,9 GB disponibles y 33 % de uso; esos valores no representan el espacio actual.

~~~bash
cat /etc/os-release
cat /etc/debian_version
dpkg --print-architecture
df -h /
~~~

Se siguieron saltos consecutivos, comprobando versión y kernel tras los reinicios:

| Etapa verificada | Kernel observado |
| --- | --- |
| Debian 10.13 Buster | 4.19.0-27-amd64 |
| Debian 11.11 Bullseye | 5.10.0-46-amd64 |
| Debian 12.15 Bookworm | 6.1.0-53-amd64 |
| Debian 13.7 Trixie | 6.12.111+deb13-amd64 |

**Resultado final confirmado:** Debian 13.7 arrancado y cero unidades en systemctl --failed. El alumno comunicó que las actualizaciones terminaron. No todas las salidas finales de APT de cada salto quedaron pegadas en la conversación; la evidencia explícita final es la versión, el kernel y el listado de unidades fallidas.

## Qué hace cada comando

~~~bash
su -
apt update
apt upgrade
apt full-upgrade
dpkg --audit
apt-mark showhold
reboot
~~~

- su - entra como root y carga su entorno. La contraseña no se muestra al escribirla. Como root no hace falta sudo.
- apt update descarga índices; no instala actualizaciones.
- apt upgrade actualiza sin eliminar paquetes instalados; puede dejar retenidos los que requieran cambios más amplios.
- apt full-upgrade resuelve transiciones que pueden necesitar sustituciones o eliminaciones. Revisar la propuesta antes de aceptarla.
- dpkg --audit detecta paquetes incompletos o inconsistentes; en las comprobaciones aportadas salió vacío.
- apt-mark showhold muestra bloqueos explícitos; salió vacío cuando se investigaron las retenciones.
- apt -s full-upgrade fue propuesto como simulación opcional; el alumno prefirió actualizar directamente.

Se recomendó una instantánea de la VM antes de los saltos, pero no consta que se creara. Los bloques de repositorios siguientes son históricos: no deben mezclarse ni copiarse todos a la vez en la máquina ya actualizada.

## Buster: errores 404 en los repositorios antiguos

Las entradas iniciales apuntaban a deb.debian.org con buster y buster-updates, y a security.debian.org con buster/updates. Devolvían 404 porque Buster se trasladó al archivo histórico. «Todos los paquetes están actualizados» tras un update fallido no era una comprobación válida: APT conservaba índices anteriores.

Se guardó/proporcionó el procedimiento de copia antes de editar y se sustituyeron las seis entradas activas, conservando comentarios originales:

~~~bash
cp -an /etc/apt/sources.list /etc/apt/sources.list.bak
nano /etc/apt/sources.list
~~~

~~~text
deb http://archive.debian.org/debian/ buster main
deb-src http://archive.debian.org/debian/ buster main

deb http://archive.debian.org/debian-security/ buster/updates main contrib
deb-src http://archive.debian.org/debian-security/ buster/updates main contrib

deb http://archive.debian.org/debian/ buster-updates main contrib
deb-src http://archive.debian.org/debian/ buster-updates main contrib
~~~

Al principio APT seguía mostrando los servidores antiguos: el cambio no se reflejaba aún en el archivo utilizado. Se explicó guardar en nano con Ctrl+O, Enter y salir con Ctrl+X, y comprobar con cat. Posteriormente el alumno confirmó apt update correcto y actualizó hasta 10.13.

## GRUB y preguntas durante la instalación

1. GRUB advirtió que su referencia anterior al disco había cambiado. Se indicó marcar el disco completo /dev/sda con Espacio hasta ver [*], dejando /dev/sda1 sin marcar.
2. Apareció «¿continuar sin instalar GRUB?» porque resaltar la fila no la había seleccionado. Se indicó No, volver, marcar /dev/sda y aceptar. El alumno confirmó la continuación y los arranques posteriores funcionaron.
3. Al actualizar libc6 se autorizó el reinicio automático de los servicios afectados: Yes. No equivale a reiniciar toda la VM.
4. En un salto posterior se preguntó por /etc/default/grub modificado: se indicó conservar la versión local actualmente instalada. Esto conserva la configuración, no impide actualizar GRUB.

## Bullseye: índices disponibles pero paquetes de seguridad ausentes

Se configuraron bullseye, bullseye-security y bullseye-updates. El nombre correcto es bullseye-security, sin /updates. Añadir non-free o cambiar el orden de componentes no resolvía los 404.

El índice ofrecía, entre otros, libudisks2-0 2.9.2-2+deb11u3 y linux-image-amd64 5.10.262-1, pero las descargas desde security.debian.org devolvían 404.

Diagnóstico realizado:

~~~bash
apt -o Acquire::http::No-Cache=true update
dpkg --audit
apt-cache policy libudisks2-0 linux-image-amd64
cd /tmp
apt download libudisks2-0
~~~

Se probó cambiar al servidor oficial deb.debian.org/debian-security. Se propuso HTTPS, aunque varias salidas seguían mostrando HTTP; una comprobación directa externa con HTTPS confirmó que el archivo también faltaba allí. **El protocolo no era una solución confirmada.** Tampoco estaba disponible ese archivo en la ruta probada de archive.debian.org.

Se eliminaron únicamente los índices locales de seguridad de Bullseye para forzar su descarga:

~~~bash
find /var/lib/apt/lists -maxdepth 1 -type f -name '*bullseye-security*' -delete
apt update
apt-cache policy libudisks2-0
~~~

El índice nuevo seguía anunciando la versión ausente. Quedó comprobada la discrepancia índice/archivo; no se determinó el motivo administrativo de su retirada.

**Solución utilizada para continuar:** copia oficial de Debian Snapshot del 31 de agosto de 2026. Se verificó respuesta HTTP 200 tanto para Release como para el paquete de prueba. Se sustituyeron las dos entradas de seguridad, manteniendo las cuatro normales de Bullseye:

~~~text
deb http://deb.debian.org/debian/ bullseye main contrib
deb-src http://deb.debian.org/debian/ bullseye main contrib

deb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20260831T000000Z/ bullseye-security main contrib
deb-src [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20260831T000000Z/ bullseye-security main contrib

deb http://deb.debian.org/debian/ bullseye-updates main contrib
deb-src http://deb.debian.org/debian/ bullseye-updates main contrib
~~~

check-valid-until=no permite un índice histórico caducado, solo en esas entradas; se mantienen las comprobaciones de firmas. Fue un paso temporal, sustituido al pasar a Bookworm. No se debe conservar esta instantánea como fuente de actualizaciones actuales.

Después de update y la prueba de descarga se continuó instalando. Un upgrade dejó 284 paquetes retenidos; se indicó full-upgrade para completar las transiciones. Escribir s en el prompt root@debian no responde a APT: solo se contesta cuando APT pregunta. Se confirmó finalmente Debian 11.11 con kernel 5.10.0-46-amd64.

## Bookworm: faltaba main y no se completaba el salto

Se sustituyeron todas las entradas de Bullseye, incluidas Snapshot, por Bookworm. Durante la edición quedaron las primeras líneas como bookworm contrib, **sin main**.

Síntomas: full-upgrade dejaba 34 paquetes retenidos; /etc/debian_version seguía mostrando 11.11. systemd seguía instalado en 247.3-7+deb11u8, y sus candidatos solo aparecían desde bookworm-security. dpkg --audit y apt-mark showhold estaban vacíos.

~~~bash
cat /etc/apt/sources.list
grep -R -n -E '^(deb|Types:|URIs:|Suites:|Components:|Enabled:)' /etc/apt/sources.list.d/
apt update
apt-cache policy systemd libnss-systemd libpam-systemd systemd-timesyncd
~~~

El directorio adicional no mostró entradas. **Solución:** recuperar main en las dos primeras líneas; después apt update y apt full-upgrade. Configuración corregida:

~~~text
deb http://deb.debian.org/debian/ bookworm main contrib
deb-src http://deb.debian.org/debian/ bookworm main contrib

deb http://security.debian.org/debian-security bookworm-security main contrib
deb-src http://security.debian.org/debian-security bookworm-security main contrib

deb http://deb.debian.org/debian/ bookworm-updates main contrib
deb-src http://deb.debian.org/debian/ bookworm-updates main contrib
~~~

APT también listó muchos paquetes como prescindibles, incluidos sudo y openssh-server. Se indicó **no ejecutar autoremove** y se propuso proteger estos paquetes:

~~~bash
apt-mark manual sudo openssh-server openssh-sftp-server
~~~

No se aportó salida de este último comando; no dar su ejecución por verificada. Más adelante ssh.service sí apareció ejecutándose. Sigue pendiente revisar si alguna aplicación deseada fue retirada durante los intentos previos. Tras corregir main, se confirmó arranque en 12.15 con kernel 6.1.0-53-amd64.

## Trixie y estado final

Se indicó guardar sources.list.bookworm.bak y reemplazar las seis entradas activas por:

~~~text
deb https://deb.debian.org/debian/ trixie main contrib
deb-src https://deb.debian.org/debian/ trixie main contrib

deb https://security.debian.org/debian-security/ trixie-security main contrib
deb-src https://security.debian.org/debian-security/ trixie-security main contrib

deb https://deb.debian.org/debian/ trixie-updates main contrib
deb-src https://deb.debian.org/debian/ trixie-updates main contrib
~~~

Es la configuración indicada para el último salto; no se pegó un cat final del archivo. Se comunicó que todo estaba actualizado y se verificó:

~~~text
cat /etc/debian_version → 13.7
uname -r → 6.12.111+deb13-amd64
systemctl --failed → 0 loaded units listed.
~~~

## Para la defensa

- `update` renueva índices; `upgrade` instala actualizaciones; `full-upgrade` puede resolver transiciones eliminando o sustituyendo paquetes.
- Un error DNS impide encontrar el servidor. Un HTTP 404 indica que ya se ha contactado con él pero no existe el recurso solicitado.
- Un índice descargado correctamente no demuestra que todos los paquetes anunciados estén disponibles.
- Se usaron saltos consecutivos y comprobaciones después de reiniciar; no se cambió directamente de Buster a Trixie.
- Las versiones y kernels de la tabla son los observados en esta VM, no una afirmación sobre lo que esté disponible hoy para otra instalación.

Fuentes: [archivo de Buster](https://lists.debian.org/debian-devel-announce/2025/06/msg00001.html), [Debian Snapshot](https://snapshot.debian.org/), [notas de Bookworm](https://www.debian.org/releases/bookworm/amd64/release-notes/ch-upgrading.en.html), [notas de Trixie](https://www.debian.org/releases/trixie/release-notes/upgrading.html).


---

## Apartado c) — Arranque, targets y unidades


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


## Paso 1. Explicar la secuencia completa

1. BIOS/UEFI inicia el hardware virtual y selecciona el dispositivo de arranque.
2. GRUB carga kernel e initramfs.
3. El kernel inicializa el sistema; el entorno temporal del initramfs permite localizar y montar la raíz.
4. Se pasa al sistema instalado y systemd organiza los procesos de espacio de usuario como PID 1.
5. Se activan dispositivos, montajes y servicios según sus dependencias, muchos en paralelo.
6. Se alcanza el target elegido y queda disponible el acceso configurado: consola, SSH o entorno gráfico.

No se hizo una comprobación específica del modo BIOS/UEFI de esta VM.

## Paso 2. Consultar y cambiar el target predeterminado

```bash
systemctl get-default
systemctl list-units --type=target --all --no-pager
systemctl list-unit-files --type=target --no-pager
```

Inicialmente era `graphical.target`. Al retirar el escritorio se aplicó:

```bash
systemctl set-default multi-user.target
```

Eso cambia el objetivo de futuros arranques, no equivale a apagar en ese instante el escritorio. La opción contraria sería `set-default graphical.target`, pero no se aplica en el estado final.

En el primer inventario aparecieron 52 unidades target y 78 archivos de unidad. Son vistas diferentes: unidades conocidas por systemd frente a archivos, alias y plantillas disponibles. No son 78 procesos. `graphical.target` puede estar activo junto con `multi-user.target`, y alcanzarlo no prueba que haya un escritorio usable.

## Paso 3. Consultar los servicios

```bash
systemctl list-units --type=service --all --no-pager
systemctl list-units --type=service --state=running --no-pager
systemctl list-unit-files --type=service --no-pager
systemctl --failed --no-pager
```

| Estado | Qué significa |
| --- | --- |
| `active (running)` | Servicio activo con proceso ejecutándose |
| `active (exited)` | La activación terminó y la unidad permanece activa |
| `inactive (dead)` | No se está ejecutando; puede ser normal |
| `failed` | Falló la ejecución de la unidad |
| `enabled` | Tiene habilitación para arrancar mediante las dependencias de instalación |
| `disabled` | No está habilitado así; podría activarse por otros medios |
| `static` | No dispone de la habilitación normal mediante `[Install]` |
| `masked` | Está bloqueada su activación |
| `alias` / `generated` | Otro nombre / unidad creada por un generador |

`PRESET` es la política predeterminada, no el estado actual. `enable` y `start` no son lo mismo. `networking.service` puede terminar tras configurar interfaces sin mantener un proceso residente. Los nombres distinguen mayúsculas: `NetworkManager.service` es diferente de `network-manager.service`.

Ejemplo final para la defensa: `lsi-companion.service` está habilitado y mantiene un proceso Python; `logrotate.service` termina tras hacer su trabajo y lo activa su temporizador.

## Paso 4. Identificar otras unidades

| Tipo | Función |
| --- | --- |
| `.socket` | Comunicación; puede activar servicios |
| `.timer` | Activación programada |
| `.path` | Activación al observar rutas |
| `.mount` / `.automount` | Montajes normales y bajo demanda |
| `.device` | Dispositivos |
| `.swap` | Espacio de intercambio |
| `.slice` / `.scope` | Agrupación y control de recursos/procesos |

## Incidencia observada: ssa.service

`systemctl is-enabled ssa.service` devolvió «Too many levels of symbolic links». Sin embargo, `readlink -f` resolvía los enlaces al archivo existente, `systemd-analyze verify` no mostró errores y el programa terminó con `status=0/SUCCESS`.

`dpkg -S` no encontró paquete propietario. La unidad incluía un alias con su mismo nombre, algo sospechoso pero no demostrado como causa. **No se borró ni modificó**, porque podía ser una personalización del laboratorio. No se debe defender como un bucle de enlaces demostrado o una incidencia resuelta.

## Para la defensa

Explicar la diferencia entre secuencia de arranque, target, servicio y proceso. Mostrar un servicio residente, una tarea que termina y el target actual. Consultar `systemctl cat` para entender una unidad antes de cambiarla.


---

## Apartado d) — Medición de tiempos de arranque


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


## Paso 1. Obtener las medidas

```bash
systemd-analyze time
systemd-analyze blame --no-pager
systemd-analyze critical-chain multi-user.target
```

Al principio se consultó `critical-chain graphical.target`; después se usó `multi-user.target`, de acuerdo con el estado sin escritorio.

| Medición compartida | Kernel/fase inicial | Userspace | Total mostrado |
| --- | ---: | ---: | ---: |
| Primera medición | 6,564 s | 39,707 s | 46,272 s |
| Una medida posterior a la limpieza | 6,389 s | 10,031 s | 16,421 s |
| Último informe revisado, 10 de octubre | 6,891 s | 10,465 s | 17,356 s |

Son observaciones de diferentes arranques, no una comparación controlada que aísle cada cambio. Las pequeñas diferencias al sumar son de redondeo. No se mostraron tiempos separados de firmware ni GRUB: el total no equivale necesariamente a pulsar el botón y cronometrar hasta el login.

## Paso 2. Interpretar blame

`blame` ordena duraciones de activación. No mide cuánto tiempo se mantiene ejecutándose un servicio ni su consumo total de CPU. No se suman todas las filas: existen tareas en paralelo.

En la primera medida destacaban AppArmor (25,674 s), fwupd (4,715 s), ifupdown-pre (4,560 s) y el dispositivo raíz (4,435 s). En arranques posteriores sus duraciones variaron. No se puede prometer ahorrar 25 segundos simplemente desactivando AppArmor.

## Paso 3. Interpretar la cadena crítica actual

Última cadena compartida:

```text
multi-user.target @10.399s
└─ssh.service @9.861s +537ms
  └─network.target @9.805s
    └─networking.service @6.378s +3.417s
      └─local-fs.target @6.365s
        └─tmp.mount @6.327s +36ms
          └─swap.target @6.309s
            └─dev-sda5.swap @6.195s +106ms
              └─dev-sda5.device @6.186s
```

- `@`: instante respecto al inicio del espacio de usuario.
- `+`: duración de la activación indicada.
- `networking` empezó a 6,378 s y tardó unos 3,417 s.
- La swap tardó 106 ms en activarse; el instante del dispositivo no equivale al tiempo que consumió un proceso de swap.
- La cadena muestra relaciones temporales de dependencias; no es una prueba de que quitar una fila reduzca exactamente ese tiempo.

## Paso 4. Separar medición y optimización

Las decisiones que quedaron aplicadas están en [h)](h-limpieza.md). Se redujo notablemente el tiempo respecto a la primera medida, pero la meta personal de 10–12 s **no se alcanzó**. Se acordó continuar con la práctica y dejar la optimización para el final.

## Para la defensa

«Mido kernel y userspace con `time`, localizo activaciones lentas con `blame` y estudio dependencias con `critical-chain`. Comparo varios arranques y verifico que SSH, red y swap siguen funcionando; no confundo espacio liberado con segundos ahorrados.»


---

## Apartado e) — Errores del journal y logrotate


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


## Paso 1. Consultar errores del arranque

```bash
journalctl -p 3 -b --no-pager
```

Ejecutar como root para disponer de los registros del sistema. Con el usuario normal apareció un aviso de permisos y «No entries»; eso no demostraba ausencia de errores.

Se observaron mensajes de SMBus virtual, etiquetas ausentes en reglas ALSA y un fallo de `logrotate.service` relacionado con CUPS. No se asumió que todos fueran fallos graves ni que hubiera que instalar servicios eliminados.

## Paso 2. Investigar el fallo de logrotate

```bash
journalctl -u logrotate.service -b --no-pager -n 80
systemctl status logrotate.service --no-pager -l
cat /etc/logrotate.d/cups*
dpkg -l 'cups*'
ls -l /var/lib/logrotate/status
```

La configuración de rotación conservaba un bloque `postrotate` que intentaba reiniciar CUPS. El servicio no estaba instalado; varios paquetes figuraban como `rc`: binarios retirados, configuración residual presente. El registro indicaba un error al ejecutar ese bloque sobre `/var/log/cups/*log`.

**Causa identificada:** configuración residual que llamaba a un servicio eliminado. No era necesario reinstalar el sistema de impresión para resolverla.

## Paso 3. Apartar la configuración residual

Se retiró de `/etc/logrotate.d/` la configuración de CUPS y se conservó en `/root/respaldo-logrotate/`. La conversación no conserva el nombre concreto final del archivo: antes de repetir esta operación en otra VM se debe identificarlo con el listado anterior.

No se vació `/var/log` ni se eliminaron todos los archivos de configuración de logrotate.

## Paso 4. Validar la corrección

```bash
logrotate --debug /etc/logrotate.conf
systemctl start logrotate.service
systemctl status logrotate.service --no-pager -l
```

El modo `--debug` ayuda a revisar sin realizar la rotación. La ejecución real posterior terminó con `status=0/SUCCESS`. `inactive (dead)` al finalizar era normal: esta tarea no permanece ejecutándose continuamente.

Hubo además un aviso antiguo sobre permisos del archivo de estado. La consulta posterior mostró `root:root` y modo `640`; no se atribuye esa situación a un comando no registrado.

## Paso 5. Contrastar la explicación de la IA

| Propuesta/interpretación | Contraste y decisión |
| --- | --- |
| Reinstalar CUPS por aparecer un error | Se comprobó que el fallo procedía de una configuración residual; se retiró esa configuración |
| `inactive` significa fallo | El proceso había terminado con éxito; no había que «arreglarlo» por estar parado |
| Todo error del kernel requiere intervención | Se consideró el contexto virtual; no se modificó hardware por el aviso SMBus |
| Error de enlaces de ssa implica bucle demostrado | `readlink` resolvía las rutas y la unidad ejecutaba correctamente; causa no confirmada |
| «No entries» demuestra journal limpio | Primero se revisaron los permisos del usuario que ejecutaba la consulta |

Los avisos ALSA y SMBus no tienen una corrección específica demostrada en esta guía. Las sugerencias de la IA se trataron como hipótesis que había que comprobar.

## Para la defensa

Presentar la secuencia: mensaje original → unidad implicada → archivo residual → comprobación de paquetes → corrección limitada → nueva ejecución correcta. Distinguir los errores históricos del estado actual.


---

## Apartado f) — Segunda interfaz y dirección temporal


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


## Paso 1. Identificar los parámetros de ens34

```bash
ip -details addr show dev ens34
ip route
cat /etc/network/interfaces
```

Se observó `ens34` con IP `IP_VM_ENS34/23`, broadcast `BROADCAST_ENS34`, MTU 1500 y flags `UP,LOWER_UP`. La configuración persistente figura en el apartado a). El alias alternativo `enp2s2` no es una segunda tarjeta física.

## Paso 2. Añadir una dirección temporal

Operación realizada como root:

```bash
ip addr add 192.0.2.56/32 dev ens34 label ens34:0
ip -4 addr show dev ens34
```

La salida mostró simultáneamente `IP_VM_ENS34/23` y `192.0.2.56/32`. `ens34:0` es una etiqueta de la dirección adicional: no se creó una tarjeta de red nueva. `/32` identifica una sola dirección y no una red local completa.

## Paso 3. Comprobar la dirección local

```bash
ping -c 3 192.0.2.56
```

Resultado: tres respuestas y 0 % de pérdida. Eso demuestra que la máquina reconoce la dirección como propia, **no** que otro equipo pueda alcanzarla. Para que lleguen paquetes desde otra máquina necesita existir un camino de red y rutas adecuados. `192.0.2.0/24` es un bloque de documentación usado aquí como ejemplo.

## Paso 4. Dejarla como estaba

```bash
ip addr del 192.0.2.56/32 dev ens34
ip -4 addr show dev ens34
```

La consulta final mostró solo `IP_VM_ENS34/23`. No se añadió la dirección de prueba a `/etc/network/interfaces`.

## Alcance y defensa

Se identificaron los parámetros y se demostró el alta, prueba y retirada de la dirección lógica adicional. El enunciado también pide cambiar los principales parámetros de la segunda interfaz: no consta una prueba separada de cambio de MTU/MAC u otros parámetros. No dar por realizadas operaciones que no aparecen en las salidas.

«Una interfaz puede tener varias IP. Añadir una dirección hace que el kernel la trate como local, pero no publica por sí solo una ruta hacia ella en el resto de la red.»


---

## Apartado g) — Tabla de rutas y ruta temporal


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


## Paso 1. Leer la tabla

```bash
ip route
```

Rutas habituales observadas:

```text
default via GATEWAY_ENS33 dev ens33 onlink
RED_ENS33/23 dev ens33 proto kernel scope link src IP_VM_ENS33
RED_ENS34/23 dev ens34 proto kernel scope link src IP_VM_ENS34
```

Las dos redes `/23` están conectadas directamente. `default` se utiliza cuando no existe una ruta más específica. `src` indica la dirección de origen preferida. La ruta `169.254.0.0/16` que aparecía inicialmente dejó de figurar tras retirar el script de avahi-autoipd.

## Paso 2. Añadir una ruta de ejemplo

```bash
ip route add 198.51.100.0/24 via GATEWAY_ENS33 dev ens33
ip route
```

El sistema incorporó la ruta hacia ese bloque de documentación a través del gateway ya alcanzable por `ens33`.

## Paso 3. Comprobar qué ruta elegiría el kernel

```bash
ip route get 198.51.100.10
```

Salida obtenida:

```text
198.51.100.10 via GATEWAY_ENS33 dev ens33 src IP_VM_ENS33 uid 0
    cache
```

Es una consulta de selección de ruta, no un envío de paquetes ni una prueba de que exista ese destino. La ruta `/24` es más específica que la ruta por defecto; en este ejemplo ambas usan el mismo gateway, por lo que no se demuestra un cambio de camino físico.

## Paso 4. Entender la persistencia

La ruta se añadió con `ip route`, sin una configuración persistente documentada. No aparece en las tablas posteriores compartidas tras reiniciar. No se afirma que se ejecutara un borrado manual concreto.

Si se repite la demostración, la operación inversa es:

```bash
ip route del 198.51.100.0/24 via GATEWAY_ENS33 dev ens33
```

## Para la defensa

Explicar destino/prefijo, siguiente salto, interfaz y dirección de origen. Una ruta estática es una decisión configurada administrativamente; «estática» no significa que persista automáticamente tras reiniciar.


---

## Apartado h) — Limpieza y optimización


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


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


---

## Apartado i) — Compañero de Telegram


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


## Objetivo y resultado

La funcionalidad definitiva envía una curiosidad por Telegram al arrancar la VM y responde a consultas sencillas sobre sus recursos. El alumno confirmó que funciona; también compartió el servicio habilitado y sus registros del arranque.

**SSH sigue en el puerto 22 sin depender del bot.** Este proyecto no es un mecanismo de autorización de acceso ni ejecuta órdenes recibidas por Telegram. No se incluyen las pruebas del proyecto descartado como pasos a repetir.

## Paso 1. Definir la idea con ayuda de IA

Se usó el asistente para explorar alternativas, desarrollar el script Python y la unidad de systemd, y probar la lógica. El objetivo final fue mantener una interacción sencilla con la VM, sin depender de una interfaz gráfica.

La IA se utilizó **durante el desarrollo**. En ejecución el programa consulta APIs y reconoce palabras clave; no llama a un LLM para inventar datos ni para interpretar libremente todas las preguntas.

## Paso 2. Crear el bot y vincular la cuenta

Se creó un bot con BotFather y se obtuvo un token. El token se renovó antes del despliegue definitivo y se introdujo mediante lectura oculta; nunca debe copiarse al repositorio ni a capturas públicas.

Se vinculó la cuenta personal mediante un código aleatorio, un mensaje privado al bot y confirmación local. Se conservaron los identificadores numéricos de usuario, chat y bot en un archivo restringido. Son identificadores usados para autorizar respuestas, no datos que deban fijarse en el código público.

Estado final:

| Archivo en Debian | Función |
| --- | --- |
| `/etc/lsi-companion/telegram-token` | Token privado; root, permisos 600 |
| `/etc/lsi-companion/administrador.json` | Identificadores de la cuenta vinculada; root, permisos 600 |
| `/usr/local/libexec/lsi-companion.py` | Programa instalado |
| `/etc/systemd/system/lsi-companion.service` | Servicio que lo ejecuta |
| `/var/lib/lsi-companion/estado.json` | Último arranque notificado, último dato e índice de mensajes procesados |

Los secretos ya existen en esta VM. Los pasos posteriores no son un instalador completo para una máquina nueva sin vinculación. El estado y las credenciales se excluyen de Git.

## Paso 3. Instalar el programa y su unidad

El instalador creó el usuario de sistema `lsi-companion`, sin inicio de sesión interactivo, e instaló el programa y la unidad. El repositorio publica la versión final, no los instaladores de migración ya retirados.

Equivalencia de la copia de archivos finales, desde una copia del repositorio y como root:

```bash
install -o root -g root -m 644 companion/bot.py /usr/local/libexec/lsi-companion.py
install -o root -g root -m 644 companion/lsi-companion.service /etc/systemd/system/lsi-companion.service
systemd-analyze verify /etc/systemd/system/lsi-companion.service
systemctl daemon-reload
systemctl enable --now lsi-companion.service
```

Este bloque sirve para entender/reponer la instalación **si el usuario y las credenciales ya están creados**, no es necesario ejecutarlo de nuevo para demostrar el servicio. Si se reemplaza el código con el servicio ya activo, el cambio requiere reiniciarlo.

Código: [bot.py](../companion/bot.py). Unidad completa: [lsi-companion.service](../companion/lsi-companion.service).

## Paso 4. Entender cómo arranca y permanece funcionando

| Directiva | Explicación en nuestra unidad |
| --- | --- |
| `After=network.target` | Ordena el inicio después de ese target; no garantiza Internet ni obliga por sí sola a activarlo |
| `Type=simple` | systemd supervisa el proceso Python; que esté activo no prueba que Telegram ya esté listo |
| `ExecStart=/usr/bin/python3 -I ...` | Ejecuta el programa usando Python en modo aislado |
| `User` / `Group` | El bot no se ejecuta como root |
| `LoadCredential` | systemd entrega al servicio copias accesibles de las credenciales sin poner el token en la orden de ejecución |
| `StateDirectory` | Proporciona almacenamiento persistente para el estado del bot |
| `Restart=on-failure` y `RestartSec=15` | Intenta recuperar el proceso si falla; no transforma una configuración incorrecta en correcta |
| `WantedBy=multi-user.target` | `enable` conecta su arranque al target de uso normal |
| `NoNewPrivileges`, `ProtectSystem`, etc. | Restringen permisos y escritura del proceso |

Se dejó que empezara temprano, después del orden de red existente. No se añadió una espera fija a Internet: el programa reintenta si Telegram no está disponible. Un fallo del bot no cambia la configuración de SSH ni impide usarlo.

## Paso 5. Obtener una curiosidad externa

Flujo implementado:

1. Leer el identificador del arranque en `/proc/sys/kernel/random/boot_id`.
2. Compararlo con el último guardado; si ya se notificó ese arranque, no repetir el saludo por un mero reinicio del servicio.
3. Consultar `https://uselessfacts.jsph.pl/api/v2/facts/random?language=en`.
4. Validar la respuesta e intentar evitar la repetición inmediata del último dato.
5. Solicitar traducción inglés → español a MyMemory y enviar el texto con enlace a la fuente.
6. Guardar el identificador del arranque tras enviar el mensaje.

No existe una lista fija de 20 curiosidades en la versión final. Si no se puede traducir, se muestra el original en inglés y se indica el motivo general. Si no se obtiene un dato, se envía un aviso y continúan disponibles las consultas de recursos. La traducción recibe únicamente el texto público del dato, no el estado de la VM ni el token de Telegram.

La fuente externa y la traducción pueden contener errores; se adjunta el enlace para poder contrastar. El programa limita tiempos de espera y tamaño de respuestas. Si se pierde la confirmación de una petición enviada, o el proceso falla antes de guardar el estado, todavía puede haber una duplicación: no se ha implementado una garantía distribuida de «exactamente una vez».

Fuentes: [API de Useless Facts](https://uselessfacts.jsph.pl/), [MyMemory](https://mymemory.translated.net/doc/spec.php), [Telegram Bot API](https://core.telegram.org/bots/api).

## Paso 6. Consultar la máquina desde el móvil

| Mensaje | Respuesta |
| --- | --- |
| `/estado` o «¿cómo estás?» | Nombre, tiempo encendida, kernel, CPU, memoria y disco |
| `/uso`, «memoria» o «CPU» | Muestra breve de CPU, RAM y swap |
| `/disco` o «¿cuánto espacio queda?» | Capacidad, uso y espacio disponible de `/` |
| `/curiosidad` | Nueva consulta a la fuente externa |
| `/ayuda` | Opciones disponibles |

La interfaz usa botones y palabras clave. El bot solo responde a mensajes privados cuyo usuario y chat coinciden con la vinculación. No usa `eval`, no transforma mensajes en órdenes de shell y no permite apagar la máquina por escribir una orden.

Se usa **long polling**: el bot consulta Telegram y espera mensajes mediante conexiones salientes HTTPS. No necesita un puerto entrante nuevo ni un servidor web público.

## Paso 7. Explicar de dónde salen las medidas

| Medida | Fuente y alcance |
| --- | --- |
| Tiempo encendida | `/proc/uptime` |
| Identificador de arranque | `/proc/sys/kernel/random/boot_id` |
| RAM | `/proc/meminfo`; estima uso como total menos disponible |
| Swap | Total menos libre en `/proc/meminfo` |
| CPU | Diferencia entre dos lecturas de `/proc/stat` separadas por un segundo |
| Disco | `shutil.disk_usage('/')`; no inventario de todos los discos |

Se distingue CPU ocupada, espera de E/S y tiempo cedido al hipervisor. Memoria disponible no es igual a memoria totalmente vacía: Linux utiliza caché. El resumen no comprueba la salud de todos los servicios y no debe presentarse como una auditoría completa.

## Paso 8. Comprobar el servicio y su arranque automático

```bash
systemctl is-enabled lsi-companion.service
systemctl status lsi-companion.service --no-pager -l
systemd-analyze critical-chain lsi-companion.service
journalctl -b -u lsi-companion.service --no-pager -n 20
```

Salida aportada:

```text
enabled
lsi-companion.service @9.826s
└─network.target @9.805s
  └─networking.service @6.378s +3.417s
```

El registro muestra el inicio del servicio a las 00:43:04 y «Compañero listo» a las 00:43:07. `@9.826s` es el instante en userspace, no la duración del programa. El alumno confirmó que el bot funciona tras la instalación y la limpieza. Estos datos acreditan la activación en el arranque actual; no se adjunta una captura independiente de cada mensaje de Telegram.

Para la demostración: mostrar el estado, escribir `/estado`, `/disco` y `/curiosidad` desde la cuenta vinculada, y relacionar una respuesta con una consulta local. No hace falta reiniciar durante la defensa salvo que se solicite y se disponga de acceso de recuperación.

## Paso 9. Pruebas y fallos contemplados

Se ejecutaron **12 pruebas locales** del código con APIs simuladas: autorización por usuario/chat privado, reconocimiento de preguntas, cálculos de recursos, repetición de datos, fuente no disponible, respuesta malformada, cuota de traducción y control de notificación por arranque.

```bash
python3 -m unittest discover -s companion -p test_bot.py -v
```

Esas pruebas no sustituyen la conexión real: el alumno la comprobó desde la VM y confirmó funcionamiento. Si el bot deja de responder, revisar su journal y la resolución/conectividad antes de reinstalarlo. Los fallos al iniciar son gestionados por systemd; durante la ejecución se reintentan los errores de Telegram.

## Paso 10. Comparar con cron

| Aspecto | Servicio de systemd | Cron |
| --- | --- | --- |
| Al arrancar | Habilitación y dependencias de unidades | `@reboot` podría lanzar un programa |
| Recuperación | Supervisa el proceso y puede reiniciarlo | Por sí solo no supervisa un proceso persistente |
| Logs y estado | Journal y `systemctl` | Hay que preparar la salida y su gestión |
| Consultas interactivas | El proceso permanece esperando mensajes | Un trabajo periódico añade demora o exige lanzar otro proceso permanente |
| Uso ocasional | Mantiene memoria para Python; el polling espera entre eventos | Un script breve periódico puede ser preferible si solo envía un informe cada cierto tiempo |

Para un único aviso de arranque, cron podría ser suficiente con manejo explícito de red, credenciales y errores. Para **este bot que recibe preguntas**, se eligió systemd. No se instaló además una tarea cron que duplique el proceso. No se ha medido un ahorro exacto de recursos de una alternativa frente a la otra.

## Para la defensa

«Diseñé con ayuda de IA un servicio residente de solo lectura. Arranca después del orden de red, consulta una fuente externa, notifica el arranque y responde a mi cuenta de Telegram. Se ejecuta sin root y con credenciales separadas del código. Systemd me permite supervisarlo y consultar sus registros. La IA ayudó a construirlo, pero no genera las curiosidades durante su ejecución.»


---

## Apartado j) — Puertos y conexiones


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


**Actualizado el 10/10/2026:** la bitácora aportada contiene las salidas reales de `ss -tulnp` y `ss -tnp state established` que antes faltaban. Se obtuvieron durante k) y l); se integran aquí como evidencia del inventario. La bitácora no había marcado j) como cerrado, aunque sí había recogido estas comprobaciones.

## Paso 1. Ver puertos y procesos

Como root:

```bash
ss -tulnp
```

`-t` TCP; `-u` UDP; `-l` sockets en escucha o vinculados para recibir tráfico; `-n` direcciones/puertos numéricos; `-p` procesos, con los permisos necesarios. UDP no tiene una fase de escucha/conexión idéntica a TCP.

## Paso 2. Ver conexiones TCP establecidas

```bash
ss -tnp state established
```

Identificar dirección y puerto local, dirección y puerto remoto, estado y proceso. Distinguir un puerto del servidor, como el 22, del puerto temporal del cliente. Puede aparecer el proceso Python del bot comunicándose con Telegram por HTTPS; no atribuir cualquier IP remota a Telegram sin comprobarla.

## Paso 3. Explicar el alcance

Escuchar no prueba que el servicio sea accesible desde cualquier red: influyen la dirección de enlace, el routing y el filtrado. Una conexión establecida es una instantánea y puede desaparecer entre consultas.

## Resultados observados

| Dirección local | Proceso | Interpretación |
| --- | --- | --- |
| `0.0.0.0:22` y `[::]:22` | sshd, PID 631 | SSH en todas las interfaces IPv4 e IPv6 |
| `127.0.0.1:6010` y `[::1]:6010` | sshd-session, PID 1218 | Sockets en loopback, compatibles con reenvío X11 |

La salida no mostró sockets UDP. Es una observación del momento, no una garantía permanente.

Había dos conexiones establecidas hacia `IP_VM_ENS33:22` desde `IP_CLIENTE_VPN`, con puertos cliente `63418` y `63441`. Python, PID 582, mantenía otra conexión hacia `149.154.166.110:443`. Es compatible con el bot, pero el listado no verificó su comando ni la identidad del destino: el puerto 443 por sí solo no demuestra Telegram o HTTPS.

## Paso 4. Distinguir conexiones, sesiones y procesos

Se ejecutaron:

```bash
who
w
ps -o pid,ppid,tty,stat,args -p 1167,1172,1218,1219
```

`who`/`w` mostraron dos sesiones para `lsi` desde la misma IP. «2 users» no significa dos personas. En una consulta posterior, `ps` solo mostró el proceso `1167` (`lsi [priv]`) y su hijo `1218` (`lsi@pts/0`): estos dos procesos pertenecen a una misma sesión.

Repetir `ss -tnp state established` confirmó que solo quedaba la conexión con puerto cliente `63418`. Los PID y puertos efímeros son históricos, no valores fijos que se deban reutilizar. `Recv-Q`/`Send-Q` muestran colas, no el tráfico acumulado.

Estas consultas no modificaron configuración. La actualización cada dos segundos se explica en [k)](k-monitorizacion.md). Para la defensa, mostrar una nueva muestra y explicar `LISTEN`, `ESTAB`, loopback, puerto servidor y puerto cliente.


---

## Apartado k) — Monitorización


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


[Volver al índice](../README.md) · [Inventario de conexiones](j-conexiones.md)

**Estado:** realizado con salidas y captura descritas en `bitacora_lsi_p1.md`, aportada por el alumno el 10/10/2026. No se instalaron paquetes ni se modificó configuración para este apartado.

## Paso 1. Monitorizar CPU, memoria y procesos

```bash
top
```

Durante la ejecución: `P` ordena por CPU, `M` por memoria, `1` alterna el desglose por CPU lógica y `q` sale.

La muestra de las 15:28:39 mostró:

```text
up 14:45, 2 users, load average: 0,08, 0,02, 0,01
187 tareas: 1 ejecutándose, 186 durmiendo, 0 detenidas, 0 zombie
CPU: 0,0 us, 1,0 sy, 99,0 id, 0,0 wa, 0,0 st
RAM: 1469,9 MiB total; 1186,0 MiB disponible
Swap: 1534,0 MiB total; 0,0 usada
```

La VM llevaba 14 horas y 45 minutos encendida. Las cargas medias corresponden a 1, 5 y 15 minutos; no son porcentajes de CPU. La muestra reflejó poca carga y no mostró presión de swap. No sirve para asegurar que siempre esté así.

### Cómo explicar las columnas

| Campo | Significado |
| --- | --- |
| PID / USUARIO | Identificador y propietario del proceso |
| PR / NI | Prioridad de planificación y ajuste nice |
| VIRT / RES / SHR | Memoria virtual, residente y compartible |
| S | Estado: R ejecutándose, S durmiendo, I hilo del núcleo inactivo |
| %CPU / %MEM | Consumo de CPU y memoria informado por el monitor |
| HORA+ | Tiempo de CPU acumulado; no tiempo total desde que arrancó |
| us / sy / id / wa / st | Usuario, núcleo, inactividad, espera de E/S y tiempo sustraído por el hipervisor |

Se observaron `kworker`, el propio `top` y `systemd` con PID 1. `14:43.16` en HORA+ significa aproximadamente 14 minutos y 43 segundos de CPU acumulada, no 14 horas. El `+` al final de un nombre truncado no es parte necesariamente de su nombre completo.

## Paso 2. Contrastar la memoria

```bash
free -h
```

```text
               total       usado       libre  compartido   búf/caché  disponible
Mem:           1,4Gi       283Mi       1,1Gi       1,1Mi       215Mi       1,2Gi
Inter:         1,5Gi          0B       1,5Gi
```

La memoria disponible estima lo utilizable por nuevas cargas sin recurrir al intercambio. No confundir memoria completamente libre con disponible ni sumar columnas sin considerar su definición y redondeo. La swap estaba activa y sin uso.

## Paso 3. Monitorizar conexiones cada dos segundos

```bash
watch -n 2 'ss -tunap'
```

La captura de las 15:59:31 mostró el refresco cada dos segundos, SSH en escucha en el puerto 22, dos conexiones SSH establecidas, sockets locales en el 6010 y una conexión saliente de Python al puerto 443. El detalle y los límites de interpretación están en [j)](j-conexiones.md).

`-a` incluye sockets activos y en escucha; `Ctrl+C` termina `watch`. Esta consulta periódica permite observar entradas que aparecen y desaparecen; no mide por sí sola el caudal de bytes por segundo.

## Ampliaciones propuestas, sin nueva ejecución acreditada en esta sesión

```bash
top -b -n 1 | head -n 25
vmstat 1 5
```

El primer comando recoge una instantánea para guardar evidencia. El segundo toma cinco muestras; la primera suele resumir estadísticas desde el arranque. La prueba interactiva ejecutada fue `top` y la de conexiones fue `watch` con `ss`.

## Para la defensa

Mostrar un refresco de `top` y otro de `watch`. Identificar un proceso, su usuario, memoria residente y consumo de CPU; distinguir proceso de conexión. Explicar que `free -h` es una instantánea, mientras que `top` y `watch` actualizan la información periódicamente.


---

## Apartado l) — TCP Wrappers


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


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
hosts.allow: sshd: IP_CLIENTE_VPN
hosts.deny:  sshd: ALL
```

Estas dos líneas resumen **dos archivos distintos**, no son un bloque para copiar literalmente. Desde ese directorio:

```bash
tcpdchk -d -v
tcpdmatch -d sshd IP_CLIENTE_VPN
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

Se ensayó permitir `IP_CLIENTE_VPN` y denegar el resto para `sshd`, con un respaldo y temporizadores transitorios de recuperación. `tcpdchk -v` enumeró ambas reglas y `tcpdmatch` permitió la IP VPN y denegó `192.0.2.10`.

El alumno confirmó que abrió una **nueva** sesión desde CMD de Windows y restauró los archivos. Las consultas posteriores no mostraron reglas activas ni temporizadores de recuperación tras detener el timer v2. Esto validó el ensayo y su retirada; no demuestra una conexión real desde la IP documental de prueba.

Los temporizadores de ese ensayo ya no estaban pendientes en la última comprobación. No se deben considerar una recuperación activa de la política final.

## Paso 7. Política permanente comunicada

Después del ensayo, el alumno decidió mantener el filtrado y comunicó la VM del compañero `IP_COMPANERO_LAN`. Recibió las reglas y confirmó «listo».

Contenido activo comunicado de **`/etc/hosts.allow`**, conservando sus comentarios originales:

```text
sshd: IP_CLIENTE_VPN, IP_COMPANERO_LAN
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
- Revisar qué ocurre cuando cambia la IP VPN del alumno. No se ha demostrado que `IP_CLIENTE_VPN` sea fija.
- Probar desde la VM compañera: su dirección se comunicó, pero no se aportó una sesión real desde ella.
- Revisar la rotación de `/var/log/denegados` si se conserva a largo plazo.

Consultas de verificación propuestas para la defensa; **no se han vuelto a ejecutar después de la aplicación final**:

```bash
grep -vE '^[[:space:]]*(#|$)' /etc/hosts.allow /etc/hosts.deny
tcpdchk -v
tcpdmatch sshd IP_CLIENTE_VPN
tcpdmatch sshd IP_COMPANERO_LAN
tcpdmatch sshd 192.0.2.10
tail -n 5 /var/log/denegados
```

## Servicios compatibles y explicación para la defensa

`apt-cache rdepends --installed libwrap0` enumeró openssh-server, tcpd, pulseaudio y libsnmp40t64. Una dependencia de paquete no demuestra un servicio activo ni cobertura de todos sus ejecutables. La muestra de `ss -tulnp` solo mostró sockets de SSH y su sesión. La compatibilidad verificada funcionalmente fue la de SSH.

TCP Wrappers consulta permisos dentro de servicios compatibles. Un firewall, por ejemplo nftables, filtra tráfico en la pila de red sin requerir esa integración. `tcpdmatch` simula una decisión, mientras que la entrada automática del intento real de loopback prueba el registro del rechazo. No confundir el host que escribe el log con la identidad del equipo/persona que intenta acceder.


---

## Apartado m) — Logs locales


**Registro del apartado.** Incluye las órdenes utilizadas, su finalidad, los resultados conocidos y el estado final. Los enlaces relativos apuntan a la guía separada del mismo repositorio.


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


---

## Anexo A — Apuntes cronológicos iniciales


Este anexo conserva el relato anterior a la separación por apartados. Incluye órdenes, salidas, decisiones y errores que podían perderse al resumir la guía.

Cuaderno de estudio de la práctica 1. Actualizado hasta el 9 de octubre de 2026, a petición del alumno. Distingue resultados comprobados, recomendaciones y tareas pendientes.

## Estado

**El estado vigente está resumido en la sección 8.** Las secciones anteriores conservan el contexto de instalación y actualización; sus inventarios iniciales no describen los servicios actuales. Esta actualización añade solo cambios que permanecen aplicados según las salidas de la VM, sin incorporar pruebas retiradas.

| Parte | Estado |
| --- | --- |
| a) Interfaces | Aplicadas; conexión al router comprobada |
| a) hosts | Archivo confirmado: IP_VM_ENS33 debian |
| a) resolv.conf | Resolución reparada y verificada; DNS originales primero |
| a) nsswitch.conf | Estado actual: files mdns4_minimal [NOTFOUND=return] dns |
| a) sources.list | Adaptado en cada salto; errores documentados |
| a) sudo | Pendiente de configurar y verificar con el usuario normal |
| b) Actualización | Debian 13.7 y kernel 6.12.111+deb13-amd64 verificados |
| c) Arranque y unidades | Explicados e inventarios interpretados; ssa pendiente |
| d) Tiempos de arranque | Última medida: 16,421 s; objetivo de 10–12 s todavía no alcanzado |
| e) Errores del journal | Corregida configuración residual de CUPS; logrotate termina correctamente |
| h) Limpieza | Escritorio retirado y ajustes vigentes documentados en sección 8; investigación en pausa de cambios |

## 1. /etc/network/interfaces

IP asignada indicada por el alumno: **IP_VM_ENS33**. Nombre observado: **debian**.

Configuración aplicada:

```text
auto lo ens33 ens34

iface lo inet loopback

iface ens33 inet static
    address IP_VM_ENS33
    netmask 255.255.254.0
    broadcast BROADCAST_ENS33
    network RED_ENS33
    gateway GATEWAY_ENS33

iface ens34 inet static
    address IP_VM_ENS34
    netmask 255.255.254.0
    broadcast BROADCAST_ENS34
    network RED_ENS34
```

Se corrigió `addres` por `address`.

### Por qué network es .48 y la IP es .49

La máscara 255.255.254.0 equivale a /23. La red RED_ENS33/23 abarca los bloques 10.11.48.x y 10.11.49.x. Sus hosts utilizables van de GATEWAY_ENS33 a IP_PRUEBA_LAN; BROADCAST_ENS33 es el broadcast.

La puerta de enlace GATEWAY_ENS33 es el router del ejemplo y respondió desde la máquina. No se calcula a partir de la IP ni tiene que terminar en .1.

### Por qué se propuso ens34 con .51

Se conservó la posición al pasar de la red RED_ENS33/23 a RED_ENS34/23: 49 pasa a 51. **Es una inferencia del ejemplo; falta confirmar la asignación del profesor.** IP_ALTERNATIVA_ENS34 también pertenece a la segunda red, pero es otra posición.

### Comprobaciones realizadas

```bash
sudo ifup --no-act ens33 ens34
sudo systemctl restart networking
ip route
ip -br addr
ping -c 4 GATEWAY_ENS33
```

`--no-act` muestra las operaciones previstas sin ejecutarlas; no comprueba conectividad ni detecta todos los errores. Aplicar cambios desde la consola de la VM permite recuperar el acceso si se interrumpe SSH.

Resultado observado:

```text
default via GATEWAY_ENS33 dev ens33 onlink
RED_ENS33/23 dev ens33 proto kernel scope link src IP_VM_ENS33
RED_ENS34/23 dev ens34 proto kernel scope link src IP_VM_ENS34
169.254.0.0/16 dev ens33 scope link metric 1000
```

- ens33: IP_VM_ENS33/23; ens34: IP_VM_ENS34/23.
- Ping al router: cuatro respuestas, 0 % de pérdida.
- UNKNOWN no impidió la comunicación en ens33.
- La ruta 169.254.0.0/16 pertenecía al estado inicial. Posteriormente se identificó su origen en el script avahi-autoipd y dejó de aparecer tras retirar ese script; véase sección 8.
- Pendiente: conectividad y asignación de ens34.

## 2. /etc/hosts

Relaciona IP con nombres localmente. Configuración inicial:

```text
127.0.0.1 localhost
127.0.1.1 debian

::1 localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
```

127.0.1.1 debian es una configuración válida y habitual. Se propuso sustituir esa línea por:

```text
IP_VM_ENS33 debian
```

Se conservan localhost y las entradas IPv6. El enunciado pide analizar estos archivos; no exige expresamente ese cambio.

```bash
getent hosts debian
getent ahostsv4 debian
```

El primero mostró IPv6 locales de enlace (fe80::). Eso no demuestra que hosts esté mal: getent puede consultar otras fuentes. El segundo consulta IPv4 y puede repetir la IP con STREAM, DGRAM y RAW. El alumno indicó que estaba bien, pero no aportó su salida ni el archivo final.

## 3. /etc/resolv.conf: DNS y resolución del fallo

Contenido inicial: dominio y búsqueda udc.pri, con DNS DNS_UDC_1 y DNS_UDC_2. Se añadieron DNS_AULA_1, DNS_AULA_2 y DNS_AULA_3 y llegaron a ocupar las tres primeras posiciones.

- domain establece el dominio local; search permite completar nombres cortos. En el resolvedor tradicional son alternativas y prevalece la última; aquí coinciden.
- nameserver identifica un servidor DNS. Una IP de la red no es necesariamente un DNS.
- El resolvedor tradicional de glibc utiliza hasta tres entradas nameserver. Tener cinco no implica utilizar las cinco.

**Síntoma:** APT mostraba «No se pudo resolver» y getent no devolvía direcciones. El router GATEWAY_ENS33 respondía al ping, pero DNS_UDC_1 no. Ese ping fallido no demostraba que DNS estuviera roto: ICMP y DNS son servicios distintos.

No había dig ni nslookup. Se usó host para consultar cada DNS sin cambiar primero el archivo:

~~~bash
host archive.debian.org DNS_AULA_1
host archive.debian.org DNS_AULA_2
host archive.debian.org DNS_AULA_3
host archive.debian.org DNS_UDC_1
host archive.debian.org DNS_UDC_2
~~~

| Servidor | Resultado observado |
| --- | --- |
| DNS_AULA_1, DNS_AULA_2, DNS_AULA_3 | Tiempo de espera agotado desde esta máquina |
| DNS_UDC_1 y DNS_UDC_2 | Respuesta DNS correcta para archive.debian.org |

**Solución aplicada:** conservar las cinco direcciones, como pidió el alumno, y colocar primero las dos que respondían:

~~~text
domain udc.pri
search udc.pri
nameserver DNS_UDC_1
nameserver DNS_UDC_2
nameserver DNS_AULA_1
nameserver DNS_AULA_2
nameserver DNS_AULA_3
~~~

Las dos últimas quedan escritas pero fuera del límite del resolvedor tradicional. No se ha determinado la función de las tres IP 10.8.12.x; no afirmar que sean inútiles en todos los entornos.

Verificación que sí se obtuvo después del cambio:

~~~bash
getent ahostsv4 archive.debian.org
~~~

Devolvió 151.101.2.132, 151.101.66.132, 151.101.130.132 y 151.101.194.132, repetidas con STREAM, DGRAM y RAW. Estas IP son una observación de la sesión, no valores para fijar manualmente. La resolución quedó funcionando.

## 4. /etc/nsswitch.conf

Revisado sin cambios. Línea observada:

```text
hosts: files mdns4_minimal [NOTFOUND=return] dns myhostname
```

Orden de consulta:

1. `files`: /etc/hosts.
2. `mdns4_minimal`: mDNS limitado, especialmente nombres .local.
3. `[NOTFOUND=return]`: termina si el módulo anterior devuelve NOTFOUND; no todos los fallos impiden usar DNS.
4. `dns`: resolución DNS.
5. `myhostname`: resolución del nombre de la máquina.

passwd, group, shadow y gshadow indican fuentes para usuarios, grupos y sus datos protegidos. `files` consulta el archivo de cada base de datos, no siempre /etc/hosts.

## 5. Apartado b: actualización de Debian

### Punto de partida y resultados

Versión inicial confirmada: Debian GNU/Linux 10.4 Buster, arquitectura amd64 (x86 de 64 bits). En la comprobación inicial, /dev/sda1 montado en / tenía 13 GB totales, 3,8 GB usados, 7,9 GB disponibles y 33 % de uso; esos valores no representan el espacio actual.

~~~bash
cat /etc/os-release
cat /etc/debian_version
dpkg --print-architecture
df -h /
~~~

Se siguieron saltos consecutivos, comprobando versión y kernel tras los reinicios:

| Etapa verificada | Kernel observado |
| --- | --- |
| Debian 10.13 Buster | 4.19.0-27-amd64 |
| Debian 11.11 Bullseye | 5.10.0-46-amd64 |
| Debian 12.15 Bookworm | 6.1.0-53-amd64 |
| Debian 13.7 Trixie | 6.12.111+deb13-amd64 |

**Resultado final confirmado:** Debian 13.7 arrancado y cero unidades en systemctl --failed. El alumno comunicó que las actualizaciones terminaron. No todas las salidas finales de APT de cada salto quedaron pegadas en la conversación; la evidencia explícita final es la versión, el kernel y el listado de unidades fallidas.

### Qué hace cada comando

~~~bash
su -
apt update
apt upgrade
apt full-upgrade
dpkg --audit
apt-mark showhold
reboot
~~~

- su - entra como root y carga su entorno. La contraseña no se muestra al escribirla. Como root no hace falta sudo.
- apt update descarga índices; no instala actualizaciones.
- apt upgrade actualiza sin eliminar paquetes instalados; puede dejar retenidos los que requieran cambios más amplios.
- apt full-upgrade resuelve transiciones que pueden necesitar sustituciones o eliminaciones. Revisar la propuesta antes de aceptarla.
- dpkg --audit detecta paquetes incompletos o inconsistentes; en las comprobaciones aportadas salió vacío.
- apt-mark showhold muestra bloqueos explícitos; salió vacío cuando se investigaron las retenciones.
- apt -s full-upgrade fue propuesto como simulación opcional; el alumno prefirió actualizar directamente.

Se recomendó una instantánea de la VM antes de los saltos, pero no consta que se creara. Los bloques de repositorios siguientes son históricos: no deben mezclarse ni copiarse todos a la vez en la máquina ya actualizada.

### Buster: errores 404 en los repositorios antiguos

Las entradas iniciales apuntaban a deb.debian.org con buster y buster-updates, y a security.debian.org con buster/updates. Devolvían 404 porque Buster se trasladó al archivo histórico. «Todos los paquetes están actualizados» tras un update fallido no era una comprobación válida: APT conservaba índices anteriores.

Se guardó/proporcionó el procedimiento de copia antes de editar y se sustituyeron las seis entradas activas, conservando comentarios originales:

~~~bash
cp -an /etc/apt/sources.list /etc/apt/sources.list.bak
nano /etc/apt/sources.list
~~~

~~~text
deb http://archive.debian.org/debian/ buster main
deb-src http://archive.debian.org/debian/ buster main

deb http://archive.debian.org/debian-security/ buster/updates main contrib
deb-src http://archive.debian.org/debian-security/ buster/updates main contrib

deb http://archive.debian.org/debian/ buster-updates main contrib
deb-src http://archive.debian.org/debian/ buster-updates main contrib
~~~

Al principio APT seguía mostrando los servidores antiguos: el cambio no se reflejaba aún en el archivo utilizado. Se explicó guardar en nano con Ctrl+O, Enter y salir con Ctrl+X, y comprobar con cat. Posteriormente el alumno confirmó apt update correcto y actualizó hasta 10.13.

### GRUB y preguntas durante la instalación

1. GRUB advirtió que su referencia anterior al disco había cambiado. Se indicó marcar el disco completo /dev/sda con Espacio hasta ver [*], dejando /dev/sda1 sin marcar.
2. Apareció «¿continuar sin instalar GRUB?» porque resaltar la fila no la había seleccionado. Se indicó No, volver, marcar /dev/sda y aceptar. El alumno confirmó la continuación y los arranques posteriores funcionaron.
3. Al actualizar libc6 se autorizó el reinicio automático de los servicios afectados: Yes. No equivale a reiniciar toda la VM.
4. En un salto posterior se preguntó por /etc/default/grub modificado: se indicó conservar la versión local actualmente instalada. Esto conserva la configuración, no impide actualizar GRUB.

### Bullseye: índices disponibles pero paquetes de seguridad ausentes

Se configuraron bullseye, bullseye-security y bullseye-updates. El nombre correcto es bullseye-security, sin /updates. Añadir non-free o cambiar el orden de componentes no resolvía los 404.

El índice ofrecía, entre otros, libudisks2-0 2.9.2-2+deb11u3 y linux-image-amd64 5.10.262-1, pero las descargas desde security.debian.org devolvían 404.

Diagnóstico realizado:

~~~bash
apt -o Acquire::http::No-Cache=true update
dpkg --audit
apt-cache policy libudisks2-0 linux-image-amd64
cd /tmp
apt download libudisks2-0
~~~

Se probó cambiar al servidor oficial deb.debian.org/debian-security. Se propuso HTTPS, aunque varias salidas seguían mostrando HTTP; una comprobación directa externa con HTTPS confirmó que el archivo también faltaba allí. **El protocolo no era una solución confirmada.** Tampoco estaba disponible ese archivo en la ruta probada de archive.debian.org.

Se eliminaron únicamente los índices locales de seguridad de Bullseye para forzar su descarga:

~~~bash
find /var/lib/apt/lists -maxdepth 1 -type f -name '*bullseye-security*' -delete
apt update
apt-cache policy libudisks2-0
~~~

El índice nuevo seguía anunciando la versión ausente. Quedó comprobada la discrepancia índice/archivo; no se determinó el motivo administrativo de su retirada.

**Solución utilizada para continuar:** copia oficial de Debian Snapshot del 31 de agosto de 2026. Se verificó respuesta HTTP 200 tanto para Release como para el paquete de prueba. Se sustituyeron las dos entradas de seguridad, manteniendo las cuatro normales de Bullseye:

~~~text
deb http://deb.debian.org/debian/ bullseye main contrib
deb-src http://deb.debian.org/debian/ bullseye main contrib

deb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20260831T000000Z/ bullseye-security main contrib
deb-src [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20260831T000000Z/ bullseye-security main contrib

deb http://deb.debian.org/debian/ bullseye-updates main contrib
deb-src http://deb.debian.org/debian/ bullseye-updates main contrib
~~~

check-valid-until=no permite un índice histórico caducado, solo en esas entradas; se mantienen las comprobaciones de firmas. Fue un paso temporal, sustituido al pasar a Bookworm. No se debe conservar esta instantánea como fuente de actualizaciones actuales.

Después de update y la prueba de descarga se continuó instalando. Un upgrade dejó 284 paquetes retenidos; se indicó full-upgrade para completar las transiciones. Escribir s en el prompt root@debian no responde a APT: solo se contesta cuando APT pregunta. Se confirmó finalmente Debian 11.11 con kernel 5.10.0-46-amd64.

### Bookworm: faltaba main y no se completaba el salto

Se sustituyeron todas las entradas de Bullseye, incluidas Snapshot, por Bookworm. Durante la edición quedaron las primeras líneas como bookworm contrib, **sin main**.

Síntomas: full-upgrade dejaba 34 paquetes retenidos; /etc/debian_version seguía mostrando 11.11. systemd seguía instalado en 247.3-7+deb11u8, y sus candidatos solo aparecían desde bookworm-security. dpkg --audit y apt-mark showhold estaban vacíos.

~~~bash
cat /etc/apt/sources.list
grep -R -n -E '^(deb|Types:|URIs:|Suites:|Components:|Enabled:)' /etc/apt/sources.list.d/
apt update
apt-cache policy systemd libnss-systemd libpam-systemd systemd-timesyncd
~~~

El directorio adicional no mostró entradas. **Solución:** recuperar main en las dos primeras líneas; después apt update y apt full-upgrade. Configuración corregida:

~~~text
deb http://deb.debian.org/debian/ bookworm main contrib
deb-src http://deb.debian.org/debian/ bookworm main contrib

deb http://security.debian.org/debian-security bookworm-security main contrib
deb-src http://security.debian.org/debian-security bookworm-security main contrib

deb http://deb.debian.org/debian/ bookworm-updates main contrib
deb-src http://deb.debian.org/debian/ bookworm-updates main contrib
~~~

APT también listó muchos paquetes como prescindibles, incluidos sudo y openssh-server. Se indicó **no ejecutar autoremove** y se propuso proteger estos paquetes:

~~~bash
apt-mark manual sudo openssh-server openssh-sftp-server
~~~

No se aportó salida de este último comando; no dar su ejecución por verificada. Más adelante ssh.service sí apareció ejecutándose. Sigue pendiente revisar si alguna aplicación deseada fue retirada durante los intentos previos. Tras corregir main, se confirmó arranque en 12.15 con kernel 6.1.0-53-amd64.

### Trixie y estado final

Se indicó guardar sources.list.bookworm.bak y reemplazar las seis entradas activas por:

~~~text
deb https://deb.debian.org/debian/ trixie main contrib
deb-src https://deb.debian.org/debian/ trixie main contrib

deb https://security.debian.org/debian-security/ trixie-security main contrib
deb-src https://security.debian.org/debian-security/ trixie-security main contrib

deb https://deb.debian.org/debian/ trixie-updates main contrib
deb-src https://deb.debian.org/debian/ trixie-updates main contrib
~~~

Es la configuración indicada para el último salto; no se pegó un cat final del archivo. Se comunicó que todo estaba actualizado y se verificó:

~~~text
cat /etc/debian_version → 13.7
uname -r → 6.12.111+deb13-amd64
systemctl --failed → 0 loaded units listed.
~~~

## 6. Apartado c: arranque y systemd

### Desde el encendido hasta el login

1. El firmware BIOS/UEFI inicializa el hardware virtual y elige el dispositivo de arranque. No se realizó una comprobación específica del modo de firmware.
2. GRUB carga el kernel y el initramfs y pasa los parámetros de arranque.
3. El kernel inicializa memoria, procesos y controladores. El initramfs aporta un entorno temporal para localizar y montar la raíz real.
4. Se pasa al sistema instalado. systemd actúa como PID 1 y organiza el espacio de usuario.
5. Activa montajes, dispositivos y servicios según dependencias, con tareas en paralelo.
6. Alcanza el target predeterminado y ofrece login por consola y, si el gestor funciona, gráfico.

**Firmware → GRUB → kernel + initramfs → raíz real → systemd → servicios → login.**

### Targets

~~~bash
systemctl get-default
systemctl list-units --type=target --all --no-pager
systemctl list-unit-files --type=target --no-pager
~~~

Resultado: graphical.target predeterminado, 52 unidades listadas en la primera consulta y 78 archivos en la segunda. Son vistas distintas: unidades que systemd conoce en ese momento frente a archivos, plantillas y alias disponibles. El resumen «loaded units» puede incluir entradas not-found.

multi-user.target y graphical.target estaban ambos activos; graphical incorpora multi-user y solicita el inicio gráfico. Alcanzarlo no demuestra que el escritorio funcione. También estaban activos sysinit, basic, local-fs, getty, network y network-online. network-online no garantiza acceso a Internet. Rescue, shutdown o suspend inactivos son normales cuando no se utilizan.

Comandos explicados inicialmente; posteriormente se aplicó `set-default multi-user.target` (sección 8):

~~~bash
systemctl set-default multi-user.target
systemctl set-default graphical.target
~~~

Cambian el objetivo del siguiente arranque, no la sesión actual. default.target es un alias. display-manager.target figuró not-found; no se reparó. La unidad habitual de inicio gráfico es display-manager.service, que sí apareció como alias en el inventario de servicios.

### Servicios: ejecución frente a habilitación

~~~bash
systemctl list-units --type=service --all --no-pager
systemctl list-unit-files --type=service --no-pager
~~~

Resultados: 133 unidades en la vista de estado y 220 entradas en la de archivos. No son 220 procesos.

| Estado de ejecución/carga | Interpretación |
| --- | --- |
| active running | Servicio activo y proceso ejecutándose |
| active exited | Proceso de activación terminado, unidad mantenida activa |
| inactive dead | No está ejecutándose; no implica error |
| not-found | Definición no encontrada para una unidad referenciada |
| masked | Activación bloqueada |

| STATE en list-unit-files | Interpretación |
| --- | --- |
| enabled | Habilitado mediante enlaces de instalación |
| disabled | Sin habilitación; puede activarse por otros medios |
| static | Sin instrucciones normales de habilitación en Install |
| alias | Otro nombre de unidad |
| generated | Definición producida por un generador |
| enabled-runtime | Habilitación temporal que desaparece al reiniciar |
| indirect | Habilitación relacionada con otras unidades, alias o instancias |
| bad | Error al determinar el estado del archivo/habilitación |

PRESET es la política predeterminada, no el estado actual. Que reboot.target esté disabled no impide solicitar un reinicio. No confundir enable con start, ni disabled con parado.

Ejemplos observados:

| Unidad | Habilitación | Ejecución |
| --- | --- | --- |
| ssh, cron, rsyslog | enabled | active running |
| networking | enabled | active exited |
| fwupd | static | active running |
| rtkit-daemon | disabled | active running |
| systemd-journald | static | active running |
| systemd-timesyncd | enabled | active running |
| open-vm-tools | enabled | active running |
| gdm3 | generated | active exited, descripción LSB |

networking configura interfaces y puede terminar sin dejar proceso. network-manager.service figuraba not-found, pero NetworkManager.service sí estaba activo: los nombres distinguen mayúsculas. Networking y NetworkManager estaban presentes; no se concluyó que hubiera un conflicto ni se desactivó ninguno. sudo.service masked no demuestra que el comando sudo no funcione. No instalar todas las unidades not-found ni desbloquear todas las masked sin analizar su función.

### Incidencia pendiente: ssa.service

El inventario mostraba bad. Se investigó con:

~~~bash
systemctl status ssa.service --no-pager -l
systemctl cat ssa.service
systemctl is-enabled ssa.service
ls -l /etc/systemd/system/ssa.service
ls -l /etc/systemd/system/multi-user.target.wants/ssa.service
ls -l /usr/lib/systemd/system/ssa.service
dpkg -S /usr/lib/systemd/system/ssa.service /usr/sbin/ssa
readlink -f /etc/systemd/system/ssa.service
readlink -f /etc/systemd/system/multi-user.target.wants/ssa.service
dpkg -S /lib/systemd/system/ssa.service
systemd-analyze verify /usr/lib/systemd/system/ssa.service
systemctl daemon-reload
systemctl is-enabled ssa.service
~~~

Resultados:

- ExecStart=/usr/sbin/ssa terminó con status=0/SUCCESS; servicio inactive, desactivado correctamente.
- is-enabled devolvió «Too many levels of symbolic links», también tras daemon-reload.
- Ambos enlaces apuntaban a /lib/systemd/system/ssa.service y readlink -f resolvió /usr/lib/systemd/system/ssa.service. **No se demostró un bucle en esas rutas.**
- El archivo era normal; dpkg -S no encontró paquete propietario en las rutas consultadas.
- verify no mostró errores.
- La sección Install contiene WantedBy=multi-user.target y Alias=ssa.service. El alias que repite su nombre es sospechoso, pero no se confirmó como causa.

La primera explicación de un bucle confirmado fue demasiado concluyente y se corrigió. Podría ser una personalización del laboratorio, pero no está demostrado. **No se editó ni borró nada; se decidió dejar la incidencia pendiente y continuar.** daemon-reload solo releyó definiciones.

### Otros tipos de unidades

| Tipo | Función |
| --- | --- |
| .socket | Punto de comunicación, puede activar un servicio |
| .timer | Activación programada |
| .path | Vigilancia de rutas para activar unidades |
| .mount / .automount | Montaje y montaje bajo demanda |
| .device | Dispositivo reconocido |
| .swap | Intercambio |
| .slice / .scope | Agrupación y gestión de recursos de procesos |

## 7. Apartado d: tiempos de arranque

~~~bash
systemd-analyze time
systemd-analyze blame --no-pager
systemd-analyze critical-chain graphical.target
~~~

### Medidas obtenidas

| Medida | Tiempo |
| --- | --- |
| Kernel según systemd | 6,564 s |
| Userspace | 39,707 s |
| Total mostrado | 46,272 s |
| graphical.target desde comienzo de userspace | 39,696 s |

El total es el mostrado por la herramienta; el redondeo de sus componentes explica la pequeña diferencia al sumarlos. No se mostraron tiempos separados de firmware/GRUB y no debe interpretarse como cronómetro desde pulsar encendido. El campo kernel puede incluir fases tempranas que no se desglosan aparte.

blame mide duración de activación, no tiempo total de ejecución ni CPU. Incluye servicios, dispositivos y montajes. No se suman sus duraciones: muchas unidades trabajan en paralelo.

| Unidad destacada | Duración |
| --- | --- |
| apparmor.service | 25,674 s |
| fwupd.service | 4,715 s |
| ifupdown-pre.service | 4,560 s |
| dev-sda1.device | 4,435 s |
| udisks2.service | 3,972 s |
| accounts-daemon.service | 3,396 s |
| polkit.service | 3,083 s |
| avahi-daemon.service | 3,002 s |
| networking.service | 2,798 s |
| dbus.service | 2,668 s |
| NetworkManager.service | 2,422 s |
| ssh.service | 433 ms |

### Cadena crítica observada

~~~text
graphical.target @39.696s
└─power-profiles-daemon.service @39.528s +167ms
  └─multi-user.target @39.510s
    └─exim4.service @38.422s +1.086s
      └─network-online.target @38.395s
        └─NetworkManager-wait-online.service @38.148s +241ms
          └─NetworkManager.service @35.694s +2.422s
            └─dbus.service @32.990s +2.668s
              └─basic.target @32.856s
                └─sockets.target @32.839s
                  └─systemd-hostnamed.socket @32.839s
                    └─sysinit.target @32.813s
                      └─apparmor.service @7.131s +25.674s
                        └─local-fs.target @7.110s
                          └─tmp.mount @7.073s +35ms
                            └─swap.target @7.063s
                              └─dev-sda5.swap @6.965s +91ms
                                └─dev-sda5.device @6.958s
~~~

@ indica el instante de inicio/activación desde userspace; +, duración de activación. AppArmor comenzó a 7,131 s y terminó aproximadamente a 32,805 s, justo antes de sysinit.target a 32,813 s. Es el tramo más largo mostrado en esta cadena. No se puede prometer que desactivarlo ahorre exactamente 25,674 s; hay trabajo paralelo. **En aquella medición inicial todavía no se había cambiado la configuración. El estado posterior se documenta en la sección 8.**

## 8. Configuración vigente después de la limpieza — 9 de octubre de 2026

Este apartado describe lo que permanece aplicado según las últimas salidas compartidas. No es un script para copiar entero ni una recomendación general para cualquier Debian. La máquina es del laboratorio, se administra por SSH y dispone de consola; no hay acceso a cambios de hardware del hipervisor. No se han modificado CPU, RAM, disco ni modelo de tarjetas virtuales.

### 8.1 Sistema y resultado medido

- Debian 13.7, kernel `6.12.111+deb13-amd64`, arquitectura amd64.
- VMware, una CPU virtual y aproximadamente 1,4 GiB de RAM visible.
- Arranque por `multi-user.target`, sin escritorio. Se aplicó `systemctl set-default multi-user.target`.
- Red estática conservada: ens33 `IP_VM_ENS33/23`, ens34 `IP_VM_ENS34/23`, gateway `GATEWAY_ENS33` por ens33. DNS funciona en las comprobaciones con `getent`.
- Última medida: **6,389 s de kernel/preparación inicial + 10,031 s de userspace = 16,421 s**. `multi-user.target` se alcanzó a los 10,030 s de userspace. No equivale al tiempo completo desde pulsar encendido ni demuestra por sí solo el instante de acceso SSH desde otro equipo.
- Última comprobación: cero unidades fallidas, swap de 1,5 GiB activa y sin uso.
- Último espacio comprobado: raíz de 13 GB, 3,1 GB usados, 8,6 GB disponibles (27 %).

Las mediciones varían entre reinicios. No se atribuye una cantidad fija de segundos a cada cambio: las tareas se solapan y `blame` mide activación, no consumo continuo de CPU. El objetivo de 10–12 segundos totales **no está alcanzado**.

### 8.2 Paquetes retirados

Se ejecutó `python3 limpieza-lsi.py paquetes`, que purgó la selección revisada de aplicaciones y configuraciones de escritorio. Entre ellas: GNOME Shell y sesión, GDM, terminal y utilidades gráficas, juegos, Firefox ESR, Nautilus, aplicaciones multimedia, Transmission gráfico y configuraciones residuales de LibreOffice. Algunas entradas purgadas ya no tenían los binarios instalados: purgar también elimina configuración residual.

Después el alumno ejecutó `apt autoremove`. El historial confirmó la retirada de numerosas dependencias gráficas y bibliotecas antiguas, además de `network-manager`, `wpasupplicant`, `fwupd`, `power-profiles-daemon`, `accountsservice`, `libnss-myhostname`, `unzip`, `7zip` y `jq`, entre otros. No se encontraron SSH, ifupdown, el kernel ni open-vm-tools entre los paquetes eliminados por esa transacción. Se comprobó `dpkg --audit` sin incidencias y se volvió a acceder por SSH después del reinicio.

La ausencia de `libnss-myhostname` significa que ya no se dispone de ese módulo para resolver el nombre propio. El inventario del 9 de octubre confirma que la línea hosts de nsswitch.conf ya no incluye myhostname: `hosts: files mdns4_minimal [NOTFOUND=return] dns`. No se atribuye su retirada a un comando concreto. Los comandos de DNS externos sí respondieron. Las utilidades retiradas se pueden reinstalar cuando la práctica las necesite. No ejecutar de nuevo la limpieza para reproducir estos apuntes sin revisar antes el estado de cada máquina.

Se instaló `strace` (y su dependencia `libunwind8`); no se ha comunicado su desinstalación. Es una herramienta disponible, no un servicio de arranque.

### 8.3 Servicios bloqueados

Se aplicaron máscaras para impedir la activación de:

```text
NetworkManager.service
NetworkManager-wait-online.service
avahi-daemon.service
avahi-daemon.socket
ModemManager.service
wpa_supplicant.service
exim4.service
e2scrub_reap.service
apparmor.service
```

NetworkManager y wpasupplicant fueron además retirados por autoremove. Las interfaces las configura **ifupdown mediante networking.service**, que se conserva, al igual que SSH. La máscara de Exim impide arrancar su servicio habitual, pero no equivale a desinstalar todo el correo ni a demostrar que todos sus temporizadores estén bloqueados. `e2scrub_reap` se bloqueó en una máquina sin LVM; no se debe inferir que se hayan desactivado las comprobaciones de ext4 o todos los temporizadores de e2scrub.

La última consulta explícita de AppArmor devuelve `masked`. Se omite la carga de perfiles por ese servicio; el módulo del kernel puede continuar cargado. **Es una reducción de protección**, no una mejora de rendimiento cuantificada. El mensaje observado de aa-status no permite afirmar el número final de perfiles cargados. No se eliminaron los archivos de perfiles.

`systemd-journal-flush.service` **todavía no se ha bloqueado**: aparece en el último `blame`. La propuesta posterior de bloquearlo no cuenta como cambio aplicado.

### 8.4 Preparación de las interfaces

Archivo añadido: `/etc/systemd/system/ifupdown-pre.service.d/90-lsi-red.conf`:

```ini
[Service]
ExecStart=
ExecStart=/bin/sh -c '/bin/udevadm wait --timeout=30 /sys/class/net/ens33 /sys/class/net/ens34 || /bin/udevadm settle --timeout=120'
```

Reemplaza la espera global inicial por una espera a que ambas interfaces estén inicializadas. Si falla, utiliza la espera general como respaldo. Se conserva la unidad original y su orden respecto a udev. Es específico de esos dos nombres de interfaz: debe revisarse si cambian. La activación observada de ifupdown-pre bajó a unos 0,08–0,10 segundos; no se traduce en restar automáticamente cuatro segundos al total.

Se apartaron los siguientes scripts, conservándolos en directorios de respaldo con fecha bajo `/root/lsi-hooks-red-*` y `/root/lsi-hooks-extra-*`:

| Directorio original | Scripts apartados |
| --- | --- |
| `/etc/network/if-pre-up.d/` | `wireless-tools`, `wpasupplicant`, `ethtool` |
| `/etc/network/if-up.d/` | `wpasupplicant`, `avahi-autoipd`, `ethtool`, `resolved` |

No se usan opciones Wi-Fi/WPA ni ajustes ethtool personalizados en interfaces; resolv.conf es un archivo regular con DNS configurados manualmente. Se confirmó que el script resolved consultaba un servicio no habilitado y que los scripts ethtool no ejecutaban la herramienta para estas interfaces. La ruta adicional `169.254.0.0/16`, creada por avahi-autoipd, dejó de aparecer. Se conservaron las dos redes estáticas y la ruta por defecto.

Esto afecta a la integración automática futura con esas herramientas: si cambia la forma de configurar la red habrá que revisar los scripts. No se ha demostrado un ahorro global significativo atribuible a retirarlos.

### 8.5 Regla de disco y módulos

Se creó el enlace `/etc/udev/rules.d/85-hdparm.rules` a `/dev/null`, desactivando la regla homónima del sistema. Su ejecución sobre el disco SATA virtual aplicaba APM 254; la traza previa mostró alrededor de un segundo de duración. No se cambiaron los controladores del disco, las particiones ni la caché de escritura. No se garantiza que ese segundo se ahorre entero en el arranque.

Archivo añadido `/etc/modprobe.d/90-lsi-vm.conf`:

```text
blacklist intel_uncore
blacklist intel_cstate
blacklist sb_edac
```

Esos módulos de monitorización del hardware físico fallaban al cargarse en esta VM. Se bloqueó su carga automática por alias; no se desactivaron las mitigaciones de seguridad de CPU ni los módulos de cifrado. No se documentó una reconstrucción del initramfs para este ajuste.

### 8.6 Journal: estado persistente confirmado

**Corrección tras recibir el inventario completo del 9 de octubre:** el modo en RAM se había indicado, pero no aparece aplicado en la configuración recogida. No se debe contabilizar como un cambio vigente.

`systemd-analyze cat-config systemd/journald.conf` no muestra el archivo propuesto `90-lsi-volatil.conf` ni una opción activa `Storage=volatile`. Los registros del mismo arranque muestran explícitamente el volcado a `/var/log/journal`, 1,250966 segundos para 1321 entradas y un journal persistente de 84,1 MB. El servicio journal-flush tardó 1,746 segundos en total. La medida de 16,421 segundos corresponde a ese arranque con almacenamiento persistente; no demuestra una mejora por pasar el journal a RAM.

La configuración de proveedor `/usr/lib/systemd/journald.conf.d/syslog.conf` contiene `ForwardToSyslog=yes`; rsyslog sigue presente. Los archivos existentes pasaron `journalctl --verify`. No se eliminaron registros por supuesta corrupción. Antes de cualquier cambio adicional debe comprobarse qué ocurrió con el archivo propuesto; no se ha corregido ni recreado automáticamente en la VM.

### 8.7 Corrección de logrotate

Se identificó una configuración residual de CUPS en `/etc/logrotate.d/cups*` que intentaba reiniciar `cups` aunque su servicio ya no estaba instalado. Los paquetes CUPS relevantes figuraban como `rc` (retirados con configuración residual).

Se apartó esa configuración en `/root/respaldo-logrotate/`. Logrotate volvió a finalizar con `status=0/SUCCESS`. Su estado `inactive (dead)` después de terminar es normal para esta tarea periódica. El archivo `/var/lib/logrotate/status` se observó con permisos `640`, propietario root:root; no se atribuye a un comando concreto que no quedó registrado.

### 8.8 Componentes conservados y punto de espera

Se mantienen el sistema base, kernel, GRUB, udev, D-Bus, SSH, ifupdown, swap, journald, rsyslog, sincronización horaria y herramientas VMware. El inventario confirma además máscaras en console-setup.service, keyboard-setup.service, tpm2-abrmd.service y run-vmblock\x2dfuse.mount; no consta en esta documentación el comando que las creó. No se atribuyen todas las máscaras del sistema a la limpieza, porque algunas vienen de los paquetes. `ssa.service` no se modificó: su función exacta sigue pendiente de aclarar y terminó correctamente en las salidas revisadas.

La swap conserva la entrada normal de `/etc/fstab`:

```text
/dev/sda5 none swap sw 0 0
```

En el último arranque la cadena que terminó en SSH pasó por dispositivos/swap, sistemas de archivos y networking. La configuración de red tardó 3,399 s; no se deben sumar las duraciones de todas las unidades del listado blame.

**Punto de espera solicitado:** no aplicar más cambios, máscaras, purgas o reinicios de diagnóstico hasta estudiar el inventario actual. Se investigarán preparación inicial/initramfs, reglas udev, carga estática de módulos, dependencias y activadores de servicios, configuración de red y contención durante el arranque. Ninguna hipótesis adicional se considera aplicada o demostrada. Se mantienen pendientes la verificación de sudo y los apartados posteriores de la práctica.

## 9. Uso del repositorio y fuentes

Actualizar estos apuntes **solo cuando el alumno lo pida expresamente**. Por cada paso distinguir comandos ejecutados, recomendaciones y resultados confirmados. No guardar contraseñas, claves ni tokens. El enunciado pide no añadir comentarios a los archivos de configuración salvo los originales: las explicaciones se guardan aquí.

El repositorio se creó público. Un compañero puede leerlo con el enlace; para editar se explicó Settings → Collaborators → Add people y aceptar la invitación. No se ha verificado que la invitación se enviara. Cada alumno debe adaptar las IP a su asignación; no duplicar la IP de esta máquina.

Fuentes consultadas durante la sesión:

- [Traslado de Buster al archivo histórico](https://lists.debian.org/debian-devel-announce/2025/06/msg00001.html)
- [Debian Snapshot: uso de archivos históricos y validez](https://snapshot.debian.org/)
- [Actualización de Debian 11 a 12](https://www.debian.org/releases/bookworm/amd64/release-notes/ch-upgrading.en.html)
- [Actualización de Debian 12 a 13](https://www.debian.org/releases/trixie/release-notes/upgrading.html)
- [Estados de unidades: documentación de systemctl](https://github.com/systemd/systemd/blob/main/man/systemctl.xml)

## Historial de los apuntes

- 2026-09-25: recopilación inicial de red y archivos básicos.
- 2026-10-02: registrada la versión inicial 10.4, amd64 y espacio disponible.
- 2026-10-07: actualización solicitada expresamente: DNS resuelto, saltos hasta 13.7, incidencias y soluciones, apartados c y d, y pendientes para continuar en e. Las fechas del historial corresponden a la documentación, no a una fecha exacta demostrada para cada comando de la VM.

- 2026-10-09: actualización solicitada: configuración vigente de la limpieza, servicios, red, journal, logrotate y último arranque; solo se añaden cambios mantenidos, sin incorporar pruebas revertidas.


---

## Anexo B — Bitácora aportada por el alumno


Se incorpora completa como evidencia cronológica. Contiene especialmente las sesiones detalladas de los apartados k), l) y m), con comandos, salidas reales, incidencias, recuperaciones y decisiones finales.

**Repositorio:** https://github.com/Thaang3l/LSI-P1  
**Enunciado de referencia:** `lsi-practica1-2026.pdf` (revisión septiembre de 2026)  
**Inicio de la bitácora:** 10 de octubre de 2026  
**Destino previsto:** añadir posteriormente al repositorio de GitHub.  

> Este archivo recoge lo tratado y las comprobaciones realizadas durante esta conversación. No constituye por sí mismo una prueba de que un comando se haya ejecutado en la VM. Se diferenciará siempre entre **comprobado**, **documentado en GitHub**, **propuesto** y **pendiente**.

## 1. Material consultado

- Repositorio: `Thaang3l/LSI-P1`, rama `main`.
- Archivo principal: `README.md`.
- Directorio `guia/`: documentación de los apartados de la práctica y guion de defensa.
- Directorio `companion/`: bot de Telegram, unidad de systemd y pruebas.
- Enunciado oficial de LSI: Práctica I, dos páginas, revisión septiembre de 2026.

## 2. Estado inicial documentado en GitHub (10/10/2026)

Este inventario procede del repositorio, **no de una nueva revisión de la VM**.

| Apartado | Estado reflejado en la documentación |
| --- | --- |
| a | Red y DNS trabajados; configuración y verificación de `sudo` pendientes. |
| b | Actualización Debian 10 → 11 → 12 → 13 documentada. |
| c | Arranque, targets, services y unidades estudiados; `ssa.service` sin resolver. |
| d | Medidas de arranque documentadas; última: 17,356 s. |
| e | Análisis de errores y corrección del problema con `logrotate` documentados. |
| f | Dirección lógica adicional de red probada y retirada; falta contrastar el alcance completo del enunciado. |
| g | Ruta estática añadida y elección de ruta comprobada; cambio no persistente. |
| h | Limpieza y revisión de configuraciones documentadas. |
| i | Bot de Telegram y `lsi-companion.service` documentados como funcionales. |
| j | Pendiente de ejecutar/interpretar las salidas de `ss`. |
| k | Completado (10/10/2026): monitorización con `top`, `free -h` y `watch` + `ss`. |
| l | Pendiente. |
| m | Completado (10/10/2026): pruebas locales con `logger`, rsyslog y journald. |
| Segunda parte | NTPSec, rsyslog en pareja, auditoría de IA, revisión de espacio y Splunk pendientes según el repositorio. |

### Datos de la VM tal como aparecen en el README

- Debian 13.7, amd64; kernel `6.12.111+deb13-amd64`.
- Target de inicio `multi-user.target`.
- `ens33`: `IP_VM_ENS33/23`; gateway `GATEWAY_ENS33`.
- `ens34`: `IP_VM_ENS34/23`.
- SSH habitual en puerto 22.
- Bot `lsi-companion.service`, con consulta de datos y curiosidades por Telegram.
- Última medición de arranque: kernel 6,891 s + userspace 10,465 s = 17,356 s.
- Meta personal de arranque de 10–12 segundos no alcanzada ni exigida literalmente por el enunciado.

Estas IP y medidas son particulares de la VM documentada.

## 3. Requisitos relevantes del enunciado

### Primera parte (apartados a–m)
Configuración, actualización del sistema, arranque y systemd, tiempos, análisis con IA de `journalctl -p 3 -b`, parámetros de `ens34`, rutas, limpieza, automatización en arranque, conexiones de red, monitorización en tiempo real, filtrado SSH y registro local con rsyslog/journald.

Atención especial a:
- **f)** identificar y cambiar los principales parámetros de `ens34`, configurar una segunda interfaz lógica y recuperar el estado original.
- **i)** utilizar IA en el desarrollo, configurar un servicio systemd que arranque cuanto antes y compararlo con cron.
- **l)** configurar y verificar el filtrado solicitado, teniendo en cuenta la compatibilidad real de SSH con tcp-wrappers y el registro de accesos denegados.
- **m)** probar explícitamente rsyslog y journald.

### Segunda parte
1. Configuración de NTPSec servidor/cliente con un compañero.
2. Cruce de roles para rsyslog servidor/cliente.
3. Auditoría de seguridad de la configuración del servidor rsyslog con IA y evaluación de sus propuestas.
4. Identificación de medidas para reducir el uso de disco.
5. Instalación de Splunk, consultas de logs internos, ingestión de Apache y journald, análisis de IP y geolocalización, `hosts`, `sources`, `sourcetypes`, y posible recepción de logs de un cliente.

### Condiciones de la evaluación
- El profesor evaluará las habilidades del alumno **trabajando sobre la máquina**.
- Los ficheros de configuración **no deben incorporar comentarios nuevos**, salvo los que traigan de origen.
- No publicar contraseñas, tokens ni otros secretos en GitHub.

## 4. Trabajo realizado específicamente en esta conversación

### 10/10/2026 — Preparación y revisión de fuentes
**Comprobado aquí:**
- Acceso y lectura del `README.md` de `Thaang3l/LSI-P1`.
- Inspección de los directorios y lectura de la documentación en `guia/` y del código en `companion/`.
- Lectura del enunciado aportado por el alumno y comparación con lo documentado en el repositorio.

**Resultado:**
- Se identificaron los apartados todavía pendientes y los puntos donde el alcance documentado puede no cubrir íntegramente el enunciado.
- Se acordó trabajar progresivamente y mantener esta bitácora para subirla al repositorio más adelante.

**Cambios en la VM:** ninguno realizado en esta conversación.  
**Cambios en GitHub:** ninguno realizado en esta conversación.

## 5. Próximas tareas

- Continuar con el apartado **j)** (inventario real de conexiones, `ss -tulnp` y `ss -tnp state established`) o con el apartado que solicite el alumno.
- Registrar cada comando, su objetivo, la salida relevante, la interpretación y el resultado.
- Señalar por separado errores, correcciones, cambios revertidos y pendientes.
- Preparar el contenido en formato Markdown para integrarlo después en `guia/` o en otro lugar que se elija.

## 6. Plantilla para nuevas entradas

### AAAA-MM-DD — [Apartado y tarea]
**Objetivo:**  
**Estado inicial:**  
**Comandos y acciones:**  
```bash
# Sustituir por comandos realmente ejecutados (no copiar esta línea a ficheros de configuración)
```
**Resultados aportados/comprobados:**  
**Explicación para la defensa:**  
**Estado final:** completado / parcial / pendiente.  
**Archivos modificados:**  
**Notas o próximos pasos:**  

---


## 7. Sesión del 10/10/2026 — Apartado m: registro local con rsyslog y journald

**Requisito literal del enunciado:** «Existen múltiples paquetes para la gestión de logs (syslog, syslog-ng, rsyslog). Utilizando el rsyslog pruebe su sistema de log local. Pruebe también el journald.»

**Estado:** COMPLETADO (comprobación práctica de rsyslog y journald con un mensaje de prueba).

**Objetivo:** verificar `rsyslog` y `systemd-journald` y comprobar la recepción y recuperación de un evento local con ambos mecanismos.

### Paso 1 — Estado y configuración básica (comprobado con las salidas del alumno)

Como root se ejecutaron:

```bash
systemctl status rsyslog --no-pager -l
systemctl status systemd-journald --no-pager -l
dpkg -l rsyslog
ls -l /var/log/syslog
```

**Resultados observados (10/10/2026):**

- `rsyslog.service`: `loaded`, `enabled`, `active (running)` desde las 00:43:04 CEST. Proceso `rsyslogd`, PID 538, 4 MB de memoria, versión en mensajes de servicio `8.2504.0`; paquete instalado `ii rsyslog 8.2504.0-1+deb13u2 amd64`.
- Mensaje de rsyslog: `imuxsock: Acquired UNIX socket '/run/systemd/journal/syslog' (fd 3) from systemd.` Muestra que recibió un socket de systemd; por sí solo no demuestra que el nuevo mensaje de prueba esté en `/var/log/syslog`.
- `systemd-journald.service`: `loaded`, `static`, `active (running)` desde las 00:42:59 CEST. PID 415, 16,7 MB de memoria. La condición `static` no significa servicio desactivado.
- Journal persistente observado en `/var/log/journal/db1c24869f59488fb51181a0eb0bcae8` (en ese momento 99,7 MB), con traslado desde el journal temporal `/run/log/journal/...`.
- Existe `/var/log/syslog`: `-rw-r----- 1 root adm 4754713 oct 10 15:17 /var/log/syslog`. Permisos 0640; fichero con unos 4,75 MB. Esto prueba la existencia del registro tradicional, no todavía el resultado de la prueba etiquetada.
- Mensaje `Notice: journal has been rotated since unit was started, output may be incomplete.`: advertencia sobre posible salida incompleta del estado, no evidencia de caída del servicio.

**Conclusión del paso 1:** ambos servicios están operativos y el fichero `/var/log/syslog` existe. No es necesario instalar o reiniciar servicios solo para cumplir esta comprobación.

### Paso 2 — Prueba controlada de registro local (ejecutado y comprobado)

```bash
logger -t LSI-P1-M -p user.notice "Prueba de registro local del apartado m"
grep 'LSI-P1-M' /var/log/syslog | tail -n 5
journalctl -t LSI-P1-M -n 5 --no-pager
```

`logger` remite un mensaje etiquetado con *facility* `user` y nivel `notice`; las dos consultas siguientes buscan ese evento en `/var/log/syslog` y en el journal.

**Salidas reales aportadas por el alumno (10/10/2026):**

`grep 'LSI-P1-M' /var/log/syslog | tail -n 5`:

```text
2026-10-10T15:23:17.219033+02:00 debian LSI-P1-M: Prueba de registro local del apartado m
```

`journalctl -t LSI-P1-M -n 5 --no-pager`:

```text
oct 10 15:23:17 debian LSI-P1-M[1267]: Prueba de registro local del apartado m
```

**Interpretación del resultado:** ambos mecanismos permiten recuperar el mismo mensaje a las 15:23:17, en el mismo host (`debian`), con la etiqueta `LSI-P1-M` y el texto exacto del evento. Rsyslog aparece escribiéndolo en `/var/log/syslog`; journald lo devuelve mediante `journalctl`. El PID `1267` en la segunda salida identifica el proceso `logger` emisor según el journal. No se cambiaron reglas ni servicios para conseguirlo.

**Conclusión del apartado m:** queda comprobado el sistema local de logs con `rsyslog` y con `journald`; por tanto, el requisito expresamente pedido en el apartado m de la primera parte se considera completado. Esto no acredita la configuración de rsyslog *entre máquinas*, que corresponde a la segunda parte.

### Paso 3 — Consultas complementarias de journald (opcionales, aún no ejecutadas)

```bash
journalctl -b -n 15 --no-pager
journalctl -b -p err --no-pager
journalctl --disk-usage
```

**Explicación para la defensa:** `systemd-journald` conserva eventos estructurados consultables con `journalctl`; `rsyslog` procesa mensajes y puede escribirlos en archivos de texto o reenviarlos. Es posible utilizar ambos simultáneamente. Esta parte evalúa logs **locales**; el reenvío entre servidor y cliente es otro ejercicio de la segunda parte.

**Cambios en la VM realizados por el asistente:** ninguno.  
**Cambios en GitHub:** ninguno.  
**Siguiente acción:** ninguna imprescindible para el apartado m. Como ampliación opcional, revisar las consultas complementarias del journal y explicar la diferencia entre persistencia y logs en RAM.


## 8. Sesión del 10/10/2026 — Apartado k: monitorización en tiempo real

**Requisito literal del enunciado:** «Nuestro sistema es el encargado de gestionar la CPU, memoria, red, etc., como soporte a los datos y procesos. Monitorice en “tiempo real” la información relevante de los procesos del sistema y los recursos consumidos. Monitorice en “tiempo real” las conexiones de su sistema.»

**Estado:** COMPLETADO el 10/10/2026 — procesos/recursos monitorizados con `top`; conexiones monitorizadas con `watch` y `ss`; evidencias aportadas por el alumno.

**Objetivo:** observar de forma dinámica los procesos y los recursos consumidos (CPU y memoria, opcionalmente E/S/red), así como los sockets y conexiones de red con actualizaciones periódicas. Se trabajará desde root (`su -`) como en el apartado m.

### Paso 1 — Monitorizar procesos y CPU/memoria (ejecutado y analizado)

```bash
top
```

Interacción durante la ejecución: `P` ordena por uso de CPU; `M`, por uso de memoria; `1` alterna la vista por CPU lógica; `q` sale. Revisar `load average`, porcentaje de CPU, RAM/swap, PID, usuario, estado y `%CPU`/`%MEM` de los procesos. 

**Para generar un resultado pegable en el chat después de usar `top`:**

```bash
top -b -n 1 | head -n 25
```

`-b` activa modo por lotes y `-n 1` toma una única muestra para registrar una instantánea. Esta instantánea se usará como evidencia de la monitorización dinámica realizada con `top`, no como sustituto de verla en tiempo real.

### Paso 2 — Muestras periódicas de recursos (propuesto)

```bash
vmstat 1 5
free -h
```

`vmstat 1 5` obtiene cinco muestras en intervalos de un segundo (la primera puede resumir estadísticas desde el arranque). `free -h` ofrece la memoria y swap del instante.

### Paso 3 — Monitorizar conexiones de red (propuesto)

```bash
watch -n 2 'ss -tunap'
```

`watch` actualiza la consulta cada dos segundos hasta pulsar `Ctrl+C`. `ss -tunap` muestra sockets TCP/UDP (incluyendo escucha y conexiones), con direcciones/puertos numéricos y procesos cuando sea posible. No confundir conexiones establecidas con puertos en escucha.

**Para registrar una instantánea pegable en la bitácora:**

```bash
ss -tunap
```

**Cambios previstos en la VM:** ninguno; solo comandos de consulta.
**Cambios en GitHub:** ninguno.
**Siguiente acción (ya realizada):** el alumno ejecutó `free -h` y `watch -n 2 'ss -tunap'` y compartió la captura de su salida. Se registra a continuación.


### Resultados reales del paso 1 — `top` (10/10/2026, 15:28:39)

**Comando ejecutado por el alumno:** `top` (monitor interactivo). La salida textual se compartió en el chat.

**Cabecera observada:**

```text
top - 15:28:39 up 14:45,  2 users,  load average: 0,08, 0,02, 0,01
Tareas: 187 total,   1 ejecutar,  186 hibernar,    0 detener,    0 zombie
%Cpu(s):  0,0 us,  1,0 sy,  0,0 ni, 99,0 id,  0,0 wa,  0,0 hi,  0,0 si,  0,0 st
MiB Mem :   1469,9 total,   1106,7 libre,    283,9 usado,    214,8 búf/caché
MiB Intercambio:   1534,0 total,   1534,0 libre,      0,0 usado.   1186,0 dispon
```

**Interpretación para la defensa:**
- `up 14:45`: 14 h y 45 min de tiempo encendida; `2 users`: sesiones activas, no necesariamente dos personas.
- `load average` 0,08/0,02/0,01: carga media a 1, 5 y 15 minutos, respectivamente; carga muy baja.
- 187 tareas, 1 ejecutándose, 186 durmiendo, ninguna detenida ni zombie.
- CPU: 99 % `id` (inactiva), 1 % `sy` (núcleo); `us`=usuario, `ni`=prioridad nice, `wa`=espera E/S, `hi`/`si`=interrupciones hardware/software, `st`=tiempo cedido al hipervisor de la VM.
- RAM reportada: total 1469,9 MiB, libre 1106,7 MiB, usada 283,9 MiB, buffers/caché 214,8 MiB, disponible estimada 1186,0 MiB. **Estas cifras se tomaron literalmente de la salida**; se obtuvo después la muestra de `free -h`, que confirma sus órdenes de magnitud. No debe sumarse sin más libre, usado y búf/caché para calcular la memoria real utilizable; para ello sirve «disponible».
- Swap: 1534 MiB totales, 0 usados; no se observa presión que obligue a intercambiar páginas en ese instante.

**Columnas de procesos:** `PID` identificador, `USUARIO` propietario, `PR` prioridad de planificación, `NI` ajuste nice, `VIRT` memoria virtual, `RES` memoria física residente, `SHR` memoria compartible, `S` estado (`R` ejecutándose, `S` durmiendo, `I` hilo del núcleo inactivo), `%CPU` y `%MEM` porcentajes de uso, `HORA+` CPU acumulada, `ORDEN` comando/proceso.

**Filas destacadas de la salida aportada:**

```text
 PID USUARIO PR NI  VIRT   RES   SHR S %CPU %MEM    HORA+ ORDEN
  11 root   20  0     0     0     0 I  1,7  0,0 14:43.16 kworker+
1272 root   20  0 10664  6080  3848 R  0,3  0,4  0:00.14 top
   1 root   20  0 23892 14408 10524 S  0,0  1,0  0:07.06 systemd
```

`kworker` es un trabajador del kernel; `top` es el propio monitor; `systemd` con PID 1 es el gestor de inicio. `14:43.16` en `HORA+` es tiempo de CPU acumulado (aprox. 14 min 43 s), **no 14 horas de ejecución continua**. Un sufijo `+` en el nombre indica truncamiento en el ancho de columna de la salida.

**Estado de esta parte:** monitorización interactiva de CPU, memoria y procesos realizada y analizada; después se verificaron RAM y conexiones, como se recoge a continuación.


### Resultados reales del paso 2 — `free -h` (10/10/2026)

**Comando ejecutado:**

```bash
free -h
```

**Salida aportada:**

```text
               total       usado       libre  compartido   búf/caché  disponible
Mem:           1,4Gi       283Mi       1,1Gi       1,1Mi       215Mi       1,2Gi
Inter:         1,5Gi          0B       1,5Gi
```

**Interpretación:** alrededor de 1,4 GiB de RAM, 283 MiB usados según `free`, aproximadamente 1,2 GiB disponibles para nuevas cargas; swap de 1,5 GiB sin uso. En esta instantánea no se observan indicios de presión de memoria. `disponible` es la estimación más útil de memoria utilizable sin recurrir al intercambio.

### Resultados reales del paso 3 — conexiones de red en tiempo real (10/10/2026, 15:59:31)

**Comando ejecutado:**

```bash
watch -n 2 'ss -tunap'
```

**Captura de la actualización observada:**

```text
Cada 2,0s: ss -tunap                            debian: Sat Oct 10 15:59:31 2026

Netid State  Recv-Q Send-Q  Local Address:Port      Peer Address:Port     Process
tcp   LISTEN 0      128     0.0.0.0:22               0.0.0.0:*             users:(("sshd",pid=631,fd=6))
tcp   LISTEN 0      128     127.0.0.1:6010           0.0.0.0:*             users:(("sshd-session",pid=1218,fd=11))
tcp   ESTAB  0      0       IP_VM_ENS33:22           IP_CLIENTE_VPN:63418   users:(("sshd-session",pid=1218,fd=7),("sshd-session",pid=1167,fd=7))
tcp   ESTAB  0      0       IP_VM_ENS33:22           IP_CLIENTE_VPN:63441   users:(("sshd-session",pid=1219,fd=7),("sshd-session",pid=1172,fd=7))
tcp   ESTAB  0      0       IP_VM_ENS33:39880        149.154.166.110:443  users:(("python3",pid=582,fd=4))
tcp   LISTEN 0      128     [::1]:6010               [::]:*               users:(("sshd-session",pid=1218,fd=10))
tcp   LISTEN 0      128     [::]:22                   [::]:*               users:(("sshd",pid=631,fd=7))
```

**Interpretación para la defensa:**
- `watch -n 2` ejecuta y refresca cada dos segundos el listado; salir con `Ctrl+C`.
- `ss -tunap`: `-t` TCP, `-u` UDP, `-n` direcciones/puertos numéricos, `-a` sockets tanto activos como en escucha, `-p` procesos asociados cuando se conocen.
- `LISTEN` indica socket preparado para aceptar conexiones. El servicio `sshd` (PID 631) aparece escuchando en puerto 22 de todas las interfaces IPv4 (`0.0.0.0`) e IPv6 (`[::]`). Esto no prueba accesibilidad desde cualquier origen: también intervienen rutas y filtrado.
- `ESTAB`/`ESTABLISHED` indica conexión TCP establecida. Hay dos conexiones SSH hacia `IP_VM_ENS33:22` desde `IP_CLIENTE_VPN`, con puertos de cliente efímeros distintos (`63418` y `63441`). No se ha demostrado qué equipo o persona ocupa esa IP.
- `127.0.0.1:6010` y `[::1]:6010` son sockets locales en loopback de `sshd-session`, compatibles con reenvío X11. No son puertos expuestos en todas las interfaces.
- `python3` (PID 582) mantiene una conexión saliente a `149.154.166.110:443` desde el puerto local `39880`. Es compatible con el bot de Telegram documentado, pero no se ha verificado la identidad del proceso ni el destino concreto; no afirmarlo como hecho en la defensa sin comprobarlo.
- `Recv-Q`/`Send-Q` aparecen en cero para las conexiones establecidas de la captura; no indica por sí solo ausencia de tráfico en otros instantes.
- La muestra es una instantánea dentro de un monitor periódico; nuevas conexiones pueden aparecer o desaparecer en actualizaciones posteriores.

**Estado final del apartado k:** **COMPLETADO**. Se han observado procesos y recursos en tiempo real con `top`, se ha consultado RAM/swap con `free -h` y se han monitorizado sockets/conexiones con `watch` + `ss`. No se ha cambiado ninguna configuración ni se han instalado paquetes. Esta evidencia será útil también al preparar el apartado j, que todavía no se marca como cerrado en esta bitácora.

**Cambios en la VM:** ninguno (solo consultas).  
**Cambios en GitHub:** ninguno.  


## 10/10/2026 — Apartado l: inicio (pendiente)

**Objetivo del enunciado:** configurar control de acceso SSH por TCP Wrappers (`/etc/hosts.allow`, `/etc/hosts.deny`), permitir IP autorizadas y denegar las demás; identificar la política, distinguirlo de un firewall, identificar servicios compatibles y registrar los intentos denegados en `/var/log/denegados` con host/IP, fecha y hora.

**Precaución:** hay sesiones SSH activas y el README indica que la consola de recuperación la gestionan los profesores. No alterar reglas de acceso hasta identificar la IP autorizada y verificar compatibilidad de `sshd` con `libwrap`.

**Dato externo contrastado:** el paquete `openssh-server` de Debian 13 (Trixie) declara dependencia de `libwrap0` y su página de manual contempla los archivos `hosts.allow` y `hosts.deny`. Debe verificarse el binario realmente instalado en la VM antes de afirmar compatibilidad.

**Estado:** planificación e inspección inicial propuestas; todavía no se han ejecutado comandos del apartado l ni cambiado configuración.

**Consultas propuestas:**
```bash
ldd /usr/sbin/sshd | grep -i libwrap
dpkg -l openssh-server libwrap0
cat /etc/hosts.allow
cat /etc/hosts.deny
ss -tnp state established
```

**Pendiente:** estudiar resultados, diseñar regla de permiso y denegación sin bloquear el acceso del alumno, probarla desde IP autorizada y no autorizada, y configurar/verificar registro en `/var/log/denegados`.


### 10/10/2026 — Apartado l: primeras comprobaciones reales

**Comandos ejecutados en la VM:**

```bash
ldd /usr/sbin/sshd | grep -i libwrap
ldd /usr/sbin/sshd | grep -i libwrap
cat /etc/hosts.allow
cat /etc/hosts.deny
```

**Resultados observados:**
- El comando `ldd /usr/sbin/sshd | grep -i libwrap` no produjo salida en dos intentos.
- `/etc/hosts.allow` contiene exclusivamente los comentarios de ejemplo originales; sin reglas activas.
- `/etc/hosts.deny` también contiene exclusivamente comentarios originales. La línea `# ALL: PARANOID` está comentada y no se aplica.
- No se ha recibido todavía el resultado de `dpkg -l openssh-server libwrap0`.
- No se han modificado ficheros ni servicios.

**Investigación adicional (fuente externa):**
- El paquete oficial Debian 13 `openssh-server` tiene una dependencia de `libwrap0`.
- El parche Debian `restore-tcp-wrappers.patch` de OpenSSH 10.0 añade las comprobaciones de TCP Wrappers en `sshd-session.c`, no en el binario principal `sshd`; por ello la prueba inicial de `ldd /usr/sbin/sshd` no basta para descartar compatibilidad.
- Fuentes:
  - https://packages.debian.org/trixie/openssh-server
  - https://sources.debian.org/patches/openssh/1:10.0p1-7+deb13u4/restore-tcp-wrappers.patch/

**Siguiente paso seguro (solo lectura):**

```bash
ldd /usr/lib/openssh/sshd-session | grep -i libwrap
dpkg -l openssh-server libwrap0
ss -tnp state established
```

**Precaución:** SSH está siendo utilizado de forma remota y la recuperación de la VM depende de los profesores; no aplicar denegaciones globales sin verificar primero la compatibilidad y las direcciones IP que deben seguir autorizadas.

**Estado:** apartado l EN CURSO. Ninguna regla aplicada; ningún acceso denegado ni registrado todavía.


### 10/10/2026 — Apartado l: compatibilidad y conexiones verificadas

**Comprobado con salidas reales facilitadas por el alumno:**

```bash
ldd /usr/sbin/sshd | grep -i libwrap
```

Sin salida, por segunda vez.

```bash
ldd /usr/lib/openssh/sshd-session | grep -i libwrap
```

Resultado:

```text
libwrap.so.0 => /lib/x86_64-linux-gnu/libwrap.so.0 (0x00007f5cea011000)
```

Paquetes comprobados con `dpkg -l openssh-server libwrap0`:

```text
ii  libwrap0:amd64 7.6.q-36            amd64
ii  openssh-server 1:10.0p1-7+deb13u4 amd64
```

Conexiones activas comprobadas mediante `ss -tnp state established`:

```text
IP_VM_ENS33:22    IP_CLIENTE_VPN:63418       sshd-session
IP_VM_ENS33:50728 149.154.166.110:443     python3, pid=582
IP_VM_ENS33:22    IP_CLIENTE_VPN:63441       sshd-session
```

**Interpretación:**
- `sshd-session` enlaza dinámicamente con `libwrap.so.0`; a diferencia del `sshd` principal, es el binario pertinente para verificar la integración con TCP Wrappers en esta versión de OpenSSH para Debian.
- El nombre del servicio que solicita la biblioteca en el código del parche de Debian es `sshd`, aunque el ejecutable se llame `sshd-session`. Las reglas de acceso se redactarán para `sshd`.
- Las dos conexiones SSH observadas proceden de `IP_CLIENTE_VPN` (puertos origen distintos). No se ha confirmado si esa IP es estable o asignada dinámicamente por la VPN; no crear una política de denegación antes de planificar recuperación y verificar la IP autorizada.
- La conexión saliente de Python a 149.154.166.110:443 es compatible con el bot de Telegram documentado, pero no se ha confirmado el comando del PID 582.

**Comprobación externa:**
- https://sources.debian.org/patches/openssh/1%3A10.0p1-7~bpo12%2B1/restore-tcp-wrappers.patch/ (bloque de código `RQ_DAEMON, "sshd"`).
- https://sources.debian.org/src/tcp-wrappers/7.6.q-36/hosts_options.5/ (opciones `spawn`, `deny`).
- https://manpages.debian.org/testing/libwrap0/hosts.deny.5.en.html (precedencia de reglas).

**Estado:** compatibilidad verificada, sin modificación todavía de `hosts.allow` ni `hosts.deny`; apartado l continúa **EN CURSO**.


### 10/10/2026, 16:33 — Interpretación de sesiones SSH en el apartado l

**Comprobaciones reales del alumno:**

```bash
who
```

Salida:

```text
lsi      sshd pts/0   2026-10-10 14:53 (IP_CLIENTE_VPN)
lsi      sshd pts/0   2026-10-10 14:53 (IP_CLIENTE_VPN)
```

```bash
w
```

Salida:

```text
16:33:15 up 15:50, 2 users, load average: 0,00, 0,00, 0,00
USUARIO  TTY      DESDE            LOGIN@   IDLE   JCPU   PCPU  WHAT
lsi               IP_CLIENTE_VPN     14:53           0.00s  0.03s sshd-session: l
lsi      pts/0    IP_CLIENTE_VPN     14:53    3.00s  0.10s  0.05s sshd-session: l
```

**Interpretación para la defensa:**
- Dos sesiones registradas para el mismo usuario `lsi`, ambas desde `IP_CLIENTE_VPN` con hora de inicio 14:53; `2 users` no implica dos personas.
- `w` muestra una sesión asociada a `pts/0` (pseudoterminal) y otra sin TTY visible. Puede deberse a una conexión no interactiva, un túnel u otra funcionalidad de SSH, pero su propósito exacto no se ha verificado.
- Ambas conexiones TCP a `IP_VM_ENS33:22` utilizan puertos remotos diferentes (`63418`, `63441`) y constituyen conexiones distintas.
- El formato duplicado de `who` no permite atribuir más detalles; verificar procesos de sesiones si es necesario.

**Comprobación adicional propuesta (solo lectura):**

```bash
ps -o pid,ppid,tty,stat,args -p 1167,1172,1218,1219
```

Estos PID fueron observados en la captura de `ss` anterior y podrían haber cambiado desde entonces.

**Estado:** investigación de las sesiones completada parcialmente; apartado l sigue EN CURSO, sin cambios en reglas TCP Wrappers ni registros de denegación.


### 10/10/2026 — Inspección de procesos SSH con ps

**Comando ejecutado:**
```bash
ps -o pid,ppid,tty,stat,args -p 1167,1172,1218,1219
```

**Salida obtenida:**
```text
    PID    PPID TT       STAT COMMAND
   1167     631 ?        Ss   sshd-session: lsi [priv]
   1218    1167 ?        S    sshd-session: lsi@pts/0
```

**Interpretación:**
- El proceso `1167` (padre `631`) es la parte privilegiada de la sesión SSH (`[priv]`).
- `1218`, hijo de `1167`, está asociado a la sesión interactiva `lsi@pts/0`.
- Estos **dos procesos** forman parte de una misma sesión SSH, no prueban por sí solos dos conexiones diferentes.
- Los procesos `1172` y `1219` que figuraban en la captura anterior de `ss` ya no aparecen en esta consulta; es compatible con el cierre de la segunda conexión, aunque conviene repetir `ss -tnp state established` y `w` para confirmar el estado actual.
- No se han aplicado aún reglas de filtrado TCP Wrappers ni se ha verificado el fichero `/var/log/denegados`.

**Siguiente comprobación propuesta (solo lectura):**
```bash
ss -tnp state established
w
```

**Estado del apartado l:** en curso.


### 10/10/2026 — Segunda conexión SSH cerrada (comprobado)

**Comando:**
```bash
ss -tnp state established
```

**Salida facilitada:**
```text
Recv-Q Send-Q Local Address:Port Peer Address:Port Process
0      212    IP_VM_ENS33:22    IP_CLIENTE_VPN:63418 users:(("sshd-session",pid=1218,fd=7),("sshd-session",pid=1167,fd=7))
0      0      IP_VM_ENS33:48400 149.154.166.110:443 users:(("python3",pid=582,fd=4))
```

**Conclusión:** solamente queda una conexión SSH establecida a `IP_VM_ENS33:22`, originada desde `IP_CLIENTE_VPN:63418`. La segunda conexión antes observada con puerto de origen `63441` ya no aparece. El proceso Python mantiene una conexión TLS/HTTPS al puerto remoto 443; su identificación como bot de Telegram sigue siendo probable, no confirmada por inspección del comando.

**Precaución para el apartado l:** la única sesión SSH observada no debe ponerse en riesgo aplicando de inmediato una denegación general. Aún no se han configurado ni probado las reglas `/etc/hosts.allow`, `/etc/hosts.deny` ni `/var/log/denegados`. Antes, comprobar respaldo de archivos, disponibilidad de herramientas de prueba (`tcpdmatch` y `tcpdchk`) y estabilidad de la IP del cliente.

**Estado:** apartado l EN CURSO; inspección de conexiones terminada.


### 10/10/2026 — Apartado l: respaldo y acceso por VPN / Wi-Fi universitario

**Comandos ejecutados:**
```bash
mkdir -p /root/lsi-tcpwrappers-respaldo
cp -a /etc/hosts.allow /etc/hosts.deny /root/lsi-tcpwrappers-respaldo/
command -v tcpdmatch
command -v tcpdchk
```

**Resultados aportados:** la creación del directorio y las copias terminaron sin mensajes de error. `command -v tcpdmatch` y `command -v tcpdchk` no devolvieron rutas; es probable que no esté instalado el paquete `tcpd`, pero se verificará mediante `dpkg -l` o `apt-cache policy`.

**Nuevo dato de acceso:** el alumno se conecta a la VM mediante VPN de la UDC y también desde la red Wi-Fi universitaria cuando está en el campus. La IP de origen observada por SSH desde VPN es `IP_CLIENTE_VPN`; la IP/rango desde Wi-Fi no se ha identificado y puede diferir. No asumir que `IP_CLIENTE_VPN` es fija.

**Riesgo:** una regla de denegación por defecto con una lista de permisos que solamente incluya la IP de VPN actual podría impedir nuevas conexiones desde Wi-Fi o tras un cambio de IP de VPN. La sesión SSH existente podría continuar, pero no constituye una garantía de recuperación.

**Próximo paso:** comprobar si `tcpd` está instalado; instalarlo desde los repositorios de Debian si procede; utilizar `tcpdmatch`/`tcpdchk` antes de cualquier cambio restrictivo. Determinar las redes autorizadas y prever un mecanismo de reversión.

**Referencia externa verificada:** paquete `tcpd` disponible en Debian 13: https://packages.debian.org/trixie/tcpd

**Estado:** en curso. Sin reglas aplicadas ni configuración de `/var/log/denegados`.


### 10/10/2026 — Apartado l: instalación comprobada de tcpd

**Resultados reales aportados por el alumno:**

Comando:
```bash
apt-cache policy tcpd
```

Salida significativa:
```text
tcpd:
  Instalados: (ninguno)
  Candidato: 7.6.q-36
  500 http://deb.debian.org/debian trixie/main amd64 Packages
```

Después ejecutó:
```bash
apt install tcpd
```
Resultado: instalación completada (`tcpd 7.6.q-36`), sin actualización ni eliminación de otros paquetes.

Comprobación:
```bash
command -v tcpdmatch
command -v tcpdchk
```

Salida:
```text
/usr/sbin/tcpdmatch
/usr/sbin/tcpdchk
```

**Interpretación:** herramientas TCP Wrappers instaladas y accesibles. Esto no implica que se hayan aplicado reglas, denegado conexiones ni comprobado todavía el fichero `/var/log/denegados`.

**Siguiente paso propuesto, no ejecutado todavía:** simulación en un directorio separado, sin modificar `/etc/hosts.allow` ni `/etc/hosts.deny`.

```bash
mkdir -p /root/lsi-tcpwrappers-prueba
cd /root/lsi-tcpwrappers-prueba
printf 'sshd: IP_CLIENTE_VPN\n' > hosts.allow
printf 'sshd: ALL\n' > hosts.deny
tcpdchk -d -v
tcpdmatch -d sshd IP_CLIENTE_VPN
tcpdmatch -d sshd 192.0.2.10
```

**Resultados esperados, aún no comprobados:** permitir `IP_CLIENTE_VPN` y denegar `192.0.2.10`, dirección de documentación. Con `-d`, las herramientas leen los archivos del directorio actual. Si `tcpdchk` avisa de que `sshd` no pertenece a inetd, revisar el aviso considerando que SSH se gestiona mediante systemd, y que ya se confirmó el enlace de `sshd-session` con libwrap.

**Advertencia operativa:** aún falta determinar los rangos o IP autorizados desde Wi-Fi UDC y VPN para evitar bloquear accesos remotos. No aplicar todavía una denegación global real. La configuración de registros rechazados en `/var/log/denegados` sigue pendiente.

**Fuentes:** manual `hosts_access(5)` y `tcpdmatch(8)` Debian:
- https://sources.debian.org/src/tcp-wrappers/7.6.q-36/hosts_access.5
- https://manpages.debian.org/testing/tcpd/tcpdmatch.8.en.html

**Estado del apartado l:** EN CURSO.


### 10/10/2026 — Error al ejecutar tcpdchk: libwrap.so.0 file too short

**Comando ejecutado en la carpeta de simulación:**
```bash
tcpdchk -d -v
```

**Error real:**
```text
tcpdchk: error while loading shared libraries: /lib/x86_64-linux-gnu/libwrap.so.0: file too short
```

**Diagnóstico provisional:** fallo del cargador dinámico al leer `libwrap.so.0`, anterior a cualquier análisis de reglas TCP Wrappers. El archivo o el destino del enlace simbólico podría estar truncado, vacío o dañado; aún no está confirmada la causa. `sshd-session` utiliza esa misma biblioteca, por lo que nuevas sesiones SSH podrían fallar. Evitar cerrar la sesión actual, reiniciar SSH/VM o instalar políticas restrictivas hasta verificar y reparar. La configuración real de `/etc/hosts.allow` y `/etc/hosts.deny` no se ha modificado.

**Dato a tener en cuenta:** la instalación anterior de `tcpd` mostró aproximadamente 9.124 MB de espacio libre en el volumen destino; es necesario revisar uso de disco e inodos para descartar falta de espacio, sin presuponer que sea la causa.

**Consultas diagnósticas propuestas, no ejecutadas todavía:**
```bash
ls -l /lib/x86_64-linux-gnu/libwrap.so.0*
readlink -f /lib/x86_64-linux-gnu/libwrap.so.0
file -L /lib/x86_64-linux-gnu/libwrap.so.0
dpkg -V libwrap0
df -h / /usr /var
df -i /
```

**Criterio:** comprobar el tamaño y tipo del archivo y la integridad del paquete `libwrap0` antes de considerar `apt install --reinstall libwrap0`. El manual de `dpkg` documenta la comprobación de integridad con `-V`: https://manpages.debian.org/testing/dpkg/dpkg.1.en.html .

**Estado:** apartado l BLOQUEADO temporalmente por incidencia de biblioteca compartida. Todavía no hay validación de las reglas ni registro en `/var/log/denegados`.


### 10/10/2026 — Confirmación del fallo de integridad en libwrap0

**Salida real de la VM:**

```bash
ls -l /lib/x86_64-linux-gnu/libwrap.so.0*
```
```text
lrwxrwxrwx 1 root root 16 feb 21  2025 /lib/x86_64-linux-gnu/libwrap.so.0 -> libwrap.so.0.7.6
-rw-r--r-- 1 root root  0 oct 10 16:29 /lib/x86_64-linux-gnu/libwrap.so.0.7.6
```

```bash
readlink -f /lib/x86_64-linux-gnu/libwrap.so.0
file -L /lib/x86_64-linux-gnu/libwrap.so.0
dpkg -V libwrap0
```
```text
/usr/lib/x86_64-linux-gnu/libwrap.so.0.7.6
/lib/x86_64-linux-gnu/libwrap.so.0: empty
??5??????   /usr/lib/x86_64-linux-gnu/libwrap.so.0.7.6
```

**Conclusión verificada:** el archivo real de `libwrap0` tiene tamaño cero y `dpkg -V` detecta desacuerdo de checksum (indicador `5`). Esta es la causa inmediata de `file too short` al ejecutar `tcpdchk`. **No se conoce la causa original del truncamiento.** La fecha de modificación observada es 10/10/2026 a las 16:29; no demuestra qué acción lo produjo.

**Comprobación del almacenamiento:**
```text
/dev/sda1 13G total, 3,1G usados, 8,5G disponibles, 27% uso
Inodos: 819200 total, 74077 usados, 745123 libres, 10% uso
```
No se observa falta de espacio ni agotamiento de inodos. Se corrige un error interpretativo anterior en la conversación: `9.124 MB available` en salida de APT en español eran aproximadamente **9.124 MB** (nueve mil ciento veinticuatro), no nueve MB.

**Acción de reparación propuesta (todavía NO ejecutada):**
```bash
apt install --reinstall libwrap0
```
La documentación oficial Debian recomienda `apt --reinstall install` para restaurar archivos de un paquete alterados o eliminados:
https://www.debian.org/doc/manuals/debian-handbook/sect.apt-get.es.html

**Comprobaciones posteriores propuestas:**
```bash
ls -lh /usr/lib/x86_64-linux-gnu/libwrap.so.0.7.6
file -L /lib/x86_64-linux-gnu/libwrap.so.0
dpkg -V libwrap0
tcpdchk -d -v
tcpdmatch -d sshd IP_CLIENTE_VPN
tcpdmatch -d sshd 192.0.2.10
```
Mantener abierta la sesión SSH actual, no reiniciar VM ni `sshd`, y detenerse si APT propone eliminar otros paquetes. La simulación de reglas debe ejecutarse desde `/root/lsi-tcpwrappers-prueba` y las reglas reales aún no se han aplicado. `/var/log/denegados` sigue pendiente.

**Estado:** incidente identificado; reparación y validaciones pendientes; apartado l EN CURSO.

### 10/10/2026 — Apartado l: reparación de libwrap0 verificada

**Comprobaciones reales aportadas después de la reparación:**

```bash
ls -lh /usr/lib/x86_64-linux-gnu/libwrap.so.0.7.6
```
```text
-rw-r--r-- 1 root root 47K feb 21  2025 /usr/lib/x86_64-linux-gnu/libwrap.so.0.7.6
```

```bash
file -L /lib/x86_64-linux-gnu/libwrap.so.0
```
```text
/lib/x86_64-linux-gnu/libwrap.so.0: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, BuildID[sha1]=192b2106b79abcc3c766f55d8323680eeb522895, stripped
```

```bash
dpkg -V libwrap0
```
No produjo salida.

**Interpretación:** el archivo ha pasado de 0 bytes a 47 KB, es una biblioteca ELF válida y `dpkg -V` no detecta discrepancias de integridad. La avería observada se considera reparada. En este turno no se proporcionó la salida de `apt install --reinstall libwrap0`, por lo que se documenta la verificación del estado final, no el detalle de la ejecución de APT.

**Siguiente fase propuesta, todavía pendiente:** comprobar los contenidos de `hosts.allow` y `hosts.deny` dentro de `/root/lsi-tcpwrappers-prueba` y ejecutar `tcpdchk -d -v` y `tcpdmatch -d sshd` con la IP IP_CLIENTE_VPN y la IP de prueba 192.0.2.10. No se deben aplicar reglas reales de denegación hasta comprobar las IP/redes de acceso por VPN y Wi-Fi UDC y planear recuperación. El registro en `/var/log/denegados` sigue pendiente.

**Estado del apartado l:** EN CURSO; biblioteca reparada y comprobada; reglas simuladas todavía sin verificar.


### 10/10/2026 — Apartado l: reglas simuladas correctamente

**Verificación de los archivos de simulación** en `/root/lsi-tcpwrappers-prueba`:
```bash
cat hosts.allow hosts.deny
```
```text
sshd: IP_CLIENTE_VPN
sshd: ALL
```

**Validación sintáctica e interpretación:**
```bash
tcpdchk -d -v
```
```text
Using network configuration file: (null)

>>> Rule hosts.allow line 1:
daemons:  sshd
clients:  IP_CLIENTE_VPN
access:   granted

>>> Rule hosts.deny line 1:
daemons:  sshd
clients:  ALL
access:   denied
```

**Simulación de conexión autorizada:**
```bash
tcpdmatch -d sshd IP_CLIENTE_VPN
```
```text
client:   address  IP_CLIENTE_VPN
server:   process  sshd
access:   granted
```

**Simulación de conexión no autorizada:**
```bash
tcpdmatch -d sshd 192.0.2.10
```
```text
client:   address  192.0.2.10
server:   process  sshd
access:   denied
```

**Interpretación:** la simulación de la política *denegar por defecto SSH salvo IP expresamente autorizada* es coherente y no provoca errores en `tcpdchk`. TCP Wrappers evalúa `hosts.allow` antes que `hosts.deny`. Esto **no verifica aún un rechazo real** de nuevas conexiones TCP, porque `-d` lee los archivos del directorio de prueba y no los archivos activos del servidor. El bloqueo `sshd: ALL` sería específico de SSH; no afecta automáticamente a todos los servicios.

**Condiciones de seguridad:** el alumno usa la VPN y la Wi-Fi de la UDC, por lo que hace falta identificar rangos legítimos de origen y disponer de una reversión antes de aplicar denegación real. Si cambia la IP asignada por la VPN, la regla para la dirección observada podría dejarlo fuera.

**Pendientes del apartado l:**
1. Comprobar reglas/inclusiones activas de rsyslog y preparar la creación segura del registro `/var/log/denegados` con fecha/hora e IP/host.
2. Determinar el conjunto de direcciones autorizadas para VPN y Wi-Fi.
3. Aplicar el filtrado real con un mecanismo de reversión, validar desde una conexión autorizada y realizar una prueba de denegación real sin perder el acceso.
4. Inventariar servicios que realmente utilizan la biblioteca libwrap, explicar la diferencia entre wrappers y firewall.
5. No añadir comentarios nuevos a archivos de configuración según el enunciado.

**Fuente técnica:** documentación Debian `hosts_options(5)` sobre `spawn`, `hosts_access(5)` sobre sustitución `%a`, manual `rsyslogd(8)` para validar configuración.
https://manpages.debian.org/trixie/libwrap0/hosts_options.5.en.html

**Estado:** reglas simuladas COMPROBADAS; apartado l EN CURSO, no completado.


### 10/10/2026 — Apartado l: inspección de rsyslog y propuesta de registro

**Comprobado con la salida del alumno:**

`/etc/rsyslog.conf` contiene:

```text
module(load="imuxsock")
module(load="imklog")
$FileOwner root
$FileGroup adm
$FileCreateMode 0640
$DirCreateMode 0755
$Umask 0022
$WorkDirectory /var/spool/rsyslog
$IncludeConfig /etc/rsyslog.d/*.conf
*.*;auth,authpriv.none          -/var/log/syslog
auth,authpriv.*                 /var/log/auth.log
cron.*                          -/var/log/cron.log
kern.*                          -/var/log/kern.log
mail.*                          -/var/log/mail.log
user.*                          -/var/log/user.log
*.emerg                         :omusrmsg:*
```

Los comentarios preexistentes se mantienen en el fichero original. El directorio `/etc/rsyslog.d/` está vacío (`ls -la` solo muestra `.` y `..`). No hay todavía ninguna regla de redirección hacia `/var/log/denegados`.

**Interpretación:** `imuxsock` está habilitado para mensajes locales, y la inclusión de `/etc/rsyslog.d/*.conf` permite añadir reglas nuevas sin modificar el archivo principal. `auth` y `authpriv` registran en `/var/log/auth.log`, mientras que `/var/log/syslog` excluye esas facilities. El orden de evaluación de rsyslog sitúa las nuevas reglas incluidas antes de las reglas generales posteriores.

**Siguiente paso propuesto y no ejecutado:** crear `/etc/rsyslog.d/30-lsi-denegados.conf`, sin comentarios añadidos, para recoger únicamente mensajes con una etiqueta específica `LSI_TCP_DENEGADO`:

```text
if ($programname == "LSI_TCP_DENEGADO") then {
    action(type="omfile" file="/var/log/denegados" template="RSYSLOG_FileFormat")
}
```

Validar con `rsyslogd -N1`, reiniciar exclusivamente el servicio rsyslog si la configuración es válida y generar un mensaje de prueba con:

```bash
logger -p authpriv.notice -t LSI_TCP_DENEGADO 'PRUEBA de enrutamiento del registro SSH'
```

Comprobar con `tail -n 5 /var/log/denegados` y distinguir explícitamente la entrada artificial de un rechazo de conexión real. Antes de la entrega se puede vaciar el fichero de prueba y registrar rechazos genuinos. La regla no usa `stop`, conservando el flujo normal de auditoría hacia `/var/log/auth.log`.

**Documentación externa:**
- https://docs.rsyslog.com/doc/getting_started/beginner_tutorials/02-first-config.html
- https://docs.rsyslog.com/doc/getting_started/installation.html
- https://docs.rsyslog.com/doc/getting_started/basic_configuration.html

**Estado:** apartado l en curso. Ni la regla de rsyslog ni el filtrado SSH real se han aplicado. Sigue pendiente identificar rangos VPN/Wi-Fi autorizados, documentar los servicios con libwrap, diferenciar wrappers de firewall y probar los rechazos reales con la bitácora `/var/log/denegados`.


### 10/10/2026 — Prueba superada del registro /var/log/denegados

**Comandos ejecutados por el alumno en la VM:**
```bash
cat > /etc/rsyslog.d/30-lsi-denegados.conf <<'EOF'
if ($programname == "LSI_TCP_DENEGADO") then {
    action(type="omfile" file="/var/log/denegados" template="RSYSLOG_FileFormat")
}
EOF
rsyslogd -N1
systemctl restart rsyslog
systemctl is-active rsyslog
logger -p authpriv.notice -t LSI_TCP_DENEGADO "PRUEBA de registro SSH denegado desde 192.0.2.10"
tail -n 5 /var/log/denegados
```

**Salidas verificadas:**
```text
rsyslogd: version 8.2504.0, config validation run (level 1), master config /etc/rsyslog.conf
rsyslogd: End of config validation run. Bye.
active
2026-10-10T17:58:54.848884+02:00 debian LSI_TCP_DENEGADO: PRUEBA de registro SSH denegado desde 192.0.2.10
```

**Interpretación:** el fichero adicional de rsyslog se ha creado, la sintaxis ha superado la validación, el servicio ha vuelto a estar activo y un mensaje enviado mediante `logger` con la etiqueta `LSI_TCP_DENEGADO` ha quedado registrado correctamente en `/var/log/denegados`, con hora y fecha. El contenido de la entrada es **una prueba artificial**, no evidencia de una denegación SSH real. El evento también puede pasar por la regla general de `auth.log`, ya que no se ha incorporado una directiva `stop`.

**Pendientes:** vincular los rechazos de TCP Wrappers con logger (mediante opción `spawn`), validar primero en el directorio de simulación y después aplicar únicamente con mecanismo de recuperación y rangos legítimos de VPN/Wi-Fi comprobados. Verificar un rechazo real, retirar del registro la única entrada de prueba sin perder registros auténticos e inventariar servicios compatibles.

**Próxima configuración de SIMULACIÓN (no ejecutada todavía):**
```bash
cd /root/lsi-tcpwrappers-prueba
printf '%s\n' 'sshd: ALL: spawn /usr/bin/logger -p authpriv.notice -t LSI_TCP_DENEGADO "SSH rechazado desde %a" : deny' > hosts.deny
tcpdchk -d -v
tcpdmatch -d sshd IP_CLIENTE_VPN
tcpdmatch -d sshd 192.0.2.10
```
La opción `%a` representa la dirección del cliente; `spawn` lanza el comando `logger` al coincidir la regla real. La hora la añade rsyslog. En modo `-d` se utilizan los archivos del directorio de pruebas; aún no debe copiarse la regla a `/etc/hosts.deny`, porque el alumno requiere acceso desde VPN y Wi-Fi UDC y los rangos autorizados no se han identificado. Conforme al enunciado, no se añaden comentarios a ficheros de configuración.

**Fuente técnica verificada:** https://sources.debian.org/src/tcp-wrappers/7.6.q-36/hosts_options.5/ (`spawn`, `deny`); https://manpages.debian.org/testing/libwrap0/hosts.deny.5.en.html (`%a`).

**Estado:** registro local para la etiqueta OPERATIVO; apartado l todavía EN CURSO.


### 10/10/2026 — Apartado l: prueba de reglas con spawn en directorio aislado

**Comandos ejecutados y verificados por el alumno:**
```bash
printf '%s\n' 'sshd: ALL: spawn /usr/bin/logger -p authpriv.notice -t LSI_TCP_DENEGADO "SSH rechazado desde %a" : deny' > hosts.deny
tcpdchk -d -v
tcpdmatch -d sshd IP_CLIENTE_VPN
tcpdmatch -d sshd 192.0.2.10
```

**Resultados reales:**
```text
>>> Rule hosts.allow line 1:
daemons:  sshd
clients:  IP_CLIENTE_VPN
access:   granted

>>> Rule hosts.deny line 1:
daemons:  sshd
clients:  ALL
access:   denied

client:   address  IP_CLIENTE_VPN
server:   process  sshd
access:   granted

client:   address  192.0.2.10
server:   process  sshd
access:   denied
```

**Interpretación:** configuración de prueba sintácticamente correcta, con permiso para IP_CLIENTE_VPN y denegación del resto. La presencia de `spawn` se ha aceptado sintácticamente; `tcpdmatch` simula la decisión, pero no ejecuta `logger` ni demuestra todavía que se haya registrado una denegación de SSH real.

**Siguiente experimento propuesto, NO ejecutado aún:** prueba de rechazo real limitada a `127.0.0.1` en el `/etc/hosts.deny` activo, sin denegar la IP VPN o Wi-Fi del alumno. Mantener `/etc/hosts.allow` actual intacto, recuperar con el respaldo existente si fuera necesario, verificar la regla con `tcpdchk` y `tcpdmatch`, hacer un intento local por IPv4 y comprobar que aparece un nuevo mensaje verdadero en `/var/log/denegados`. Retirar la regla de prueba al terminar, antes de diseñar la política final. Comandos propuestos:

```bash
printf '%s\n' 'sshd: 127.0.0.1: spawn /usr/bin/logger -p authpriv.notice -t LSI_TCP_DENEGADO "SSH rechazado desde %a" : deny' >> /etc/hosts.deny
tcpdchk -v
tcpdmatch sshd 127.0.0.1
ssh -4 -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null lsi@127.0.0.1
tail -n 5 /var/log/denegados
```

**Avisos:** el comando `ssh` puede devolver un error esperado por cierre de conexión; solo registrar como éxito si se verifica el evento generado automáticamente en `/var/log/denegados`. La IP `127.0.0.1` es loopback de la propia VM, distinta de la conexión remota VPN `IP_CLIENTE_VPN`. Debe seguir abierta la sesión SSH existente. Antes de cambiar las reglas definitivas faltan las IP/rangos permitidos de VPN y Wi-Fi y un método de reversión seguro.

**Estado:** simulación verificada; apartado l sigue EN CURSO.



### 10/10/2026, 18:22 — Rechazo SSH real mediante TCP Wrappers confirmado

**Situación inicial:** existía una regla de rsyslog en `/etc/rsyslog.d/30-lsi-denegados.conf` que almacena mensajes `LSI_TCP_DENEGADO` en `/var/log/denegados`. La regla anterior de simulación estaba en `/root/lsi-tcpwrappers-prueba`, no en la configuración activa.

**Comando ejecutado (cambio real en la VM):**
```bash
printf '%s\n' 'sshd: 127.0.0.1: spawn /usr/bin/logger -p authpriv.notice -t LSI_TCP_DENEGADO "SSH rechazado desde %a" : deny' >> /etc/hosts.deny
```
Añadió al final de `/etc/hosts.deny` una regla **temporal**, limitada a la IP loopback IPv4 `127.0.0.1`.

**Verificaciones reales:**
```bash
tcpdchk -v
```
```text
Using network configuration file: (null)

>>> Rule /etc/hosts.deny line 18:
daemons:  sshd
clients:  127.0.0.1
access:   denied
```
```bash
tcpdmatch sshd 127.0.0.1
tcpdmatch sshd IP_CLIENTE_VPN
```
```text
client:   address  127.0.0.1
server:   process  sshd
access:   denied
client:   address  IP_CLIENTE_VPN
server:   process  sshd
access:   granted
```

**Intento de conexión local real:**
```bash
ssh -4 -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null lsi@127.0.0.1
```
```text
Connection timed out during banner exchange
Connection to 127.0.0.1 port 22 timed out
```
El error por sí solo sería ambiguo, pero se correlaciona con la regla de denegación y el mensaje de `logger` generado automáticamente en el registro.

**Verificación del fichero de rechazos:**
```bash
tail -n 5 /var/log/denegados
```
```text
2026-10-10T17:58:54.848884+02:00 debian LSI_TCP_DENEGADO: PRUEBA de registro SSH denegado desde 192.0.2.10
2026-10-10T18:22:14.253650+02:00 debian LSI_TCP_DENEGADO: SSH rechazado desde 127.0.0.1
```

**Interpretación:** se ha comprobado un rechazo real de conexión SSH hacia localhost mediante TCP Wrappers y la generación de un registro con fecha, hora, máquina e IP. La entrada de `192.0.2.10` era una **prueba artificial anterior** enviada manualmente con `logger`, no un acceso remoto real. Esta prueba demuestra la integración de `spawn` + logger + rsyslog, pero **no cumple todavía la restricción definitiva de SSH para un conjunto autorizado de IP**: la regla activa solo afecta a `127.0.0.1`.

**Incidencias menores:** el alumno probó varios nombres erróneos del comando (`tcpdhck`, `tcpdcjk-v`, `tcpdcjk`) y obtuvo `orden no encontrada`. Finalmente ejecutó correctamente `tcpdchk -v`. No hubo cambios causados por esas erratas.

**Siguiente acción recomendada:** eliminar únicamente la regla temporal de loopback de `/etc/hosts.deny` y verificar con `tcpdchk -v` y `tcpdmatch sshd 127.0.0.1`; conservar el fichero `/var/log/denegados` y la configuración de rsyslog. **Todavía no ejecutado**. Mantener la sesión SSH remota durante el cambio.

**Pendientes de l:** inventariar servicios reales que utilicen TCP Wrappers, explicar diferencias con firewall, diseñar la política definitiva que funcione desde VPN y Wi-Fi UDC (con rangos oficiales o autorizados y recuperación), aplicarla y verificarla desde accesos permitidos y no permitidos.

**Estado:** registro y rechazo real COMPROBADOS; apartado l EN CURSO.

### 10/10/2026 — Retirada de la regla temporal de TCP Wrappers (confirmada)

**Comandos ejecutados por el alumno:**

```bash
sed -i '/^sshd: 127\.0\.0\.1: spawn /d' /etc/hosts.deny
tcpdchk -v
tcpdmatch sshd 127.0.0.1
cat /etc/hosts.deny
```

**Resultados observados:**
- `tcpdchk -v` solo mostró `Using network configuration file: (null)` y no enumeró reglas activas.
- `tcpdmatch sshd 127.0.0.1` devolvió `access: granted`.
- `/etc/hosts.deny` volvió a contener exclusivamente los comentarios originales, incluido `# ALL: PARANOID` comentado.
- Se confirma la retirada de la regla real temporal que había denegado el intento SSH desde `127.0.0.1`.
- La regla de registro de rsyslog en `/etc/rsyslog.d/30-lsi-denegados.conf` y el registro histórico `/var/log/denegados` no se han retirado.

**Interpretación:** no queda una política activa de denegación por TCP Wrappers. El rechazo y registro real desde localhost ya fueron demostrados; falta una configuración definitiva que restrinja SSH a los orígenes realmente autorizados, sin impedir el acceso por VPN y Wi-Fi de la UDC. La IP conocida de la sesión VPN era `IP_CLIENTE_VPN`, sin garantía de permanencia.

**Próximo paso (propuesto, no ejecutado):** identificar paquetes instalados dependientes de libwrap0 y los servicios actualmente en escucha con `apt-cache rdepends --installed libwrap0` y `ss -tulnp`. La dependencia de paquete es solo un indicio de compatibilidad; no demuestra por sí sola que un determinado servicio que esté ejecutándose utilice TCP Wrappers. Verificar ejecutables individuales con `ldd` o evidencias equivalentes. El binario `/usr/lib/openssh/sshd-session` ya fue confirmado enlazado con `libwrap.so.0`.

**Diferencia conceptual para la defensa:** un TCP Wrapper controla el acceso a servicios concretos compatibles con libwrap a nivel de aplicación, mientras que un firewall aplica reglas sobre tráfico de red y puede cubrir servicios que no utilizan libwrap. Ambos mecanismos no son equivalentes.

**Fuente externa:** Manual Debian apt-cache(8), opción `rdepends --installed`: https://manpages.debian.org/bookworm/apt/apt-cache.8.en.html

**Estado:** apartado l EN CURSO; regla temporal retirada y recuperación de acceso `localhost` comprobada.


### 10/10/2026 — Apartado l: inventario de paquetes y puertos

**Comandos ejecutados y salidas reales:**
```bash
apt-cache rdepends --installed libwrap0
```
```text
libwrap0
Reverse Depends:
  openssh-server
  tcpd
  pulseaudio
  openssh-server
  libsnmp40t64
```
```bash
ss -tulnp
```
```text
Netid  State   Recv-Q Send-Q Local Address:Port Peer Address:Port Process
tcp    LISTEN  0      128    0.0.0.0:22         0.0.0.0:*       users:(("sshd",pid=631,fd=6))
tcp    LISTEN  0      128    127.0.0.1:6010     0.0.0.0:*       users:(("sshd-session",pid=1218,fd=11))
tcp    LISTEN  0      128    [::1]:6010         [::]:*          users:(("sshd-session",pid=1218,fd=10))
tcp    LISTEN  0      128    [::]:22             [::]:*          users:(("sshd",pid=631,fd=7))
```

**Interpretación:**
- `apt-cache rdepends --installed libwrap0` enumera paquetes instalados con dependencias inversas relacionadas con `libwrap0`; la duplicación de `openssh-server` puede reflejar distintos tipos de dependencia o entradas de metadatos, no dos servidores SSH distintos. Por sí solo no demuestra que cada paquete ejecute un servicio protegido con libwrap.
- `tcpd` ofrece herramientas para TCP Wrappers, pero no es un servicio en escucha en esta VM.
- `libsnmp40t64` es una biblioteca; no implica que `snmpd` esté ejecutándose.
- `pulseaudio` figura en las dependencias inversas; no aparece un puerto del servicio en la captura, por lo que no podemos afirmar que haya un servicio PulseAudio escuchando.
- Los únicos sockets en escucha corresponden a SSH: puerto 22 en IPv4 e IPv6 (todas las interfaces) y puerto 6010 en loopback (asociado a `sshd-session`, compatible con reenvío X11).
- Ya se verificó con `ldd /usr/lib/openssh/sshd-session` la presencia de libwrap y, más importante, un rechazo real de SSH desde `127.0.0.1` con su registro en `/var/log/denegados`.
- No se ha verificado un inventario exhaustivo de todos los ejecutables del sistema enlazados con libwrap; la lista de dependencias y los sockets de escucha es una aproximación relevante.

**Diferencia para la defensa:** TCP Wrappers aplica un control de acceso dentro de los servicios compatibles con libwrap, en tanto que un firewall como nftables filtra paquetes en la pila de red sin requerir integración de las aplicaciones.

**Pendiente para cerrar el apartado l:** aplicar una política real de permiso explícito y denegación del resto para un conjunto de IP o redes autorizadas desde VPN y Wi-Fi UDC, comprobar nuevas conexiones permitidas y denegadas y dejar configurado el registro. La IP observada `IP_CLIENTE_VPN` es de una conexión VPN, pero no se ha determinado si cambia; aún no se conoce la IP o rango de entrada a la VM desde Wi-Fi UDC. No configurar una denegación general sin prever una reversión segura, dada la dependencia del acceso remoto SSH.

**Documentación:**
- Manual de hosts_access: https://manpages.debian.org/trixie/libwrap0/hosts_access.5.en.html
- Guía Debian TCP Wrappers: https://www.debian.org/doc/manuals/securing-debian-manual/tcpwrappers.en.html

**Estado:** inventario y explicación realizados; la política final sigue pendiente, por lo que el apartado l permanece EN CURSO.


### 10/10/2026 — Ubicación de acceso actual: casa mediante VPN UDC

El alumno confirma que **en este momento se conecta desde casa mediante la VPN de la UDC**. La última IP de origen observada en las conexiones SSH establecidas fue `IP_CLIENTE_VPN`; aún no se ha determinado si la VPN la asigna de forma persistente. No conocemos todavía la dirección/rango que verá la VM cuando el alumno utilice el Wi-Fi universitario sin VPN.

**Consecuencia práctica:** no dejar indefinidamente habilitada una política de denegación SSH que autorice solo `IP_CLIENTE_VPN`. Puede bloquear nuevas conexiones si cambia la IP VPN o si se conecta desde la universidad. Ya se probó una denegación real, su registro y la reversión de una regla restringida a loopback.

**Siguiente etapa propuesta (no ejecutada):** hacer una prueba temporal de política de denegación general, solo después de actualizar el respaldo seguro y armar/verificar un temporizador transitorio de systemd que restaure `hosts.allow` y `hosts.deny`. Verificar después una conexión SSH **nueva** por VPN, no solo la sesión actual. Retirar la política temporal o dejarla revertir mientras se obtienen las IP/redes autorizadas del campus. No reiniciar ni cerrar la sesión SSH durante la prueba.

**Herramienta posible:** `systemd-run --on-active=...` para programar una ejecución transitoria de recuperación con temporizador; consultar la documentación de Debian 13: https://manpages.debian.org/trixie/systemd/systemd-run.1.en.html

**Estado:** apartado l continúa EN CURSO; la configuración real de TCP Wrappers permanece sin reglas activas (según última comprobación del alumno). La regla de rsyslog para `/var/log/denegados` sigue configurada y la evidencia de rechazo desde localhost se conserva.


### 10/10/2026 — Temporizador de recuperación TCP Wrappers programado

**Comandos ejecutados (salida real del alumno):**
```bash
cp -a /etc/hosts.allow /root/lsi-tcpwrappers-respaldo/hosts.allow
cp -a /etc/hosts.deny /root/lsi-tcpwrappers-respaldo/hosts.deny
systemd-run --unit=lsi-tcpwrap-rollback --on-active=15min /bin/sh -c 'cp -a /root/lsi-tcpwrappers-respaldo/hosts.allow /etc/hosts.allow && cp -a /root/lsi-tcpwrappers-respaldo/hosts.deny /etc/hosts.deny'
systemctl list-timers --all | grep lsi-tcpwrap-rollback
```

**Salida verificada:**
```text
Running timer as unit: lsi-tcpwrap-rollback.timer
Will run service as unit: lsi-tcpwrap-rollback.service
Sat 2026-10-10 18:49:49 CEST    14min -    - lsi-tcpwrap-rollback.timer   lsi-tcpwrap-rollback.service
```

**Interpretación:** el usuario ha copiado de nuevo los archivos originales de control de acceso al directorio de respaldo y ha programado una tarea transitoria de systemd para restaurarlos a las **18:49:49 CEST del 10/10/2026**, aproximadamente 15 minutos después de crearla. Se ha comprobado su presencia en `list-timers`, pero **no se ha comprobado aún que la restauración haya llegado a ejecutarse**. Si vence antes de aplicar las reglas restrictivas, es imprescindible crear un nuevo temporizador: no se puede asumir que siga activo.

**Siguiente paso propuesto (todavía no ejecutado):** comprobar que el timer continúa activo y dispone de varios minutos, confirmar la dirección de origen de la conexión SSH existente (anteriormente `IP_CLIENTE_VPN`), aplicar temporalmente una regla permisiva específica en `hosts.allow` y una regla restrictiva para `sshd` en `hosts.deny`, verificar con `tcpdchk` y `tcpdmatch`, probar apertura de nueva sesión SSH sin cerrar la actual y dejar actuar al mecanismo de recuperación o restablecer archivos de respaldo.

**Precaución:** la IP asignada por la VPN UDC puede cambiar; ninguna regla permanente de denegación debe mantenerse hasta identificar las redes autorizadas del campus y de la VPN. No modificar ni reiniciar el servicio SSH en este experimento.

**Estado:** apartado l EN CURSO; el temporizador está **programado según la última salida**, pendiente de nueva verificación y prueba de restauración.


### 10/10/2026 — Comprobación del temporizador antes del filtrado real

**Comandos y salidas reales aportadas:**

```bash
systemctl is-active lsi-tcpwrap-rollback.timer
```
```text
active
```

```bash
systemctl list-timers --all | grep lsi-tcpwrap-rollback
```
```text
Sat 2026-10-10 18:49:49 CEST     5min -                                       - lsi-tcpwrap-rollback.timer   lsi-tcpwrap-rollback.service
```

```bash
ss -tnp state established | grep ':22'
```
```text
0      196      IP_VM_ENS33:22       IP_CLIENTE_VPN:63418 users:(("sshd-session",pid=1218,fd=7),("sshd-session",pid=1167,fd=7))
```

**Conclusión:** el temporizador original estaba activo en ese instante y restaban aproximadamente cinco minutos; la IP del cliente SSH seguía siendo `IP_CLIENTE_VPN`. Como el tiempo restante puede haber transcurrido antes de ejecutar nuevas instrucciones, no se puede asumir que ese temporizador siga disponible. No hay evidencia de que las reglas restrictivas generales se hayan aplicado aún.

**Siguiente paso propuesto, NO ejecutado:** rearmar recuperación con una nueva unidad transitoria, por ejemplo `lsi-tcpwrap-rollback-v2.timer`, antes de activar la política; confirmar primero que la nueva unidad está activa, retirar el temporizador antiguo solo después, y continuar la prueba con una nueva conexión SSH desde la VPN sin cerrar la sesión actual. No dejar activa una política que únicamente permita una IP de VPN potencialmente cambiante como configuración definitiva.

**Estado del apartado l:** EN CURSO; prueba real de loopback y registro completados, prueba temporal de lista autorizada todavía pendiente.


### 10/10/2026 — Apartado l: validación de reglas reales allow/deny

**Comandos ejecutados y salidas proporcionadas por el alumno:**
```bash
tcpdchk -v
tcpdmatch sshd IP_CLIENTE_VPN
tcpdmatch sshd 192.0.2.10
```

```text
Using network configuration file: (null)

>>> Rule /etc/hosts.allow line 11:
daemons:  sshd
clients:  IP_CLIENTE_VPN
access:   granted

>>> Rule /etc/hosts.deny line 18:
daemons:  sshd
clients:  ALL
access:   denied
client:   address  IP_CLIENTE_VPN
server:   process  sshd
access:   granted
client:   address  192.0.2.10
server:   process  sshd
access:   denied
```

**Interpretación:** las reglas actualmente visibles en los archivos reales `/etc/hosts.allow` y `/etc/hosts.deny` han superado el análisis sintáctico y la evaluación simulada. La IP VPN observada `IP_CLIENTE_VPN` está permitida y la IP documental de prueba `192.0.2.10` se denegaría. Esta validación no equivale a haber comprobado la apertura de una sesión SSH nueva y tampoco acredita por sí sola una conexión realmente rechazada desde `192.0.2.10`. El rechazo real desde loopback `127.0.0.1` ya se verificó en una prueba anterior.

**Seguridad operacional:** existe o existió un timer de rollback `lsi-tcpwrap-rollback-v2.timer` (su activación no fue confirmada explícitamente por salida del alumno en el último turno). Antes de realizar pruebas reales, verificarlo y asegurarse de que quedan minutos. Mantener la sesión actual abierta. Probar desde una segunda terminal por VPN con `ssh lsi@IP_VM_ENS33` y registrar el resultado. Restaurar luego `hosts.allow` y `hosts.deny` desde el respaldo cuando ya no se necesite la política temporal; verificar restauración y desactivar cualquier rollback restante. Evitar dejar permanentemente la regla `sshd: ALL` con solo una IP VPN que pueda cambiar y que no incluya a las direcciones del campus y compañero.

**Estado:** política real validada por `tcpdchk` y `tcpdmatch`, **pendiente prueba de nueva sesión autorizada y restauración documentada**. Apartado l EN CURSO.


### 10/10/2026 — Conexión SSH autorizada desde Windows y restauración (confirmado por el alumno)

**Confirmación del alumno (no se aportó captura de la nueva sesión ni salida de los comandos de restauración):**
- Pudo abrir una **nueva conexión SSH desde CMD de Windows** a la VM, mientras estaban configuradas las reglas reales que autorizaban `IP_CLIENTE_VPN` y denegaban el resto.
- Después indicó que **restauró todos los archivos de control de acceso a su configuración original**.

**Conclusión y grado de evidencia:**
- **Comprobado antes con salida:** `tcpdchk -v` sin errores, `tcpdmatch sshd IP_CLIENTE_VPN` → `granted` y `tcpdmatch sshd 192.0.2.10` → `denied`. Anteriormente se verificó un rechazo SSH local real desde `127.0.0.1`, generado y registrado automáticamente en `/var/log/denegados`.
- **Confirmado por el alumno:** nueva conexión SSH real autorizada desde Windows y restauración posterior.
- **No comprobado aún con salida después de la restauración:** ausencia de reglas activas en `/etc/hosts.allow` y `/etc/hosts.deny`, estado final de los temporizadores de reversión y persistencia del archivo `/var/log/denegados`.

**Revisión final sugerida (consultas no destructivas):**
```bash
tcpdchk -v
tcpdmatch sshd IP_CLIENTE_VPN
tcpdmatch sshd 192.0.2.10
systemctl list-timers --all | grep lsi-tcpwrap-rollback
```

Si las reglas han vuelto por completo a la configuración de origen (solo comentarios), `tcpdchk -v` no debería listar reglas y ambos `tcpdmatch` devolverían `access: granted` por ausencia de coincidencias de denegación. Si queda algún temporizador de recuperación **activo**, detenerlo una vez confirmado el estado restaurado para que no sobrescriba configuraciones futuras:
```bash
systemctl stop lsi-tcpwrap-rollback.timer lsi-tcpwrap-rollback-v2.timer
```
Es posible que alguna unidad ya no exista, por ser temporal; no interpretar eso como fallo de restauración.

**Pendiente para cerrar el apartado l de forma definitiva:** decidir/documentar el conjunto autorizado que contemple VPN y Wi-Fi de la UDC y, si corresponde, las IP desde las que se conecta el compañero; no dejar una lista de permisos de una sola IP de VPN potencialmente cambiante como política permanente. La prueba temporal y su reversión sí están documentadas.

**Estado:** funcionalidad de filtrado y registro validada mediante pruebas temporales; **configuración restrictiva definitiva pendiente**. El archivo `/etc/rsyslog.d/30-lsi-denegados.conf` se instaló y probó; no se ha confirmado su retirada y se presupone conservado hasta comprobar lo contrario.


### 10/10/2026 — Restauración verificada y temporizador v2 aún pendiente

**Salidas reales aportadas:**
```bash
systemctl list-timers --all | grep lsi-tcpwrap-rollback
```
```text
Sat 2026-10-10 19:01:20 CEST 2min 13s - - lsi-tcpwrap-rollback-v2.timer lsi-tcpwrap-rollback-v2.service
```
```bash
tcpdchk -v
```
```text
Using network configuration file: (null)
```

**Interpretación:** la comprobación de `tcpdchk` no enumera reglas activas, coherente con la restauración que el alumno confirmó haber realizado. En el momento de la consulta quedaban 2 min 13 s para la ejecución del temporizador temporal `lsi-tcpwrap-rollback-v2.timer`, previsto para las 19:01:20 CEST del 10/10/2026. Que `tcpdchk` no muestre reglas no confirma por sí solo que los archivos sean idénticos byte a byte al respaldo.

**Próxima acción propuesta, aún no confirmada como ejecutada:**
```bash
systemctl stop lsi-tcpwrap-rollback-v2.timer
systemctl list-timers --all | grep lsi-tcpwrap-rollback
grep -vE '^[[:space:]]*(#|$)' /etc/hosts.allow /etc/hosts.deny
```

**Precaución temporal:** el temporizador podría haber vencido entre consultas. Si ya no existe o se ejecutó, comprobar el estado resultante y no interpretarlo automáticamente como fallo.

**Estado del apartado l:** pruebas de compatibilidad, filtrado, registro real, acceso SSH autorizado y reversión realizadas; configuración de denegación por defecto **no quedó instalada de forma permanente**. Para afirmar que el requisito literal de configuración definitiva está completado, aún se necesitará elegir las IP/rangos autorizados (VPN, Wi-Fi UDC, posible compañero) y dejar la política correctamente configurada sin riesgo de perder acceso.


### 10/10/2026 — Verificación final: rollback detenido y reglas restauradas

**Comandos ejecutados (confirmados por la salida facilitada por el alumno):**

```bash
systemctl stop lsi-tcpwrap-rollback-v2.timer
systemctl list-timers --all | grep lsi-tcpwrap-rollback
grep -vE '^[[:space:]]*(#|$)' /etc/hosts.allow /etc/hosts.deny
```

**Resultados observados:**
- `systemctl stop` concluyó sin errores visibles.
- `systemctl list-timers --all | grep lsi-tcpwrap-rollback` no produjo ninguna salida: ya no aparecen temporizadores de recuperación con ese nombre en el listado.
- `grep` tampoco devolvió líneas: `/etc/hosts.allow` y `/etc/hosts.deny` no contienen reglas activas; solo líneas vacías o comentarios.
- La salida anterior de `tcpdchk -v` tampoco había enumerado reglas, coherente con los resultados actuales.

**Conclusión:** la política temporal restrictiva ha sido retirada y el mecanismo de recuperación v2 ya no está pendiente. Las pruebas de filtrado y auditoría del apartado l están realizadas: vinculación libwrap a `sshd-session`, denegación SSH real desde `127.0.0.1` con registro automático en `/var/log/denegados`, simulaciones de aceptación/rechazo y acceso SSH nuevo desde CMD de Windows autorizado (este último confirmado por el alumno). La configuración independiente de rsyslog para el registro no ha sido retirada según lo observado; no se ha verificado nuevamente su estado en esta última operación.

**Estado del apartado l:** PRUEBAS COMPLETADAS; requisito de mantener una lista de IP autorizadas y denegar las demás **pendiente de configuración definitiva**. Se evitará establecer una regla permanente hasta conocer las redes autorizadas desde VPN de la UDC, Wi-Fi de la universidad y, en su caso, las IP reales desde las que se conectará el compañero. No inventar direcciones ni asumir que `IP_CLIENTE_VPN` será fija.

**Cambios en GitHub:** ninguno. Esta documentación queda lista para integrarse posteriormente en el repositorio.


### 10/10/2026 — Decisión: mantener TCP Wrappers de forma permanente

**Decisión manifestada por el alumno:** quiere dejar **activa de forma permanente** una política de TCP Wrappers que permita la IP desde su VPN (`IP_CLIENTE_VPN`) y la IP desde la que se conecta la máquina virtual de su compañero; queda pendiente añadir más adelante la IP observada cuando se conecte desde el Wi-Fi universitario. La frase del alumno repitió «VPN» al final; se interpreta provisionalmente como Wi-Fi por contexto, pendiente de corrección si no fuera así.

**Estado actual probado:** en la última comprobación no había reglas activas ni temporizadores de reversión; se había restaurado la configuración original. Por tanto, **la política permanente aún NO se ha aplicado**.

**Configuración deseada de `/etc/hosts.allow` (esquema, no ejecutar con marcador):**
```text
sshd: IP_CLIENTE_VPN
sshd: IP_REAL_DE_ORIGEN_DEL_COMPAÑERO
```

**Configuración deseada de `/etc/hosts.deny`:**
```text
sshd: ALL: spawn /usr/bin/logger -p authpriv.notice -t LSI_TCP_DENEGADO "SSH rechazado desde %a" : deny
```

**Requisitos antes de la implantación:** obtener la IP exacta desde la cual el compañero establecerá SSH hacia la VM (no confundir IP de su servidor con la IP cliente si no se conecta desde esa VM); crear un respaldo actualizado y rearmar y verificar un temporizador de recuperación; comprobar `tcpdchk -v` y `tcpdmatch`; abrir una nueva sesión permitida antes de desactivar la recuperación. No sobreescribir el respaldo con las reglas restrictivas. Confirmar que la dirección VPN no varía si se pretende acceso estable fuera del campus.

**Pendiente:** el usuario debe facilitar la IP de origen de la máquina de su compañero. Después se aplicará la política persistente y se verificarán los accesos; se añadirá más adelante la IP/rango autorizado del Wi-Fi UDC. Registrar los cambios y resultados reales en esta bitácora.


### 10/10/2026 — IP de compañero confirmada; reglas definitivas preparadas

**Nuevo dato confirmado por el alumno:** la IP de la máquina virtual de su compañero es `IP_COMPANERO_LAN`. Es la dirección que se pretende autorizar en SSH junto con la IP observada del cliente del alumno conectado desde VPN UDC (`IP_CLIENTE_VPN`). La IP o rango de acceso desde Wi-Fi UDC sigue sin determinarse. El alumno desea mantener una política restrictiva permanente una vez verificadas nuevas conexiones reales.

**Política elegida, aún NO aplicada en este paso:**

`/etc/hosts.allow` (conservar los comentarios preexistentes):
```text
sshd: IP_CLIENTE_VPN
sshd: IP_COMPANERO_LAN
```

`/etc/hosts.deny` (conservar los comentarios preexistentes):
```text
sshd: ALL: spawn /usr/bin/logger -p authpriv.notice -t LSI_TCP_DENEGADO "SSH rechazado desde %a" : deny
```

**Riesgo identificado:** la IP VPN `IP_CLIENTE_VPN` puede cambiar. Hasta añadir el rango autorizado de Wi-Fi, nuevas conexiones desde la red del campus quedarían denegadas. No confundir la IP de la VM compañera con la IP desde la que realmente origina una conexión: si se conecta desde su ordenador o VPN, debe determinarse la dirección de origen por `ss`.

**Plan de despliegue seguro para la siguiente intervención (no ejecutado):**
1. Mantener la sesión SSH actual; confirmar ausencia de reglas y respaldar `/etc/hosts.allow` y `/etc/hosts.deny`.
2. Armar y verificar temporizador de rollback independiente para restaurar ambos archivos pasado un plazo suficiente.
3. Añadir las dos reglas de permiso y una regla global de denegación para `sshd` sin añadir comentarios.
4. Ejecutar `tcpdchk -v`, `tcpdmatch sshd IP_CLIENTE_VPN`, `tcpdmatch sshd IP_COMPANERO_LAN` y `tcpdmatch sshd 192.0.2.10`.
5. Comprobar nueva conexión real desde Windows por VPN; si es posible, desde la VM del compañero. Verificar registro de denegaciones auténticas sin inventar accesos.
6. Si alguna prueba falla, restaurar el respaldo y dejar actuar la reversión programada. Solo cancelar el temporizador después de verificar la funcionalidad, confirmar la elección de mantener la política y considerar el riesgo de IP VPN dinámica.

**Fuente de referencia:** https://manpages.debian.org/trixie/libwrap0/hosts_access.5.en.html (precedencia de hosts.allow sobre hosts.deny) y https://manpages.debian.org/trixie/systemd/systemd-run.1.en.html (timer `--on-active`).

**Estado del apartado l:** IP del compañero documentada, política preparada; AÚN PENDIENTE de despliegue permanente y verificación.


### Apartado l — Incluir también el acceso VPN del compañero

El alumno pregunta si conviene autorizar, además de la IP de la VM del compañero (`IP_COMPANERO_LAN`), la IP de su portátil cuando se conecta mediante la VPN de la UDC. **Decisión recomendada:** sí, si el compañero necesita abrir sesiones SSH desde su ordenador por VPN. El servidor ve como origen la IP de esa conexión, distinta de la IP de su VM. Si solamente accediese desde su VM, no haría falta esa entrada adicional.

**Plan para `/etc/hosts.allow` (aún no aplicado):**
```text
sshd: IP_CLIENTE_VPN
sshd: IP_COMPANERO_LAN
sshd: IP_VPN_REAL_DEL_COMPAÑERO
```

**Pendiente:** obtener la IP de VPN real del compañero (por ejemplo, conectándose a su propia VM y ejecutando `echo "$SSH_CONNECTION"` en una sesión interactiva SSH, donde el primer campo indica la IP de origen observada); posteriormente, obtener la IP o el rango autorizado desde el Wi-Fi UDC del alumno. Las IP VPN pueden cambiar. No copiar literalmente el marcador `IP_VPN_REAL_DEL_COMPAÑERO` a archivos de configuración ni activar aún una denegación general sin tener un acceso de recuperación disponible.

**Estado:** las reglas restrictivas definitivas no están desplegadas; la bitácora y el fichero de rsyslog de registro de denegados se mantienen.


### Apartado l — Configuración definitiva entregada para aplicar

El alumno solicita expresamente **no realizar más pruebas** y recibir la configuración de TCP Wrappers para mantenerla permanentemente. Se facilitan los siguientes comandos, **propuestos y todavía no confirmados como ejecutados en la máquina**, partiendo de los archivos originales restaurados:

```bash
printf '%s\n' 'sshd: IP_CLIENTE_VPN, IP_COMPANERO_LAN' >> /etc/hosts.allow
printf '%s\n' 'sshd: ALL: spawn /usr/bin/logger -p authpriv.notice -t LSI_TCP_DENEGADO "SSH rechazado desde %a" : deny' >> /etc/hosts.deny
```

La política resultante permite nuevas conexiones SSH desde la IP VPN del alumno `IP_CLIENTE_VPN` y desde la VM del compañero `IP_COMPANERO_LAN`, y rechaza las demás, con registro mediante la etiqueta `LSI_TCP_DENEGADO`. Ya estaba comprobado el encaminamiento de esa etiqueta por rsyslog a `/var/log/denegados`, y un rechazo real desde localhost durante pruebas anteriores.

**Pendientes de añadir a la lista permitida:** IP VPN del compañero e IP (o rango autorizado) desde Wi-Fi UDC del alumno, aún desconocidos; no se inventan. La IP VPN puede variar y el filtrado, si queda permanente, podría impedir futuras reconexiones desde una IP nueva. No es necesario reiniciar SSH ni rsyslog para que se evalúen las reglas en nuevas conexiones.

**Estado:** instrucciones definitivas entregadas; **no afirmar que la política quedó aplicada** hasta que el alumno confirme su ejecución. Conservación de comentarios originales conforme al enunciado.


### Apartado l — Aplicación definitiva confirmada por el alumno

El alumno respondió «listo» tras recibir los comandos de configuración permanente de TCP Wrappers, por lo que **se registra como aplicada según confirmación del alumno**, sin nueva captura de los archivos.

**Política comunicada:**
- `/etc/hosts.allow`: `sshd: IP_CLIENTE_VPN, IP_COMPANERO_LAN`.
- `/etc/hosts.deny`: `sshd: ALL: spawn /usr/bin/logger -p authpriv.notice -t LSI_TCP_DENEGADO "SSH rechazado desde %a" : deny`.
- `/etc/rsyslog.d/30-lsi-denegados.conf` y `/var/log/denegados`: previamente comprobados con un rechazo real desde localhost.

**Pendiente:** añadir la IP de VPN del compañero y la IP o el rango autorizado del Wi-Fi universitario cuando se conozcan. Si la VPN del alumno cambia su IP actual `IP_CLIENTE_VPN`, podría perder el acceso de nuevas conexiones por VPN. Distinguir la aplicación **confirmada por el alumno** de una comprobación posterior con salidas de `tcpdchk`.

**GitHub:** no modificado.
