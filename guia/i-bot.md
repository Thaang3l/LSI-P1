# i) Servicio original: compañero de VM en Telegram

[Volver al índice](../README.md)

## Objetivo y resultado

La funcionalidad definitiva envía una curiosidad por Telegram al arrancar la VM y responde a consultas sencillas sobre sus recursos. El alumno confirmó que funciona; también compartió el servicio habilitado y sus registros del arranque.

**SSH sigue en el puerto 22 sin depender del bot.** Este proyecto no es un mecanismo de autorización de acceso ni ejecuta órdenes recibidas por Telegram. No se incluyen las pruebas del proyecto descartado como pasos a repetir.

## Paso 1. Definir la idea con ayuda de IA

Se usó el asistente para explorar alternativas, desarrollar el script Python y la unidad de systemd, y probar la lógica. El objetivo final fue mantener una interacción sencilla con la VM, sin depender de una interfaz gráfica.

La IA se utilizó **durante el desarrollo**. En ejecución el programa consulta APIs y reconoce palabras clave; no llama a un LLM para inventar datos ni para interpretar libremente todas las preguntas.

## Paso 2. Crear el bot y vincular la cuenta

Se creó un bot con BotFather y se obtuvo un token. El token se renovó antes del despliegue definitivo y se introdujo mediante lectura oculta; nunca debe copiarse al repositorio ni a capturas públicas.

Se vinculó la cuenta personal mediante un código aleatorio, un mensaje privado al bot y confirmación local. Se conservaron los identificadores numéricos de usuario, chat y bot en un archivo restringido. Son identificadores usados para autorizar respuestas, no datos que deban fijarse en el código público.

Estado final:

| Archivo en Debian | Función |
| --- | --- |
| `/etc/lsi-companion/telegram-token` | Token privado; root, permisos 600 |
| `/etc/lsi-companion/administrador.json` | Identificadores de la cuenta vinculada; root, permisos 600 |
| `/usr/local/libexec/lsi-companion.py` | Programa instalado |
| `/etc/systemd/system/lsi-companion.service` | Servicio que lo ejecuta |
| `/var/lib/lsi-companion/estado.json` | Último arranque notificado, último dato e índice de mensajes procesados |

Los secretos ya existen en esta VM. Los pasos posteriores no son un instalador completo para una máquina nueva sin vinculación. El estado y las credenciales se excluyen de Git.

## Paso 3. Instalar el programa y su unidad

El instalador creó el usuario de sistema `lsi-companion`, sin inicio de sesión interactivo, e instaló el programa y la unidad. El repositorio publica la versión final, no los instaladores de migración ya retirados.

Equivalencia de la copia de archivos finales, desde una copia del repositorio y como root:

```bash
install -o root -g root -m 644 companion/bot.py /usr/local/libexec/lsi-companion.py
install -o root -g root -m 644 companion/lsi-companion.service /etc/systemd/system/lsi-companion.service
systemd-analyze verify /etc/systemd/system/lsi-companion.service
systemctl daemon-reload
systemctl enable --now lsi-companion.service
```

Este bloque sirve para entender/reponer la instalación **si el usuario y las credenciales ya están creados**, no es necesario ejecutarlo de nuevo para demostrar el servicio. Si se reemplaza el código con el servicio ya activo, el cambio requiere reiniciarlo.

Código: [bot.py](../companion/bot.py). Unidad completa: [lsi-companion.service](../companion/lsi-companion.service).

## Paso 4. Entender cómo arranca y permanece funcionando

| Directiva | Explicación en nuestra unidad |
| --- | --- |
| `After=network.target` | Ordena el inicio después de ese target; no garantiza Internet ni obliga por sí sola a activarlo |
| `Type=simple` | systemd supervisa el proceso Python; que esté activo no prueba que Telegram ya esté listo |
| `ExecStart=/usr/bin/python3 -I ...` | Ejecuta el programa usando Python en modo aislado |
| `User` / `Group` | El bot no se ejecuta como root |
| `LoadCredential` | systemd entrega al servicio copias accesibles de las credenciales sin poner el token en la orden de ejecución |
| `StateDirectory` | Proporciona almacenamiento persistente para el estado del bot |
| `Restart=on-failure` y `RestartSec=15` | Intenta recuperar el proceso si falla; no transforma una configuración incorrecta en correcta |
| `WantedBy=multi-user.target` | `enable` conecta su arranque al target de uso normal |
| `NoNewPrivileges`, `ProtectSystem`, etc. | Restringen permisos y escritura del proceso |

Se dejó que empezara temprano, después del orden de red existente. No se añadió una espera fija a Internet: el programa reintenta si Telegram no está disponible. Un fallo del bot no cambia la configuración de SSH ni impide usarlo.

## Paso 5. Obtener una curiosidad externa

Flujo implementado:

1. Leer el identificador del arranque en `/proc/sys/kernel/random/boot_id`.
2. Compararlo con el último guardado; si ya se notificó ese arranque, no repetir el saludo por un mero reinicio del servicio.
3. Consultar `https://uselessfacts.jsph.pl/api/v2/facts/random?language=en`.
4. Validar la respuesta e intentar evitar la repetición inmediata del último dato.
5. Solicitar traducción inglés → español a MyMemory y enviar el texto con enlace a la fuente.
6. Guardar el identificador del arranque tras enviar el mensaje.

No existe una lista fija de 20 curiosidades en la versión final. Si no se puede traducir, se muestra el original en inglés y se indica el motivo general. Si no se obtiene un dato, se envía un aviso y continúan disponibles las consultas de recursos. La traducción recibe únicamente el texto público del dato, no el estado de la VM ni el token de Telegram.

La fuente externa y la traducción pueden contener errores; se adjunta el enlace para poder contrastar. El programa limita tiempos de espera y tamaño de respuestas. Si se pierde la confirmación de una petición enviada, o el proceso falla antes de guardar el estado, todavía puede haber una duplicación: no se ha implementado una garantía distribuida de «exactamente una vez».

Fuentes: [API de Useless Facts](https://uselessfacts.jsph.pl/), [MyMemory](https://mymemory.translated.net/doc/spec.php), [Telegram Bot API](https://core.telegram.org/bots/api).

## Paso 6. Consultar la máquina desde el móvil

| Mensaje | Respuesta |
| --- | --- |
| `/estado` o «¿cómo estás?» | Nombre, tiempo encendida, kernel, CPU, memoria y disco |
| `/uso`, «memoria» o «CPU» | Muestra breve de CPU, RAM y swap |
| `/disco` o «¿cuánto espacio queda?» | Capacidad, uso y espacio disponible de `/` |
| `/curiosidad` | Nueva consulta a la fuente externa |
| `/ayuda` | Opciones disponibles |

La interfaz usa botones y palabras clave. El bot solo responde a mensajes privados cuyo usuario y chat coinciden con la vinculación. No usa `eval`, no transforma mensajes en órdenes de shell y no permite apagar la máquina por escribir una orden.

Se usa **long polling**: el bot consulta Telegram y espera mensajes mediante conexiones salientes HTTPS. No necesita un puerto entrante nuevo ni un servidor web público.

## Paso 7. Explicar de dónde salen las medidas

| Medida | Fuente y alcance |
| --- | --- |
| Tiempo encendida | `/proc/uptime` |
| Identificador de arranque | `/proc/sys/kernel/random/boot_id` |
| RAM | `/proc/meminfo`; estima uso como total menos disponible |
| Swap | Total menos libre en `/proc/meminfo` |
| CPU | Diferencia entre dos lecturas de `/proc/stat` separadas por un segundo |
| Disco | `shutil.disk_usage('/')`; no inventario de todos los discos |

Se distingue CPU ocupada, espera de E/S y tiempo cedido al hipervisor. Memoria disponible no es igual a memoria totalmente vacía: Linux utiliza caché. El resumen no comprueba la salud de todos los servicios y no debe presentarse como una auditoría completa.

## Paso 8. Comprobar el servicio y su arranque automático

```bash
systemctl is-enabled lsi-companion.service
systemctl status lsi-companion.service --no-pager -l
systemd-analyze critical-chain lsi-companion.service
journalctl -b -u lsi-companion.service --no-pager -n 20
```

Salida aportada:

```text
enabled
lsi-companion.service @9.826s
└─network.target @9.805s
  └─networking.service @6.378s +3.417s
```

El registro muestra el inicio del servicio a las 00:43:04 y «Compañero listo» a las 00:43:07. `@9.826s` es el instante en userspace, no la duración del programa. El alumno confirmó que el bot funciona tras la instalación y la limpieza. Estos datos acreditan la activación en el arranque actual; no se adjunta una captura independiente de cada mensaje de Telegram.

Para la demostración: mostrar el estado, escribir `/estado`, `/disco` y `/curiosidad` desde la cuenta vinculada, y relacionar una respuesta con una consulta local. No hace falta reiniciar durante la defensa salvo que se solicite y se disponga de acceso de recuperación.

## Paso 9. Pruebas y fallos contemplados

Se ejecutaron **12 pruebas locales** del código con APIs simuladas: autorización por usuario/chat privado, reconocimiento de preguntas, cálculos de recursos, repetición de datos, fuente no disponible, respuesta malformada, cuota de traducción y control de notificación por arranque.

```bash
python3 -m unittest discover -s companion -p test_bot.py -v
```

Esas pruebas no sustituyen la conexión real: el alumno la comprobó desde la VM y confirmó funcionamiento. Si el bot deja de responder, revisar su journal y la resolución/conectividad antes de reinstalarlo. Los fallos al iniciar son gestionados por systemd; durante la ejecución se reintentan los errores de Telegram.

## Paso 10. Comparar con cron

| Aspecto | Servicio de systemd | Cron |
| --- | --- | --- |
| Al arrancar | Habilitación y dependencias de unidades | `@reboot` podría lanzar un programa |
| Recuperación | Supervisa el proceso y puede reiniciarlo | Por sí solo no supervisa un proceso persistente |
| Logs y estado | Journal y `systemctl` | Hay que preparar la salida y su gestión |
| Consultas interactivas | El proceso permanece esperando mensajes | Un trabajo periódico añade demora o exige lanzar otro proceso permanente |
| Uso ocasional | Mantiene memoria para Python; el polling espera entre eventos | Un script breve periódico puede ser preferible si solo envía un informe cada cierto tiempo |

Para un único aviso de arranque, cron podría ser suficiente con manejo explícito de red, credenciales y errores. Para **este bot que recibe preguntas**, se eligió systemd. No se instaló además una tarea cron que duplique el proceso. No se ha medido un ahorro exacto de recursos de una alternativa frente a la otra.

## Para la defensa

«Diseñé con ayuda de IA un servicio residente de solo lectura. Arranca después del orden de red, consulta una fuente externa, notifica el arranque y responde a mi cuenta de Telegram. Se ejecuta sin root y con credenciales separadas del código. Systemd me permite supervisarlo y consultar sus registros. La IA ayudó a construirlo, pero no genera las curiosidades durante su ejecución.»
