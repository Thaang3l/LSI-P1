# LSI · UDC · 2026

Cuaderno de estudio de la práctica 1. Actualizado hasta el 9 de octubre de 2026, a petición del alumno. Distingue resultados comprobados, recomendaciones y tareas pendientes.

## Estado

**El estado vigente está resumido en la sección 8.** Las secciones anteriores conservan el contexto de instalación y actualización; sus inventarios iniciales no describen los servicios actuales. Esta actualización añade solo cambios que permanecen aplicados según las salidas de la VM, sin incorporar pruebas retiradas.

| Parte | Estado |
| --- | --- |
| a) Interfaces | Aplicadas; conexión al router comprobada |
| a) hosts | Archivo confirmado: 10.11.49.56 debian |
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

IP asignada indicada por el alumno: **10.11.49.56**. Nombre observado: **debian**.

Configuración aplicada:

```text
auto lo ens33 ens34

iface lo inet loopback

iface ens33 inet static
    address 10.11.49.56
    netmask 255.255.254.0
    broadcast 10.11.49.255
    network 10.11.48.0
    gateway 10.11.48.1

iface ens34 inet static
    address 10.11.51.56
    netmask 255.255.254.0
    broadcast 10.11.51.255
    network 10.11.50.0
```

Se corrigió `addres` por `address`.

### Por qué network es .48 y la IP es .49

La máscara 255.255.254.0 equivale a /23. La red 10.11.48.0/23 abarca los bloques 10.11.48.x y 10.11.49.x. Sus hosts utilizables van de 10.11.48.1 a 10.11.49.254; 10.11.49.255 es el broadcast.

La puerta de enlace 10.11.48.1 es el router del ejemplo y respondió desde la máquina. No se calcula a partir de la IP ni tiene que terminar en .1.

### Por qué se propuso ens34 con .51

Se conservó la posición al pasar de la red 10.11.48.0/23 a 10.11.50.0/23: 49 pasa a 51. **Es una inferencia del ejemplo; falta confirmar la asignación del profesor.** 10.11.50.56 también pertenece a la segunda red, pero es otra posición.

### Comprobaciones realizadas

```bash
sudo ifup --no-act ens33 ens34
sudo systemctl restart networking
ip route
ip -br addr
ping -c 4 10.11.48.1
```

`--no-act` muestra las operaciones previstas sin ejecutarlas; no comprueba conectividad ni detecta todos los errores. Aplicar cambios desde la consola de la VM permite recuperar el acceso si se interrumpe SSH.

Resultado observado:

```text
default via 10.11.48.1 dev ens33 onlink
10.11.48.0/23 dev ens33 proto kernel scope link src 10.11.49.56
10.11.50.0/23 dev ens34 proto kernel scope link src 10.11.51.56
169.254.0.0/16 dev ens33 scope link metric 1000
```

- ens33: 10.11.49.56/23; ens34: 10.11.51.56/23.
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
10.11.49.56 debian
```

Se conservan localhost y las entradas IPv6. El enunciado pide analizar estos archivos; no exige expresamente ese cambio.

```bash
getent hosts debian
getent ahostsv4 debian
```

El primero mostró IPv6 locales de enlace (fe80::). Eso no demuestra que hosts esté mal: getent puede consultar otras fuentes. El segundo consulta IPv4 y puede repetir la IP con STREAM, DGRAM y RAW. El alumno indicó que estaba bien, pero no aportó su salida ni el archivo final.

## 3. /etc/resolv.conf: DNS y resolución del fallo

Contenido inicial: dominio y búsqueda udc.pri, con DNS 10.8.8.8 y 10.8.8.9. Se añadieron 10.8.12.49, 10.8.12.50 y 10.8.12.47 y llegaron a ocupar las tres primeras posiciones.

- domain establece el dominio local; search permite completar nombres cortos. En el resolvedor tradicional son alternativas y prevalece la última; aquí coinciden.
- nameserver identifica un servidor DNS. Una IP de la red no es necesariamente un DNS.
- El resolvedor tradicional de glibc utiliza hasta tres entradas nameserver. Tener cinco no implica utilizar las cinco.

**Síntoma:** APT mostraba «No se pudo resolver» y getent no devolvía direcciones. El router 10.11.48.1 respondía al ping, pero 10.8.8.8 no. Ese ping fallido no demostraba que DNS estuviera roto: ICMP y DNS son servicios distintos.

No había dig ni nslookup. Se usó host para consultar cada DNS sin cambiar primero el archivo:

~~~bash
host archive.debian.org 10.8.12.49
host archive.debian.org 10.8.12.50
host archive.debian.org 10.8.12.47
host archive.debian.org 10.8.8.8
host archive.debian.org 10.8.8.9
~~~

| Servidor | Resultado observado |
| --- | --- |
| 10.8.12.49, 10.8.12.50, 10.8.12.47 | Tiempo de espera agotado desde esta máquina |
| 10.8.8.8 y 10.8.8.9 | Respuesta DNS correcta para archive.debian.org |

**Solución aplicada:** conservar las cinco direcciones, como pidió el alumno, y colocar primero las dos que respondían:

~~~text
domain udc.pri
search udc.pri
nameserver 10.8.8.8
nameserver 10.8.8.9
nameserver 10.8.12.49
nameserver 10.8.12.50
nameserver 10.8.12.47
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
- Red estática conservada: ens33 `10.11.49.56/23`, ens34 `10.11.51.56/23`, gateway `10.11.48.1` por ens33. DNS funciona en las comprobaciones con `getent`.
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
