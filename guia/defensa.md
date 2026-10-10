# Guion de demostración de lo realizado

[Volver al índice](../README.md)

La evaluación se prepara para explicar y trabajar sobre la máquina. Este guion usa consultas; no requiere reinstalar el sistema ni repetir las purgas.

## 1. Presentar la VM

```bash
cat /etc/debian_version
uname -r
systemctl get-default
```

Explicar origen en Debian 10.4, saltos sucesivos hasta 13.7 y uso actual sin escritorio. La arquitectura observada fue amd64.

## 2. Explicar red y DNS — a), f), g)

```bash
ip -br addr
ip route
getent ahostsv4 deb.debian.org
```

Relacionar las dos IP con sus redes `/23`, identificar la ruta por defecto y separar DNS de routing. Explicar cómo se añadió y retiró la IP lógica de f), y cómo `ip route get` verificó la selección de ruta en g). Si se pide repetir una modificación, seguir el apartado correspondiente y dejar la interfaz en su estado original.

## 3. Explicar systemd y las medidas — c), d), h)

```bash
systemctl --failed --no-pager
systemd-analyze time
systemd-analyze critical-chain multi-user.target
```

Explicar `@` frente a `+`, activación frente a CPU y paralelismo. Indicar qué se retiró por no utilizar escritorio, qué máscaras siguen aplicadas y qué concesión de protección supone AppArmor bloqueado. No afirmar que se alcanzaron 10–12 segundos.

## 4. Mostrar una incidencia investigada — e)

```bash
systemctl status logrotate.service --no-pager -l
journalctl -u logrotate.service --no-pager -n 20
```

Explicar la llamada residual a CUPS y cómo se contrastó con paquetes/configuración. No confundir una tarea finalizada con éxito con un servicio averiado por estar `inactive`.

## 5. Demostrar la funcionalidad original — i)

```bash
systemctl is-enabled lsi-companion.service
systemctl status lsi-companion.service --no-pager -l
systemctl cat lsi-companion.service
journalctl -b -u lsi-companion.service --no-pager -n 20
```

Desde Telegram, enviar `/estado`, `/disco` y `/curiosidad`. Explicar el usuario sin privilegios, dónde están los secretos sin mostrarlos, la fuente externa, el mecanismo de consultas salientes y la comparación con cron.

## Preguntas que conviene poder responder

| Pregunta | Idea esencial |
| --- | --- |
| ¿Por qué .49 pertenece a una red .48? | El prefijo es /23 |
| ¿Qué diferencia hay entre update y full-upgrade? | Índices frente a instalación/resolución de transiciones |
| ¿Enabled significa running? | No; habilitación y ejecución son estados diferentes |
| ¿Se suman todas las filas de blame? | No, hay tareas en paralelo |
| ¿Borrar initramfs de respaldo acelera el arranque? | Libera espacio; esas copias no se cargaban |
| ¿Network.target garantiza Internet? | No; el programa debe gestionar la conectividad |
| ¿El bot es una IA conversacional? | No, reconoce palabras clave y consulta APIs; se desarrolló con ayuda de IA |
| ¿Una caída del bot bloquea SSH? | No, el bot definitivo no participa en SSH |

Sudo, el inventario de conexiones de j) y los apartados posteriores siguen con los límites indicados en el índice. No presentar como terminados ejercicios pendientes.
