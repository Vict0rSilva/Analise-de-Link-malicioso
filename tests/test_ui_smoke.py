"""Teste de FUMAÇA da GUI com stub do Qt (ver aviso em qt_stub.py)."""
import os, sys, unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import PySide6.QtWidgets  # noqa  (Qt real instalado? então este teste é desnecessário)
    TEM_QT = True
except ImportError:
    TEM_QT = False

if not TEM_QT:
    import qt_stub
    qt_stub.instalar()

from analisalink import backend as b, presenter
from helpers import RespostaFalsa as R, SessaoFalsa  # noqa
from test_presenter_reports import res, salto


@unittest.skipIf(TEM_QT, "Qt real presente: use um teste com QApplication")
class TestFumaca(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from analisalink.ui import icones, pages, main_window
        icones.pixmap = lambda *a, **k: None     # sem renderização real
        pages.Icone = lambda *a, **k: mock.MagicMock()  # evita QPixmap
        from analisalink.ui import widgets
        widgets.RotuloElidido._reduzir = lambda self: None  # depende de QFontMetrics real
        cls.pages, cls.mw = pages, main_window

    def views(self):
        s3 = [salto("https://a.com", 301, "https://b.com"), salto("https://b.com", 302, "https://c.com"),
              salto("https://c.com")]
        s6 = [salto(f"https://h{i}.com", 301, f"https://h{i+1}.com") for i in range(5)] + [salto("https://h5.com")]
        return [
            presenter.construir_view(res([salto("https://exemplo.com")], "https://exemplo.com")),
            presenter.construir_view(res(s3, "https://c.com")),
            presenter.construir_view(res(s6, "https://h5.com")),
            presenter.construir_view(res([salto("http://exemplo.com")], "http://exemplo.com")),
            presenter.construir_view(res([salto("http://1.2.3.4/a.exe")], "http://1.2.3.4/a.exe",
                                         info={"status": 200, "tipo": "application/octet-stream", "download": True})),
            presenter.construir_view(res([], None, erro="Bloqueado por segurança: x (y)", link="https://x")),
            presenter.construir_view(res([], None, erro="Falha ao acessar https://x: Timeout", link="https://x")),
        ]

    def test_todas_as_telas_montam(self):
        pg = self.pages.PaginaResultado()
        estados = []
        for v in self.views():
            pg.mostrar(v, "/tmp/relatorio_x.txt", "")
            estados.append(v.estado)
        pg.mostrar(self.views()[0], None, "Sem permissão para gravar nessa pasta.")
        self.assertEqual(set(estados), {"ok", "atencao", "perigo", "bloqueado", "erro"})

    def test_entrada_valida_e_invalida(self):
        pg = self.pages.PaginaEntrada()
        recebido = []
        pg.analisar_pedido.connect(lambda l, t: recebido.append((l, t)))

        class Campo:
            def __init__(s, t): s.t = t
            def text(s): return s.t
            def setFocus(s): pass
            def setReadOnly(s, v): pass
        for texto in ("", "   ", "a b", "https://"):
            pg.campo = Campo(texto)
            pg._enviar()
        self.assertEqual(recebido, [])
        pg.campo = Campo("exemplo.com")
        pg.chk_tor = mock.MagicMock(isChecked=lambda: True)
        pg._enviar()
        self.assertEqual(recebido, [("exemplo.com", True)])
        pg.definir_ocupado(True)
        pg.definir_ocupado(False)

    def test_janela_fluxo_completo_com_backend_falso(self):
        import tempfile, threading
        resultado = res([salto("https://exemplo.com")], "https://exemplo.com")
        chamadas = []

        def falso(link, tor, cb):
            cb(1, "https://exemplo.com")
            chamadas.append((link, tor))
            return resultado

        with tempfile.TemporaryDirectory() as d, mock.patch.object(b, "analisar", falso):
            j = self.mw.JanelaPrincipal(d, "https://x.com", False)
            j.resultado.mostrar = mock.MagicMock()
            j.entrada.analisar_pedido.emit("exemplo.com", False)
            for t in threading.enumerate():
                if t is not threading.main_thread():
                    t.join(2)
            self.assertEqual(chamadas, [("exemplo.com", False)])
            j.resultado.mostrar.assert_called_once()
            view, caminho, erro = j.resultado.mostrar.call_args[0]
            self.assertEqual(view.estado, "ok")
            self.assertTrue(caminho.exists())          # relatório gravado de verdade
            self.assertIn("ANALISA LINK - RELATÓRIO", caminho.read_text(encoding="utf-8"))
            self.assertEqual(erro, "")
            j.resultado.nova_analise.emit()

    def test_falha_ao_salvar_relatorio_nao_quebra(self):
        import tempfile, threading
        resultado = res([salto("https://exemplo.com")], "https://exemplo.com")
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(b, "analisar", lambda l, t, cb: resultado):
            arquivo = os.path.join(d, "arq"); open(arquivo, "w").close()
            j = self.mw.JanelaPrincipal(os.path.join(arquivo, "sub"), "", False)
            j.resultado.mostrar = mock.MagicMock()
            j.entrada.analisar_pedido.emit("exemplo.com", False)
            for t in threading.enumerate():
                if t is not threading.main_thread():
                    t.join(2)
            view, caminho, erro = j.resultado.mostrar.call_args[0]
            self.assertIsNone(caminho)
            self.assertTrue(erro)

    def test_excecao_inesperada_vira_mensagem(self):
        import tempfile, threading
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(b, "analisar", side_effect=RuntimeError("boom")):
            j = self.mw.JanelaPrincipal(d, "", False)
            j.entrada.mostrar_erro = mock.MagicMock()
            j.entrada.analisar_pedido.emit("exemplo.com", False)
            for t in threading.enumerate():
                if t is not threading.main_thread():
                    t.join(2)
            j.entrada.mostrar_erro.assert_called_once()
            self.assertFalse(j.ctrl.ocupado)


if __name__ == "__main__":
    unittest.main()
