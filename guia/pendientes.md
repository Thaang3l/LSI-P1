# Apartados pendientes

[Volver al índice](../README.md)

Esta lista organiza el trabajo restante. No son resultados ejecutados ni una configuración para aplicar de golpe.

## Primera parte

| Apartado | Qué falta |
| --- | --- |
| a | Configurar y comprobar sudo desde la cuenta normal; cerrar la revisión de permisos |
| c | Si se retoma, aclarar la personalización `ssa.service`; no fue reparada ni eliminada |
| f | Confirmar con el alcance del enunciado si basta la dirección lógica o falta demostrar cambios en otros parámetros de ens34 |
| j | Recibir y explicar las conexiones reales de `ss` |
| k | Monitorizar procesos, recursos y conexiones en tiempo real |
| l | Estudiar filtrado con tcp-wrappers y registro de accesos denegados; verificar primero compatibilidad real del servicio SSH instalado |
| m | Probar explícitamente el registro local con rsyslog y journald |

En l), la existencia de `/etc/hosts.allow` o `/etc/hosts.deny` no demuestra que un servicio los consulte. No se ha aplicado esa política ni debe suponerse que ya esté funcionando.

## Segunda parte de la práctica 1

1. Configurar servidor/cliente NTPSec con un compañero.
2. Cruzar los equipos como servidor/cliente de rsyslog.
3. Presentar la configuración de rsyslog a una IA para una revisión de seguridad y contrastar sus propuestas.
4. Revisar reducción del espacio ocupado; aprovechar las mediciones previas, sin dar el apartado por completo solo por haber borrado copias.
5. Instalar Splunk y realizar las consultas, ingestión de logs, visualizaciones y pruebas solicitadas.

Faltan las IP y el acuerdo de roles del compañero para los ejercicios compartidos. No se ha acreditado instalación de Splunk ni ingestión de journald o Apache.

## Criterio para actualizar los apuntes

Añadir pasos ejecutados cuando el alumno lo solicite. Distinguir siempre «comprobado con salida», «confirmado por el alumno» y «pendiente/propuesto». No incluir contraseñas, tokens ni tratar una prueba revertida como configuración actual.
