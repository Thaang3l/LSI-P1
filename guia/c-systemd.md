# c) Secuencia de arranque, targets y unidades

[Volver al índice](../README.md)

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
