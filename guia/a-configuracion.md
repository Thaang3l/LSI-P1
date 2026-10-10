# a) Configuración básica de la VM

[Volver al índice](../README.md)

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

Se corrigió una errata `addres` → `address`. La asignación de `ens34` se utilizó y se verificó en la máquina; no se aporta una confirmación independiente de la asignación del profesor.

| Dato | Explicación |
| --- | --- |
| `/23` | Equivale a `255.255.254.0`; agrupa dos bloques consecutivos del tercer octeto |
| Red `10.11.48.0/23` | Incluye `10.11.48.x` y `10.11.49.x` |
| IP `10.11.49.56` | Dirección del equipo, distinta de la dirección de red |
| Broadcast `10.11.49.255` | Última dirección de esa subred |
| Gateway `10.11.48.1` | Router configurado; no se obtiene automáticamente sumando uno a la red |
| Red `10.11.50.0/23` | Incluye tanto `10.11.50.x` como `10.11.51.x` |

**Respuesta breve:** que `network` termine en `.48.0` no obliga a que todas las IP tengan `.48` en el tercer octeto.

## Paso 2. Aplicar y comprobar la red

Durante la configuración se usaron `ifup --no-act` y el reinicio de networking. Son operaciones históricas: reiniciar la red desde SSH puede cortar la conexión; no hace falta repetirlo para defender la práctica.

Para demostrar el estado sin cambiarlo:

```bash
ip -br addr
ip route
ping -c 3 10.11.48.1
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
10.11.49.56 debian
```

La asociación quedó recogida en el inventario usado en la anterior actualización de los apuntes. Se conservan `localhost` y las entradas IPv6 originales. No se sustituye la palabra `debian` por una IP: el formato es **dirección, seguida de nombre**.

`getent hosts` llegó a mostrar IPv6 locales. No demostraba por sí solo un fallo: consulta las fuentes configuradas en NSS. `getent ahostsv4` permite centrarse en IPv4; STREAM, DGRAM y RAW no son tres máquinas diferentes.

## Paso 4. Reparar DNS

```bash
cat /etc/resolv.conf
host archive.debian.org 10.8.12.49
host archive.debian.org 10.8.12.50
host archive.debian.org 10.8.12.47
host archive.debian.org 10.8.8.8
host archive.debian.org 10.8.8.9
```

APT no resolvía nombres. Se probaron los DNS individualmente: los tres `10.8.12.x` agotaron el tiempo; `10.8.8.8` y `10.8.8.9` sí contestaron consultas DNS. Un ping sin respuesta a un DNS no demuestra que su servicio DNS esté caído.

Se conservaron las cinco direcciones a petición del alumno, poniendo primero las que respondían:

```text
domain udc.pri
search udc.pri
nameserver 10.8.8.8
nameserver 10.8.8.9
nameserver 10.8.12.49
nameserver 10.8.12.50
nameserver 10.8.12.47
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
