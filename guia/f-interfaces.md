# f) Segunda interfaz y dirección lógica adicional

[Volver al índice](../README.md)

## Paso 1. Identificar los parámetros de ens34

```bash
ip -details addr show dev ens34
ip route
cat /etc/network/interfaces
```

Se observó `ens34` con IP `10.11.51.56/23`, broadcast `10.11.51.255`, MTU 1500 y flags `UP,LOWER_UP`. La configuración persistente figura en el apartado a). El alias alternativo `enp2s2` no es una segunda tarjeta física.

## Paso 2. Añadir una dirección temporal

Operación realizada como root:

```bash
ip addr add 192.0.2.56/32 dev ens34 label ens34:0
ip -4 addr show dev ens34
```

La salida mostró simultáneamente `10.11.51.56/23` y `192.0.2.56/32`. `ens34:0` es una etiqueta de la dirección adicional: no se creó una tarjeta de red nueva. `/32` identifica una sola dirección y no una red local completa.

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

La consulta final mostró solo `10.11.51.56/23`. No se añadió la dirección de prueba a `/etc/network/interfaces`.

## Alcance y defensa

Se identificaron los parámetros y se demostró el alta, prueba y retirada de la dirección lógica adicional. El enunciado también pide cambiar los principales parámetros de la segunda interfaz: no consta una prueba separada de cambio de MTU/MAC u otros parámetros. No dar por realizadas operaciones que no aparecen en las salidas.

«Una interfaz puede tener varias IP. Añadir una dirección hace que el kernel la trate como local, pero no publica por sí solo una ruta hacia ella en el resto de la red.»
