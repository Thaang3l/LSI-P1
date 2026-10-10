# d) Medir los tiempos de arranque

[Volver al índice](../README.md)

## Paso 1. Obtener las medidas

```bash
systemd-analyze time
systemd-analyze blame --no-pager
systemd-analyze critical-chain multi-user.target
```

Al principio se consultó `critical-chain graphical.target`; después se usó `multi-user.target`, de acuerdo con el estado sin escritorio.

| Medición compartida | Kernel/fase inicial | Userspace | Total mostrado |
| --- | ---: | ---: | ---: |
| Primera medición | 6,564 s | 39,707 s | 46,272 s |
| Una medida posterior a la limpieza | 6,389 s | 10,031 s | 16,421 s |
| Último informe revisado, 10 de octubre | 6,891 s | 10,465 s | 17,356 s |

Son observaciones de diferentes arranques, no una comparación controlada que aísle cada cambio. Las pequeñas diferencias al sumar son de redondeo. No se mostraron tiempos separados de firmware ni GRUB: el total no equivale necesariamente a pulsar el botón y cronometrar hasta el login.

## Paso 2. Interpretar blame

`blame` ordena duraciones de activación. No mide cuánto tiempo se mantiene ejecutándose un servicio ni su consumo total de CPU. No se suman todas las filas: existen tareas en paralelo.

En la primera medida destacaban AppArmor (25,674 s), fwupd (4,715 s), ifupdown-pre (4,560 s) y el dispositivo raíz (4,435 s). En arranques posteriores sus duraciones variaron. No se puede prometer ahorrar 25 segundos simplemente desactivando AppArmor.

## Paso 3. Interpretar la cadena crítica actual

Última cadena compartida:

```text
multi-user.target @10.399s
└─ssh.service @9.861s +537ms
  └─network.target @9.805s
    └─networking.service @6.378s +3.417s
      └─local-fs.target @6.365s
        └─tmp.mount @6.327s +36ms
          └─swap.target @6.309s
            └─dev-sda5.swap @6.195s +106ms
              └─dev-sda5.device @6.186s
```

- `@`: instante respecto al inicio del espacio de usuario.
- `+`: duración de la activación indicada.
- `networking` empezó a 6,378 s y tardó unos 3,417 s.
- La swap tardó 106 ms en activarse; el instante del dispositivo no equivale al tiempo que consumió un proceso de swap.
- La cadena muestra relaciones temporales de dependencias; no es una prueba de que quitar una fila reduzca exactamente ese tiempo.

## Paso 4. Separar medición y optimización

Las decisiones que quedaron aplicadas están en [h)](h-limpieza.md). Se redujo notablemente el tiempo respecto a la primera medida, pero la meta personal de 10–12 s **no se alcanzó**. Se acordó continuar con la práctica y dejar la optimización para el final.

## Para la defensa

«Mido kernel y userspace con `time`, localizo activaciones lentas con `blame` y estudio dependencias con `critical-chain`. Comparo varios arranques y verifico que SSH, red y swap siguen funcionando; no confundo espacio liberado con segundos ahorrados.»
