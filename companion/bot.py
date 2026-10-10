#!/usr/bin/python3
"""Compañero de VM: curiosidades y consultas de solo lectura por Telegram."""
import json
import html
import os
import re
import shutil
import socket
import time
import unicodedata
import urllib.request
import urllib.parse
from pathlib import Path

STATE = Path('/var/lib/lsi-companion/estado.json')
FACT_API = 'https://uselessfacts.jsph.pl/api/v2/facts/random?language=en'
KEYBOARD = {'keyboard': [['/estado', '/uso'], ['/disco', '/curiosidad'], ['/ayuda']],
            'resize_keyboard': True}


def normalizar(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                   if unicodedata.category(c) != 'Mn')


def autorizado(msg, admin):
    return (msg.get('from', {}).get('id') == admin['user_id']
            and msg.get('chat', {}).get('id') == admin['chat_id']
            and msg.get('chat', {}).get('type') == 'private')


def intencion(text):
    words = set(re.findall(r'[a-z]+', normalizar(text)))
    if words & {'curiosidad', 'curiosidades', 'dato', 'cuentame'}: return 'curiosidad'
    if words & {'disco', 'espacio', 'ocupacion', 'almacenamiento'}: return 'disco'
    if words & {'memoria', 'ram', 'cpu', 'procesador', 'uso', 'consumo', 'carga'}: return 'uso'
    if words & {'estado', 'estas', 'arranque', 'encendida', 'uptime', 'hola', 'funcionas'}: return 'estado'
    return 'ayuda'


def json_externo(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/json',
                                              'User-Agent': 'LSICompanion/2.0'})
    with urllib.request.urlopen(req, timeout=6) as r:
        raw = r.read(65537)
    if len(raw) > 65536:
        raise ValueError('Respuesta demasiado grande')
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError('Respuesta incorrecta')
    return result


def traducir(original):
    # Solo se envía el texto público de la curiosidad, nunca datos de la VM.
    if len(original.encode('utf-8')) > 500:
        return original, False
    try:
        params = urllib.parse.urlencode({'q': original, 'langpair': 'en|es'})
        data = json_externo('https://api.mymemory.translated.net/get?' + params)
        if str(data.get('responseStatus')) != '200' or data.get('quotaFinished'):
            raise ValueError('Traducción no disponible')
        translated = data.get('responseData', {}).get('translatedText')
        if not isinstance(translated, str) or not translated.strip() or len(translated) > 1800:
            raise ValueError('Traducción incorrecta')
        translated = html.unescape(translated).strip()
        if translated == original:
            return original, False
        return translated, True
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return original, False


def elegir_curiosidad(anterior=None):
    try:
        data = None
        for _ in range(2):
            data = json_externo(FACT_API)
            ident, original = data.get('id'), data.get('text')
            if (not isinstance(ident, str) or not re.fullmatch(r'[A-Za-z0-9-]{1,100}', ident)
                    or not isinstance(original, str) or not 1 <= len(original.strip()) <= 1500
                    or data.get('language') != 'en'):
                raise ValueError('Dato no válido')
            if ident != anterior:
                break
        if ident == anterior:
            return anterior, 'La fuente ha repetido el último dato. Pídeme /curiosidad de nuevo en un momento.'
        text, translated = traducir(html.unescape(original).strip())
        aviso = 'Traducción automática al español.' if translated else 'Texto original en inglés; traducción no disponible.'
        return ident, ('🧠 Curiosidad de Useless Facts\n\n' + text + '\n\n' + aviso
                       + '\nFuente: https://uselessfacts.jsph.pl/api/v2/facts/' + ident)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return anterior, ('No he podido obtener la curiosidad de Internet. Prueba /curiosidad más tarde. '
                          'Puedes seguir consultando /estado, /uso y /disco.')


def memoria():
    datos = {}
    for linea in Path('/proc/meminfo').read_text().splitlines():
        k, value = linea.split(':', 1)
        datos[k] = int(value.split()[0])
    total = datos['MemTotal']
    usada = total - datos['MemAvailable']
    swap = datos['SwapTotal'] - datos['SwapFree']
    return (f'RAM: {usada / 1024:.0f} / {total / 1024:.0f} MiB ({usada / total:.0%})\n'
            f'RAM disponible: {datos["MemAvailable"] / 1024:.0f} MiB\n'
            f'Swap usada: {swap / 1024:.0f} / {datos["SwapTotal"] / 1024:.0f} MiB')


def leer_cpu():
    # guest y guest_nice ya están incluidos en user y nice: no sumarlos otra vez.
    ticks = [int(x) for x in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
    return ticks


def cpu_delta(a, b):
    d = [max(0, y - x) for x, y in zip(a, b)]
    total = sum(d)
    if not total: return 0.0, 0.0, 0.0
    return (100 * sum(d[i] for i in (0, 1, 2, 5, 6)) / total,
            100 * d[4] / total, 100 * d[7] / total)


def uso():
    a = leer_cpu()
    time.sleep(1)
    busy, wait, steal = cpu_delta(a, leer_cpu())
    return (f'⚙️ CPU ocupada: {busy:.1f}% (muestra de 1 s)\n'
            f'Espera de E/S: {wait:.1f}% · Espera del hipervisor: {steal:.1f}%\n' + memoria())


def disco():
    d = shutil.disk_usage('/')
    gib = 1024 ** 3
    return (f'💾 Disco de /\nUsado: {d.used / gib:.2f} GiB\n'
            f'Libre disponible: {d.free / gib:.2f} GiB\nTotal: {d.total / gib:.2f} GiB\n'
            f'Ocupación: {d.used / d.total:.0%}')


def estado():
    minutos = int(float(Path('/proc/uptime').read_text().split()[0])) // 60
    dias, rem = divmod(minutos, 1440)
    horas, mins = divmod(rem, 60)
    return (f'🤖 Estoy aquí: {socket.gethostname()}\n'
            f'Encendida: {dias} días, {horas} h, {mins} min\n'
            f'Kernel: {os.uname().release}\n\n' + uso() + '\n\n' + disco()
            + '\n\nEstas son medidas de recursos; no comprueban todos los servicios.')


def respuesta(text, state):
    accion = intencion(text)
    if accion == 'curiosidad':
        n, text = elegir_curiosidad(state.get('ultima_curiosidad'))
        state['ultima_curiosidad'] = n
        return text
    if accion == 'estado': return estado()
    if accion == 'uso': return uso()
    if accion == 'disco': return disco()
    return ('🤖 Soy tu compañero de VM.\n/estado — resumen\n/uso — CPU, RAM y swap\n'
            '/disco — ocupación y espacio libre\n/curiosidad — otro dato\n'
            'También entiendo frases como «¿cómo estás?» o «¿cuánto disco queda?».\n'
            'Reconozco palabras clave; no soy un chat de IA ni ejecuto órdenes del sistema.')


class Telegram:
    def __init__(self, token): self.token = token

    def api(self, metodo, datos=None):
        req = urllib.request.Request('https://api.telegram.org/bot' + self.token + '/' + metodo,
            data=json.dumps(datos or {}).encode(), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=35) as r: data = json.load(r)
            if data.get('ok') is not True: raise ValueError()
            return data['result']
        except Exception:
            raise RuntimeError('Telegram no disponible; se reintentará.') from None


def guardar(state):
    temp = STATE.with_suffix('.tmp')
    with open(temp, 'w') as f:
        json.dump(state, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, STATE)


def notificar_arranque(tg, admin, state, boot, persistir=guardar):
    if state.get('boot_notificado') == boot:
        return
    n, dato = elegir_curiosidad(state.get('ultima_curiosidad'))
    tg.api('sendMessage', {'chat_id': admin['chat_id'],
        'text': '🌅 ¡He arrancado! Soy ' + socket.gethostname() + '.\n\n' + dato
                + '\n\nEscríbeme /estado para ver cómo estoy.', 'reply_markup': KEYBOARD})
    state.update(boot_notificado=boot, ultima_curiosidad=n)
    persistir(state)


def main():
    import fcntl
    os.umask(0o077)
    lock = open(STATE.parent / 'bot.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    creds = Path(os.environ['CREDENTIALS_DIRECTORY'])
    admin = json.loads((creds / 'administrador').read_text())
    tg = Telegram((creds / 'token').read_text().strip())
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if tg.api('getMe')['id'] != admin['bot_id']: raise ValueError('Bot incorrecto')
    if tg.api('getWebhookInfo').get('url'): raise ValueError('Existe un webhook activo')
    minimo_fecha = time.time() - float(Path('/proc/uptime').read_text().split()[0])
    print('Compañero listo. Solo responde a la cuenta privada vinculada.', flush=True)
    while True:
        try:
            notificar_arranque(tg, admin, state, boot)
            for evento in tg.api('getUpdates', {'offset': state.get('offset', 0), 'timeout': 25,
                                                'allowed_updates': ['message']}):
                msg = evento.get('message', {})
                if (autorizado(msg, admin) and isinstance(msg.get('text'), str)
                        and msg.get('date', 0) >= minimo_fecha):
                    try:
                        text = respuesta(msg['text'][:2000], state)
                    except (OSError, ValueError, KeyError):
                        text = 'No he podido leer esa medida. El acceso SSH sigue funcionando.'
                    tg.api('sendMessage', {'chat_id': admin['chat_id'], 'text': text,
                                          'reply_markup': KEYBOARD})
                state['offset'] = evento['update_id'] + 1
                guardar(state)
        except RuntimeError:
            print('Sin conexión con Telegram; reintento en 15 segundos.', flush=True)
            time.sleep(15)


if __name__ == '__main__':
    try: main()
    except Exception:
        raise SystemExit('El bot no pudo continuar. Consulta su configuración y conectividad.') from None
