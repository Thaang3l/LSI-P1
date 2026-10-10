# k) Monitorización de procesos, recursos y conexiones

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
