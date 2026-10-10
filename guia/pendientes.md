# Apartados pendientes

[Volver al índice](../README.md)

Esta lista organiza el trabajo restante. No son resultados ejecutados ni una configuración para aplicar de golpe.

## Primera parte

| Apartado | Qué falta |
| --- | --- |
| a | Configurar y comprobar sudo desde la cuenta normal; cerrar la revisión de permisos |
| c | Si se retoma, aclarar la personalización `ssa.service`; no fue reparada ni eliminada |
| f | Confirmar con el alcance del enunciado si basta la dirección lógica o falta demostrar cambios en otros parámetros de ens34 |
| l | Verificar con salidas la política permanente confirmada por el alumno; incorporar los orígenes autorizados de VPN del compañero y Wi-Fi UDC cuando se conozcan; probar acceso desde la VM compañera y revisar rotación del registro nuevo |

La bitácora del 10/10/2026 aporta el inventario de conexiones de [j)](j-conexiones.md), la monitorización de [k)](k-monitorizacion.md) y la prueba de logs locales de [m)](m-logs-locales.md). Ya no se consideran tareas sin realizar.

En [l)](l-tcp-wrappers.md), se verificaron libwrap en sshd-session, las simulaciones, un rechazo real desde loopback y su registro. La política final permite `10.30.13.239` y `10.11.49.57`; el alumno confirmó su aplicación, pero falta una comprobación posterior de esos archivos y conexiones. Las IP VPN pueden cambiar. Los timers del ensayo se retiraron: no contar con ellos como recuperación actual.

## Segunda parte de la práctica 1

1. Configurar servidor/cliente NTPSec con un compañero.
2. Cruzar los equipos como servidor/cliente de rsyslog.
3. Presentar la configuración de rsyslog a una IA para una revisión de seguridad y contrastar sus propuestas.
4. Revisar reducción del espacio ocupado; aprovechar las mediciones previas, sin dar el apartado por completo solo por haber borrado copias.
5. Instalar Splunk y realizar las consultas, ingestión de logs, visualizaciones y pruebas solicitadas.

La IP comunicada de la VM compañera es `10.11.49.57`. Falta acordar los roles y comprobar la conectividad necesaria para los ejercicios compartidos. No se ha acreditado instalación de Splunk ni ingestión de journald o Apache. El registro local de m) y el archivo de denegaciones de l) no sustituyen la configuración de rsyslog entre máquinas.

## Criterio para actualizar los apuntes

Añadir pasos ejecutados cuando el alumno lo solicite. Distinguir siempre «comprobado con salida», «confirmado por el alumno» y «pendiente/propuesto». No incluir contraseñas, tokens ni tratar una prueba revertida como configuración actual.
