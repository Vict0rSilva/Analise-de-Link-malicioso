"""
Controlador: liga a interface ao backend SEM travar a janela.

A análise (rede) roda numa thread separada; o resultado volta para a janela
por sinais do Qt (entrega segura para a thread da interface).

# FUNCIONALIDADE: se quiser mudar o que acontece após a análise (ex.: gravar
# histórico), altere `_trabalho`.
"""

import logging
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from . import backend, presenter, reports

log = logging.getLogger("analisalink")


class ControladorAnalise(QObject):
    progresso = Signal(str)               # texto do salto atual (progresso real)
    concluido = Signal(object, object, str)   # (ResultadoView, Path|None, erro_ao_salvar)
    falhou = Signal(str)                  # erro inesperado (já registrado no log)

    def __init__(self, pasta_relatorios, parent=None):
        super().__init__(parent)
        self._pasta = Path(pasta_relatorios)
        self._ocupado = False

    @property
    def ocupado(self):
        return self._ocupado

    def iniciar(self, link, usar_tor):
        if self._ocupado:
            return
        self._ocupado = True
        # daemon=True: se o usuário fechar a janela, a thread não segura o programa
        threading.Thread(target=self._trabalho, args=(link, usar_tor), daemon=True).start()

    # ---------------------------------------------------------------------
    def _emitir(self, sinal, *args):
        try:
            sinal.emit(*args)
        except RuntimeError:   # janela já destruída
            pass

    def _trabalho(self, link, usar_tor):
        try:
            def on_salto(numero, url):
                self._emitir(self.progresso,
                             f"Salto {numero}: consultando {presenter.host_curto(url)}…")

            res = backend.analisar(link, usar_tor, on_salto)
            view = presenter.construir_view(res)
            caminho, erro_salvar = None, ""
            try:
                caminho = reports.salvar_em_pasta(res.relatorio, self._pasta)
            except OSError as e:
                erro_salvar = reports.explicar_erro(e)
                log.warning("Falha ao salvar relatório em %s: %s", self._pasta, e)
            self._ocupado = False
            self._emitir(self.concluido, view, caminho, erro_salvar)
        except Exception:
            log.exception("Falha inesperada na análise")
            self._ocupado = False
            self._emitir(self.falhou, "Ocorreu um erro inesperado durante a análise. "
                                      "Os detalhes foram gravados no arquivo de log.")
