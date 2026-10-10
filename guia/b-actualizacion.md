# b) Actualización de Debian

[Volver al índice](../README.md)

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
