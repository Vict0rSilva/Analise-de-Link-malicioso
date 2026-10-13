"""
Janela principal: alterna entre PaginaEntrada e PaginaResultado, cuida dos
diálogos (confirmação antes de abrir endereços externos, "Salvar como...") e
conecta tudo ao ControladorAnalise.

# NOVOS ELEMENTOS: para adicionar uma tela, crie a página em pages.py,
# acrescente-a ao QStackedWidget abaixo e troque com `self.pilha.setCurrentWidget`.
"""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (QFileDialog, QMainWindow, QMessageBox, QStackedWidget)

from .. import reports, theme
from ..controller import ControladorAnalise
from .pages import PaginaEntrada, PaginaResultado


class JanelaPrincipal(QMainWindow):
    def __init__(self, pasta_relatorios, link_inicial="", tor=False):
        super().__init__()
        self.setWindowTitle("AnalisaLink")
        self.setMinimumSize(*theme.JANELA_MINIMA)
        self.resize(*theme.JANELA_ENTRADA)

        self._pasta = Path(pasta_relatorios)
        self._view = None
        self._caminho = None

        self.entrada = PaginaEntrada()
        self.resultado = PaginaResultado()
        self.pilha = QStackedWidget()
        self.pilha.addWidget(self.entrada)
        self.pilha.addWidget(self.resultado)
        self.setCentralWidget(self.pilha)

        self.ctrl = ControladorAnalise(self._pasta, self)

        # FUNCIONALIDADE: ligação interface <-> controlador
        self.entrada.analisar_pedido.connect(self._iniciar)
        self.ctrl.progresso.connect(self.entrada.mostrar_progresso)
        self.ctrl.concluido.connect(self._concluido)
        self.ctrl.falhou.connect(self._falhou)
        self.resultado.nova_analise.connect(self._nova_analise)
        self.resultado.acessar.connect(self._acessar)
        self.resultado.abrir_servico.connect(self._abrir_servico)
        self.resultado.salvar_como.connect(self._salvar_como)
        self.resultado.abrir_pasta.connect(self._abrir_pasta)

        if link_inicial:                 # só preenche; NUNCA analisa sozinho
            self.entrada.preencher(link_inicial, tor)
        self.entrada.campo.setFocus()

    # ---- fluxo de análise ----------------------------------------------------
    def _iniciar(self, link, usar_tor):
        self.entrada.definir_ocupado(True)
        self.ctrl.iniciar(link, usar_tor)

    def _concluido(self, view, caminho, erro_salvar):
        self._view, self._caminho = view, caminho
        self.entrada.definir_ocupado(False)
        self.resultado.mostrar(view, caminho, erro_salvar)
        self.pilha.setCurrentWidget(self.resultado)
        self._ajustar_tamanho(resultado=True)

    def _falhou(self, msg):
        self.entrada.definir_ocupado(False)
        self.entrada.mostrar_erro(msg)

    def _nova_analise(self):
        self.entrada.limpar()
        self.pilha.setCurrentWidget(self.entrada)
        self._ajustar_tamanho(resultado=False)

    def _ajustar_tamanho(self, resultado):
        """Tamanhos de referência do Figma (entrada 950x675 / resultado 1280x800)."""
        if self.isMaximized() or self.isFullScreen():
            return
        larg, alt = theme.JANELA_RESULTADO if resultado else theme.JANELA_ENTRADA
        tela = self.screen() or QGuiApplication.primaryScreen()
        if tela is not None:
            area = tela.availableGeometry()
            larg, alt = min(larg, area.width()), min(alt, area.height())
        if resultado:
            larg, alt = max(larg, self.width()), max(alt, self.height())
        self.resize(larg, alt)

    # ---- endereços externos (sempre com confirmação) ---------------------------
    def _confirmar_abrir(self, titulo, texto, url):
        caixa = QMessageBox(self)
        caixa.setIcon(QMessageBox.Icon.Warning)
        caixa.setWindowTitle(titulo)
        caixa.setText(texto)
        caixa.setInformativeText(url)
        abrir = caixa.addButton("Abrir no navegador", QMessageBox.ButtonRole.AcceptRole)
        cancelar = caixa.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        caixa.setDefaultButton(cancelar)      # o padrão é NÃO abrir
        caixa.setEscapeButton(cancelar)
        caixa.exec()
        return caixa.clickedButton() is abrir

    @staticmethod
    def _abrir_url(url):
        if url.lower().startswith(("http://", "https://")):
            QDesktopServices.openUrl(QUrl(url))

    def _acessar(self):
        v = self._view
        if not v or not v.pode_acessar:
            return
        aviso = ("Este link foi classificado como “" + v.classificacao + "”. "
                 "Abri-lo é por sua conta e risco." if v.estado != "ok" else
                 "Nenhum sinal de alerta foi encontrado, mas isso não prova que o link é "
                 "seguro.")
        info = v.acessar_url
        if v.destino_url and v.destino_url != v.acessar_url:
            info += "\nDestino final da análise:\n" + v.destino_url
        if self._confirmar_abrir("Abrir link analisado", aviso + "\n\nEndereço que será aberto:",
                                 info):
            self._abrir_url(v.acessar_url)

    def _abrir_servico(self, url, nome):
        if self._confirmar_abrir(f"Abrir {nome}",
                                 "Este endereço será aberto no seu navegador:", url):
            self._abrir_url(url)

    # ---- relatório ---------------------------------------------------------------
    def _salvar_como(self):
        if not self._view:
            return
        sugestao = str((self._caminho.parent if self._caminho else self._pasta)
                       / reports.nome_arquivo())
        destino, _ = QFileDialog.getSaveFileName(self, "Salvar relatório", sugestao,
                                                 "Texto (*.txt)")
        if not destino:      # usuário cancelou: nada a fazer
            return
        try:
            self._caminho = reports.salvar_em_arquivo(self._view.relatorio, destino)
        except OSError as e:
            QMessageBox.warning(self, "Não foi possível salvar", reports.explicar_erro(e))
            return
        QMessageBox.information(self, "Relatório salvo", f"Relatório salvo em:\n{self._caminho}")

    def _abrir_pasta(self):
        if self._caminho:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self._caminho).parent)))
