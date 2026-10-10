# g) Rutas del sistema y alta de una ruta estática

[Volver al índice](../README.md)

## Paso 1. Leer la tabla

```bash
ip route
```

Rutas habituales observadas:

```text
default via 10.11.48.1 dev ens33 onlink
10.11.48.0/23 dev ens33 proto kernel scope link src 10.11.49.56
10.11.50.0/23 dev ens34 proto kernel scope link src 10.11.51.56
```

Las dos redes `/23` están conectadas directamente. `default` se utiliza cuando no existe una ruta más específica. `src` indica la dirección de origen preferida. La ruta `169.254.0.0/16` que aparecía inicialmente dejó de figurar tras retirar el script de avahi-autoipd.

## Paso 2. Añadir una ruta de ejemplo

```bash
ip route add 198.51.100.0/24 via 10.11.48.1 dev ens33
ip route
```

El sistema incorporó la ruta hacia ese bloque de documentación a través del gateway ya alcanzable por `ens33`.

## Paso 3. Comprobar qué ruta elegiría el kernel

```bash
ip route get 198.51.100.10
```

Salida obtenida:

```text
198.51.100.10 via 10.11.48.1 dev ens33 src 10.11.49.56 uid 0
    cache
```

Es una consulta de selección de ruta, no un envío de paquetes ni una prueba de que exista ese destino. La ruta `/24` es más específica que la ruta por defecto; en este ejemplo ambas usan el mismo gateway, por lo que no se demuestra un cambio de camino físico.

## Paso 4. Entender la persistencia

La ruta se añadió con `ip route`, sin una configuración persistente documentada. No aparece en las tablas posteriores compartidas tras reiniciar. No se afirma que se ejecutara un borrado manual concreto.

Si se repite la demostración, la operación inversa es:

```bash
ip route del 198.51.100.0/24 via 10.11.48.1 dev ens33
```

## Para la defensa

Explicar destino/prefijo, siguiente salto, interfaz y dirección de origen. Una ruta estática es una decisión configurada administrativamente; «estática» no significa que persista automáticamente tras reiniciar.
