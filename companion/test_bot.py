import importlib.util
import pathlib
import unittest
from unittest.mock import patch, Mock

spec = importlib.util.spec_from_file_location('companion_bot', pathlib.Path(__file__).with_name('bot.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class Tests(unittest.TestCase):
    def test_solo_propietario_privado(self):
        admin = {'user_id': 1, 'chat_id': 1}
        self.assertTrue(b.autorizado({'from': {'id': 1}, 'chat': {'id': 1, 'type': 'private'}}, admin))
        for uid, cid, tipo in [(2, 1, 'private'), (1, 2, 'private'), (1, 1, 'group')]:
            self.assertFalse(b.autorizado({'from': {'id': uid}, 'chat': {'id': cid, 'type': tipo}}, admin))

    def test_preguntas(self):
        for text, expected in [('¿Cómo estás?', 'estado'), ('/estado', 'estado'),
                               ('¿Cuánta memoria queda?', 'uso'), ('ocupación de disco', 'disco'),
                               ('/curiosidad', 'curiosidad'), ('rm -rf /', 'ayuda')]:
            self.assertEqual(b.intencion(text), expected)

    def test_cpu_no_doble_conteo_guest(self):
        a = [0] * 8
        busy, wait, steal = b.cpu_delta(a, [10, 0, 10, 70, 5, 0, 0, 5])
        self.assertEqual((busy, wait, steal), (20, 5, 5))
        self.assertEqual(b.cpu_delta(a, a), (0, 0, 0))

    def test_memoria_disponible(self):
        with patch.object(b.Path, 'read_text', return_value='MemTotal: 2048 kB\nMemAvailable: 1024 kB\nSwapTotal: 1024 kB\nSwapFree: 512 kB\n'):
            text = b.memoria()
            self.assertIn('50%', text)
            self.assertIn('RAM disponible: 1 MiB', text)

    def test_curiosidad_no_repite_inmediata(self):
        fact = {'id': 'anterior', 'text': 'A test fact.', 'language': 'en'}
        with patch.object(b, 'json_externo', side_effect=[fact, dict(fact, id='nuevo')]), \
             patch.object(b, 'traducir', return_value=('Dato traducido.', True)):
            n, text = b.elegir_curiosidad('anterior')
            self.assertEqual(n, 'nuevo')
            self.assertIn('Dato traducido.', text)
            self.assertIn('https://uselessfacts.jsph.pl/api/v2/facts/nuevo', text)

    def test_fuente_caida(self):
        with patch.object(b, 'json_externo', side_effect=OSError('Sin red')):
            n, text = b.elegir_curiosidad('anterior')
            self.assertEqual(n, 'anterior')
            self.assertIn('No he podido', text)

    def test_fuente_malformada(self):
        with patch.object(b, 'json_externo', return_value={'id': '../../secreto'}):
            self.assertIn('No he podido', b.elegir_curiosidad()[1])

    def test_traduccion_y_cuota(self):
        with patch.object(b, 'json_externo', return_value={
                'responseStatus': 200, 'responseData': {'translatedText': 'Un dato.'}}):
            self.assertEqual(b.traducir('A fact.'), ('Un dato.', True))
        with patch.object(b, 'json_externo', return_value={'responseStatus': 429}):
            self.assertEqual(b.traducir('A fact.'), ('A fact.', False))

    def test_repeticion_no_se_presenta_como_novedad(self):
        with patch.object(b, 'json_externo', return_value={'id': 'igual', 'text': 'Fact.', 'language': 'en'}):
            self.assertIn('repetido', b.elegir_curiosidad('igual')[1])

    def test_comando_desconocido_no_ejecuta_nada(self):
        self.assertIn('ni ejecuto', b.respuesta('sudo reboot', {}))

    @patch.object(b, 'elegir_curiosidad', return_value=('id1', 'Dato externo.'))
    def test_una_notificacion_por_arranque(self, _):
        api, guardar, state = Mock(), Mock(), {}
        b.notificar_arranque(api, {'chat_id': 1}, state, 'boot1', guardar)
        b.notificar_arranque(api, {'chat_id': 1}, state, 'boot1', guardar)
        self.assertEqual(api.api.call_count, 1)
        b.notificar_arranque(api, {'chat_id': 1}, state, 'boot2', guardar)
        self.assertEqual(api.api.call_count, 2)

    @patch.object(b, 'elegir_curiosidad', return_value=('id1', 'Dato externo.'))
    def test_fallo_red_no_marca_notificacion_enviada(self, _):
        api, state = Mock(), {}
        api.api.side_effect = RuntimeError('Sin red')
        with self.assertRaises(RuntimeError):
            b.notificar_arranque(api, {'chat_id': 1}, state, 'boot1', Mock())
        self.assertNotIn('boot_notificado', state)


if __name__ == '__main__': unittest.main()
