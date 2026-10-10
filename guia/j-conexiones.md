# j) Conexiones abiertas y servicios en escucha

[Volver al índice](../README.md)

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

Había dos conexiones establecidas hacia `10.11.49.56:22` desde `10.30.13.239`, con puertos cliente `63418` y `63441`. Python, PID 582, mantenía otra conexión hacia `149.154.166.110:443`. Es compatible con el bot, pero el listado no verificó su comando ni la identidad del destino: el puerto 443 por sí solo no demuestra Telegram o HTTPS.

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
