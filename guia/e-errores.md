# e) Analizar errores del journal con ayuda de IA

[Volver al índice](../README.md)

## Paso 1. Consultar errores del arranque

```bash
journalctl -p 3 -b --no-pager
```

Ejecutar como root para disponer de los registros del sistema. Con el usuario normal apareció un aviso de permisos y «No entries»; eso no demostraba ausencia de errores.

Se observaron mensajes de SMBus virtual, etiquetas ausentes en reglas ALSA y un fallo de `logrotate.service` relacionado con CUPS. No se asumió que todos fueran fallos graves ni que hubiera que instalar servicios eliminados.

## Paso 2. Investigar el fallo de logrotate

```bash
journalctl -u logrotate.service -b --no-pager -n 80
systemctl status logrotate.service --no-pager -l
cat /etc/logrotate.d/cups*
dpkg -l 'cups*'
ls -l /var/lib/logrotate/status
```

La configuración de rotación conservaba un bloque `postrotate` que intentaba reiniciar CUPS. El servicio no estaba instalado; varios paquetes figuraban como `rc`: binarios retirados, configuración residual presente. El registro indicaba un error al ejecutar ese bloque sobre `/var/log/cups/*log`.

**Causa identificada:** configuración residual que llamaba a un servicio eliminado. No era necesario reinstalar el sistema de impresión para resolverla.

## Paso 3. Apartar la configuración residual

Se retiró de `/etc/logrotate.d/` la configuración de CUPS y se conservó en `/root/respaldo-logrotate/`. La conversación no conserva el nombre concreto final del archivo: antes de repetir esta operación en otra VM se debe identificarlo con el listado anterior.

No se vació `/var/log` ni se eliminaron todos los archivos de configuración de logrotate.

## Paso 4. Validar la corrección

```bash
logrotate --debug /etc/logrotate.conf
systemctl start logrotate.service
systemctl status logrotate.service --no-pager -l
```

El modo `--debug` ayuda a revisar sin realizar la rotación. La ejecución real posterior terminó con `status=0/SUCCESS`. `inactive (dead)` al finalizar era normal: esta tarea no permanece ejecutándose continuamente.

Hubo además un aviso antiguo sobre permisos del archivo de estado. La consulta posterior mostró `root:root` y modo `640`; no se atribuye esa situación a un comando no registrado.

## Paso 5. Contrastar la explicación de la IA

| Propuesta/interpretación | Contraste y decisión |
| --- | --- |
| Reinstalar CUPS por aparecer un error | Se comprobó que el fallo procedía de una configuración residual; se retiró esa configuración |
| `inactive` significa fallo | El proceso había terminado con éxito; no había que «arreglarlo» por estar parado |
| Todo error del kernel requiere intervención | Se consideró el contexto virtual; no se modificó hardware por el aviso SMBus |
| Error de enlaces de ssa implica bucle demostrado | `readlink` resolvía las rutas y la unidad ejecutaba correctamente; causa no confirmada |
| «No entries» demuestra journal limpio | Primero se revisaron los permisos del usuario que ejecutaba la consulta |

Los avisos ALSA y SMBus no tienen una corrección específica demostrada en esta guía. Las sugerencias de la IA se trataron como hipótesis que había que comprobar.

## Para la defensa

Presentar la secuencia: mensaje original → unidad implicada → archivo residual → comprobación de paquetes → corrección limitada → nueva ejecución correcta. Distinguir los errores históricos del estado actual.
