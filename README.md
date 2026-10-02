# LSI · UDC · 2026

Cuaderno de estudio de la práctica 1. Se actualiza conforme se realizan los pasos, distinguiendo resultados comprobados y tareas pendientes.

## Estado

| Parte | Estado |
| --- | --- |
| a) Interfaces | Aplicadas; conexión al router comprobada |
| a) hosts | Cambio comunicado; comprobación IPv4 indicada como correcta |
| a) resolv.conf | DNS cambiados; falta validarlos |
| a) nsswitch.conf | Revisado, sin cambios |
| a) sources.list | Revisado; Buster devuelve 404 |
| a) sudo | Pendiente de configurar y verificar con el usuario normal |
| b) Actualización | Pendiente; todavía no se ha actualizado Debian |

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
- La ruta 169.254.0.0/16 se observó, pero no se investigó ni modificó.
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

## 3. /etc/resolv.conf

Contenido inicial facilitado:

```text
domain udc.pri
search udc.pri
nameserver 10.8.8.8
nameserver 10.8.8.9
```

- `domain`: dominio local. En el resolvedor tradicional, domain y search son alternativas y prevalece la última; aquí ambos señalan udc.pri.
- `search`: sufijo para nombres cortos, por ejemplo servidor → servidor.udc.pri.
- `nameserver`: servidor DNS que traduce nombres a IP. Una máquina cualquiera no es DNS solo por tener una IP.

El alumno comunicó que retiró los dos DNS iniciales y dejó:

```text
nameserver 10.8.12.49
nameserver 10.8.12.47
nameserver 10.8.12.50
```

**Sin validar:** no sabemos si esas IP prestan DNS o son las indicadas por el profesor. No se ha visto el archivo final. El resolvedor tradicional de glibc admite hasta tres entradas nameserver.

Comprobación propuesta, sin resultado documentado tras el cambio:

```bash
getent ahostsv4 deb.debian.org
```

Comprueba la resolución del sistema para ese nombre, no cada servidor individualmente. Los 404 anteriores de APT demostraron resolución y conexión en aquel momento, no el funcionamiento de los DNS nuevos.

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

## 5. /etc/apt/sources.list y error 404

Se observaron entradas deb y deb-src para:

| Servidor | Distribución | Componentes |
| --- | --- | --- |
| http://deb.debian.org/debian/ | buster | main |
| http://security.debian.org/debian-security | buster/updates | main contrib |
| http://deb.debian.org/debian/ | buster-updates | main contrib |

`deb` ofrece paquetes instalables; `deb-src`, fuentes. Las líneas con # son comentarios. La referencia al DVD Debian 10.4 identifica el medio de instalación, no confirma la versión instalada actual.

`apt update` falló con 404 porque Buster pasó al archivo histórico. El posterior `apt upgrade` con cero actualizaciones **no demuestra que el sistema esté actualizado**, pues no se descargaron los índices.

Se propuso cambiar los servidores a archive.debian.org conservando Buster para preparar la actualización. **No consta que se haya aplicado ni que apt update haya terminado correctamente.** El alumno decidió continuar dentro del apartado b.

[Aviso oficial del traslado de Buster](https://lists.debian.org/debian-devel-announce/2025/06/msg00001.html).

## 6. Apartado b: versión inicial y actualización

**Versión inicial confirmada el 2 de octubre de 2026:** Debian GNU/Linux 10.4 (Buster), arquitectura amd64 (x86 de 64 bits). La actualización sigue pendiente.

En `/`, dispositivo `/dev/sda1`: 13 GB totales, 3,8 GB usados, 7,9 GB disponibles y 33 % de uso. El espacio necesario se comprobará también con la propuesta de APT antes de instalar.

Comandos ejecutados y resultados facilitados por el alumno:

```bash
cat /etc/os-release
cat /etc/debian_version
dpkg --print-architecture
df -h /
```

Documentan distribución, versión, arquitectura y espacio disponible. Se recomendó una instantánea antes de actualizar si la plataforma lo permite; no consta que se haya creado.

Consulta del 25 de septiembre de 2026: estable era **Debian 13 Trixie, actualización 13.7**. Revisar la versión vigente al ejecutar la actualización.

Ruta prevista:

```text
Debian 10 Buster → Debian 11 Bullseye → Debian 12 Bookworm → Debian 13 Trixie
```

Preparar la versión de partida y seguir cada salto consecutivo. No sustituir directamente buster por trixie ni ejecutar todos los saltos de una vez.

- [Actualizaciones de Debian 13](https://www.debian.org/releases/trixie/errata)
- [Debian 12 a 13](https://www.debian.org/releases/trixie/release-notes/upgrading.html)
- [Debian 11 a 12](https://www.debian.org/releases/bookworm/amd64/release-notes/ch-upgrading.html)

## 7. Cómo mantener estos apuntes

Por cada paso registrar objetivo, archivo, comandos ejecutados, explicación, resultado y pendientes. No marcar como ejecutado un comando propuesto sin confirmación. No guardar contraseñas, claves privadas ni tokens.

Los comandos Linux son para la VM; este repositorio contiene apuntes. Como root no hace falta sudo, pero eso no prueba que sudo esté configurado para el usuario normal.

El enunciado indica no añadir comentarios a los archivos de configuración salvo los originales. Las explicaciones se conservan aquí.

Pendientes inmediatos: validar DNS, preparar el primer salto de Debian, completar sudo y confirmar ens34.

## Historial

- 2026-09-25: recopilación inicial de la sesión; red comprobada, archivos básicos revisados y actualización pendiente.

- 2026-10-02: confirmados Debian 10.4, amd64 y 7,9 GB disponibles en `/`. Siguiente comprobación propuesta: resolución de archive.debian.org y estado actual de sources.list; todavía sin resultado.
