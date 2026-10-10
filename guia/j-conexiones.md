# j) Conexiones abiertas: siguiente apartado

[Volver al índice](../README.md)

**Pendiente de recibir e interpretar la salida de la VM.** Los siguientes pasos se han propuesto; no se inventa un inventario de conexiones.

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

**Siguiente acción en la práctica:** ejecutar ambos comandos y analizar las salidas reales. Este apartado no está terminado.
