"""
Páginas da interface: PaginaEntrada (Figma "Frame 1") e PaginaResultado
(Figma "Frame 2" positivo / "Frame 3" alerta).

Estrutura do resultado (de cima para baixo):
    cabeçalho (selo, título, explicação) -> resumo -> percurso -> sinais
    -> orientação -> acesso | coluna "Recomendações" ao lado.

# NOVOS ELEMENTOS: para acrescentar um cartão ao painel de resultado, crie
# um método `_meu_cartao(self, view)` seguindo `_cartao_percurso` e chame-o em
# `_painel()`. Para um novo serviço de consulta, duplique uma chamada de
# `_servico(...)` em `_lateral()`.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QScrollArea, QSizePolicy,
                               QVBoxLayout, QWidget)

from .. import backend, theme
from .widgets import (Botao, BotaoTexto, BarraIndeterminada, CampoTexto, Cartao,
                      CartaoClicavel, CENTRO, DIR, Icone, PaginaBase, Rotulo,
                      RotuloElidido, TituloAjustavel, fonte, linha_separadora, qcor,
                      selo, sombra)

N = theme.PESO_NORMAL
B = theme.PESO_NEGRITO


def _fixar_transparente_ao_mouse(widget):
    """Filhos de um cartão clicável não "roubam" o clique."""
    for f in widget.findChildren(QWidget):
        f.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)


# =============================================================================
# Tela de entrada
# =============================================================================
class PaginaEntrada(PaginaBase):
    """Campo de link + botão VERIFICAR (Figma: 'painel-analise')."""

    # FUNCIONALIDADE: emitido ao clicar em VERIFICAR / Enter com link válido.
    analisar_pedido = Signal(str, bool)   # (link digitado, usar_tor)

    def __init__(self, parent=None):
        super().__init__(deslocamento_roxo=(380, -32), parent=parent)
        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(24, 24, 24, 24)

        self.painel = Cartao(raio=theme.PAINEL_RAIO)
        self.painel.setMaximumWidth(theme.PAINEL_LARGURA)
        self.painel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        sombra(self.painel, *theme.SOMBRA_PAINEL)
        pad = theme.PAINEL_PADDING_ENTRADA
        lay = QVBoxLayout(self.painel)
        lay.setContentsMargins(pad, pad, pad, pad)
        lay.setSpacing(theme.GAP_SECAO)

        # --- cabeçalho -------------------------------------------------------
        cab = QVBoxLayout()
        cab.setSpacing(12)
        cab.addWidget(selo("Análise de link", theme.TEAL, theme.TEAL_TEXTO), 0, CENTRO)
        cab.addWidget(TituloAjustavel("ANALISA LINK", theme.T_HERO))
        cab.addWidget(Rotulo("Cole o link para verificar a segurança e o conteúdo antes de "
                             "compartilhar ou acessar.", theme.T_SUBTITULO, N,
                             theme.TEXTO_SECUNDARIO, CENTRO, quebra=True))
        lay.addLayout(cab)

        # --- formulário ------------------------------------------------------
        form = QVBoxLayout()
        form.setSpacing(16)

        # DESIGN: COMPONENTES - campo de link (raio 18, altura 64, padding 20)
        self.campo_caixa = Cartao(raio=theme.CAMPO_RAIO)
        self.campo_caixa.setFixedHeight(theme.CAMPO_ALTURA)
        cl = QHBoxLayout(self.campo_caixa)
        cl.setContentsMargins(20, 0, 20, 0)
        cl.setSpacing(12)
        cl.addWidget(Icone("link", 20, theme.AZUL_ICONE))
        self.campo = CampoTexto()
        self.campo.setPlaceholderText("Cole o link aqui")
        self.campo.setClearButtonEnabled(False)
        self.campo.setFont(fonte(theme.T_SUBTITULO, N))
        self.campo.setFrame(False)
        self.campo.setStyleSheet(
            f"QLineEdit{{background:transparent; border:none; color:{theme.TEXTO};"
            f" selection-background-color:{theme.ROXO}; selection-color:#FFFFFF;}}")
        self.campo.setAccessibleName("Link para analisar")
        cl.addWidget(self.campo, 1)
        form.addWidget(self.campo_caixa)

        # Mensagem de erro de validação (estado "link inválido ou vazio")
        self.erro = Rotulo("", theme.T_CORPO_PEQ, N, theme.PERIGO_TEXTO, CENTRO, quebra=True)
        self.erro.hide()
        form.addWidget(self.erro)

        # EXTENSÃO (não está no Figma): opção Tor, exigida pelo backend original
        self.chk_tor = QCheckBox("Sair pela rede Tor (oculta seu IP)")
        self.chk_tor.setFont(fonte(theme.T_CORPO_PEQ, N))
        self.chk_tor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_tor.setToolTip("Requer o Tor aberto neste computador (porta 9050; "
                                "9150 no Tor Browser).")
        self.chk_tor.setStyleSheet(
            f"QCheckBox{{color:{theme.TEXTO_SECUNDARIO}; spacing:8px; background:transparent;}}"
            f"QCheckBox::indicator{{width:18px; height:18px; border-radius:5px;"
            f" border:1px solid {theme.BORDA}; background:{theme.FUNDO};}}"
            f"QCheckBox::indicator:checked{{background:{theme.ROXO}; border-color:{theme.ROXO};}}"
            f"QCheckBox::indicator:focus{{border-color:{theme.FOCO};}}")
        form.addWidget(self.chk_tor, 0, CENTRO)

        self.botao = Botao("VERIFICAR")
        form.addWidget(self.botao, 0, CENTRO)

        # Estado "análise em andamento": texto REAL do salto atual + barra animada
        self.status = Rotulo("", theme.T_CORPO_PEQ, N, theme.TEXTO_SECUNDARIO, CENTRO,
                             quebra=True)
        self.barra = BarraIndeterminada()
        self.status.hide()
        self.barra.hide()
        form.addWidget(self.status)
        form.addWidget(self.barra)
        lay.addLayout(form)

        raiz.addStretch(1)
        raiz.addWidget(self.painel, 100)
        raiz.addStretch(1)

        # FUNCIONALIDADE: ligação dos controles
        self.botao.clicked.connect(self._enviar)
        self.campo.returnPressed.connect(self._enviar)
        self.campo.foco.connect(self._foco_campo)
        self.campo.textChanged.connect(lambda _t: self.erro.hide())
        self.setTabOrder(self.campo, self.chk_tor)
        self.setTabOrder(self.chk_tor, self.botao)

    # ---- API usada pela janela ---------------------------------------------
    def _foco_campo(self, tem):
        self.campo_caixa.definir_cores(theme.FUNDO, theme.FOCO if tem else theme.BORDA)

    def _enviar(self):
        link = self.campo.text()
        ok, msg = backend.validar_entrada(link)   # estado: link inválido/vazio
        if not ok:
            self.mostrar_erro(msg)
            self.campo.setFocus()
            return
        self.erro.hide()
        self.analisar_pedido.emit(link, self.chk_tor.isChecked())

    def mostrar_erro(self, msg):
        self.erro.setText(msg)
        self.erro.show()

    def definir_ocupado(self, ocupado):
        """Estado 'análise em andamento'."""
        self.botao.setEnabled(not ocupado)
        self.botao.setText("ANALISANDO…" if ocupado else "VERIFICAR")
        self.botao.updateGeometry()
        self.chk_tor.setEnabled(not ocupado)
        self.campo.setReadOnly(ocupado)
        self.status.setVisible(ocupado)
        self.barra.setVisible(ocupado)
        if ocupado:
            self.erro.hide()
            self.status.setText("Iniciando análise…")

    def mostrar_progresso(self, texto):
        self.status.setText(texto)

    def preencher(self, link="", tor=False):
        self.campo.setText(link)
        self.chk_tor.setChecked(tor)

    def limpar(self):
        self.definir_ocupado(False)
        self.campo.clear()
        self.erro.hide()
        self.campo.setFocus()


# =============================================================================
# Tela de resultado
# =============================================================================
class PaginaResultado(PaginaBase):
    """Resultado da análise + coluna de recomendações."""

    # FUNCIONALIDADE: sinais tratados pela janela principal
    nova_analise = Signal()
    acessar = Signal()                 # botão ACESSAR / ACESSAR LINK
    abrir_servico = Signal(str, str)   # (url, nome) — VirusTotal, urlscan, GitHub
    salvar_como = Signal()
    abrir_pasta = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(theme.MARGEM_JANELA, 19, theme.MARGEM_JANELA, 12)
        raiz.setSpacing(12)

        # --- navegação (Figma: 'Navegação') -----------------------------------
        nav = QHBoxLayout()
        nav.setSpacing(12)
        nav.addWidget(Icone("shield-check", 22, theme.TEXTO_SUAVE))
        nav.addWidget(Rotulo("ANALISA LINK", theme.T_NAV, B, theme.TEXTO))
        nav.addStretch(1)
        self.btn_nova = Botao("Nova análise", theme.ROXO, icone="rotate-ccw",
                              tam=theme.T_NAV, pad_x=18, pad_y=12)
        nav.addWidget(self.btn_nova)
        raiz.addLayout(nav)

        # --- área rolável com o conteúdo -------------------------------------
        self.rolagem = QScrollArea()
        self.rolagem.setWidgetResizable(True)
        self.rolagem.setFrameShape(QScrollArea.Shape.NoFrame)
        self.rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.rolagem.setStyleSheet(
            "QScrollArea{background:transparent; border:none;}"
            f"QScrollBar:vertical{{background:transparent; width:10px; margin:0;}}"
            f"QScrollBar::handle:vertical{{background:{theme.BORDA}; border-radius:5px;"
            f" min-height:30px;}}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:transparent;}"
            f"QScrollBar:horizontal{{background:transparent; height:10px;}}"
            f"QScrollBar::handle:horizontal{{background:{theme.BORDA}; border-radius:5px;"
            f" min-width:30px;}}"
            "QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{width:0;}")
        self.rolagem.viewport().setAutoFillBackground(False)
        raiz.addWidget(self.rolagem, 1)

        # --- rodapé (Figma: 'Contexto do exemplo') ----------------------------
        self.btn_github = BotaoTexto("GitHub •", theme.TEXTO_SECUNDARIO)
        self.btn_github.setToolTip("https://github.com/Vict0rSilva")
        self.btn_github.setStyleSheet(
            self.btn_github.styleSheet().replace("text-align:left;", "text-align:center;"))
        raiz.addWidget(self.btn_github, 0, CENTRO)

        # FUNCIONALIDADE
        self.btn_nova.clicked.connect(lambda *_: self.nova_analise.emit())
        self.btn_github.clicked.connect(
            lambda: self.abrir_servico.emit("https://github.com/Vict0rSilva",
                                            "Perfil no GitHub"))
        self._view = None

    # ---- preenchimento -------------------------------------------------------
    def mostrar(self, view, caminho_relatorio=None, erro_salvar=""):
        """Reconstrói a tela a partir de um ResultadoView (do presenter)."""
        self._view = view
        # DESIGN: o fundo do alerta tem círculos mais discretos (Frame 3)
        if view.estado in ("ok",):
            self._teal, self._roxo = theme.BLOB_TEAL, theme.BLOB_ROXO
        else:
            self._teal, self._roxo = theme.BLOB_TEAL_ALERTA, theme.BLOB_ROXO_ALERTA
        self.update()

        conteudo = QWidget()
        h = QHBoxLayout(conteudo)
        h.setContentsMargins(4, 4, 4, 24)   # folga para a sombra dos painéis
        h.setSpacing(theme.GAP_COLUNAS)
        h.addStretch(1)
        h.addWidget(self._painel(view), 100, Qt.AlignmentFlag.AlignTop)
        h.addWidget(self._lateral(view, caminho_relatorio, erro_salvar), 0,
                    Qt.AlignmentFlag.AlignTop)
        h.addStretch(1)
        self.rolagem.setWidget(conteudo)   # o widget anterior é descartado pelo Qt
        conteudo.setAutoFillBackground(False)  # setWidget() liga o preenchimento: desligar
        self.rolagem.verticalScrollBar().setValue(0)
        self.btn_nova.setFocus()

    # ---- painel principal ----------------------------------------------------
    def _painel(self, v):
        tom = theme.TONS[v.tom]
        painel = Cartao(raio=theme.PAINEL_RAIO)
        painel.setMaximumWidth(theme.PAINEL_LARGURA)
        painel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        sombra(painel, *theme.SOMBRA_PAINEL)
        pad = theme.PAINEL_PADDING_RESULTADO
        lay = QVBoxLayout(painel)
        lay.setContentsMargins(pad, pad, pad, pad)
        lay.setSpacing(theme.GAP_RESULTADO)

        # cabeçalho ------------------------------------------------------------
        cab = QVBoxLayout()
        cab.setSpacing(12)
        if tom.selo_solido:
            cab.addWidget(selo(v.selo, tom.selo_fundo, tom.selo_texto), 0, CENTRO)
        else:
            cab.addWidget(selo(v.selo, qcor(tom.tint, 0.07), tom.selo_texto,
                               borda=qcor(tom.tint, 0.30), icone=tom.icone), 0, CENTRO)
        grande = theme.T_HERO if v.estado == "ok" else theme.T_HERO_ALERTA
        cab.addWidget(TituloAjustavel(v.titulo, grande))
        tam_sub = theme.T_SUBTITULO if v.estado == "ok" else theme.T_SUBTITULO_ALERTA
        cab.addWidget(Rotulo(v.explicacao, tam_sub, N, theme.TEXTO_SECUNDARIO, CENTRO,
                             quebra=True))
        if v.problema:
            cab.addWidget(Rotulo(f"Detalhe: {v.problema}", theme.T_CORPO_PEQ, N, tom.texto,
                                 CENTRO, quebra=True))
        lay.addLayout(cab)

        lay.addWidget(self._cartao_resumo(v, tom))
        lay.addWidget(self._cartao_percurso(v))
        if v.sinais:
            lay.addWidget(self._cartao_sinais(v, tom))
        lay.addLayout(self._orientacao(v, tom))
        self._acesso(lay, v, tom)
        return painel

    def _linha(self, rotulo, valor, cor_valor):
        h = QHBoxLayout()
        h.addWidget(Rotulo(rotulo, theme.T_CORPO, N, theme.TEXTO_SECUNDARIO))
        h.addStretch(1)
        h.addWidget(Rotulo(valor, theme.T_CORPO, B, cor_valor, DIR))
        return h

    def _cartao_resumo(self, v, tom):
        c = Cartao(raio=theme.CARTAO_RAIO, fundo=qcor(tom.tint, tom.tint_alpha),
                   borda=qcor(tom.tint, tom.borda_alpha))
        lay = QVBoxLayout(c)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)
        topo = QHBoxLayout()
        topo.addWidget(Rotulo("Resumo da análise", theme.T_TITULO_CARTAO, B, theme.TEXTO))
        topo.addStretch(1)
        if tom.selo_solido:
            pill = selo(v.classificacao, tom.selo_fundo, tom.selo_texto)
        else:
            pill = selo(v.classificacao, qcor(tom.tint, 0.07), tom.selo_texto,
                        tam=theme.T_NOTA)
        topo.addWidget(pill)
        lay.addLayout(topo)
        lay.addLayout(self._linha("Rotas identificadas", v.rotas, theme.TEXTO))
        lay.addLayout(self._linha("Status de segurança", v.status, tom.texto))
        return c

    def _cartao_percurso(self, v):
        c = Cartao(raio=theme.CARTAO_RAIO, fundo=theme.CARTAO_ROTA, borda=theme.BORDA)
        lay = QVBoxLayout(c)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)
        topo = QHBoxLayout()
        topo.addWidget(Rotulo(f"{v.rotas} no percurso", theme.T_CORPO, B, theme.TEXTO))
        topo.addStretch(1)
        # DESVIO DO FIGMA: o texto original "Exemplo ilustrativo" não vale aqui,
        # pois os dados são reais.
        topo.addWidget(Rotulo("Percurso real", theme.T_MICRO, N, theme.TEXTO_SECUNDARIO, DIR))
        lay.addLayout(topo)

        et = v.etapas
        if 0 < len(et) <= 3:     # layout horizontal do Figma
            linha = QHBoxLayout()
            linha.setSpacing(16)
            for i, e in enumerate(et):
                col = QVBoxLayout()
                col.setSpacing(6)
                col.addWidget(Rotulo(e.titulo, theme.T_CORPO_PEQ, B, theme.TEXTO))
                d = RotuloElidido(e.descricao, theme.T_MICRO)
                d.setToolTip(e.url)
                col.addWidget(d)
                linha.addLayout(col, 1)
                if i < len(et) - 1:
                    linha.addWidget(Icone("arrow-right", 18, theme.TEXTO_SECUNDARIO), 0,
                                    Qt.AlignmentFlag.AlignVCenter)
            lay.addLayout(linha)
        else:                    # 4+ rotas: lista vertical (extensão)
            for i, e in enumerate(et, 1):
                linha = QHBoxLayout()
                linha.setSpacing(10)
                n = Rotulo(f"{i}.", theme.T_MICRO, B, theme.TEXTO_SECUNDARIO)
                n.setFixedWidth(22)
                linha.addWidget(n)
                t = Rotulo(e.titulo, theme.T_CORPO_PEQ, B, theme.TEXTO)
                t.setFixedWidth(104)
                linha.addWidget(t)
                d = RotuloElidido(e.descricao, theme.T_MICRO)
                d.setToolTip(e.url)
                linha.addWidget(d, 1)
                lay.addLayout(linha)
        return c

    def _cartao_sinais(self, v, tom):
        """EXTENSÃO: lista dos sinais reais do backend (o relatório .txt tem a mesma)."""
        c = Cartao(raio=theme.CARTAO_RAIO, fundo=theme.CARTAO_ROTA, borda=theme.BORDA)
        lay = QVBoxLayout(c)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)
        topo = QHBoxLayout()
        topo.addWidget(Rotulo("Sinais encontrados", theme.T_CORPO, B, theme.TEXTO))
        topo.addStretch(1)
        topo.addWidget(Rotulo(str(len(v.sinais)), theme.T_MICRO, N, theme.TEXTO_SECUNDARIO, DIR))
        lay.addLayout(topo)
        for pts, txt in v.sinais:
            linha = QHBoxLayout()
            linha.setSpacing(10)
            p = Rotulo(f"+{pts}", theme.T_NOTA, B, tom.texto)
            p.setFixedWidth(26)
            linha.addWidget(p, 0, Qt.AlignmentFlag.AlignTop)
            linha.addWidget(Rotulo(txt, theme.T_CORPO_PEQ, N, theme.TEXTO_SUAVE, quebra=True), 1)
            lay.addLayout(linha)
        return c

    def _orientacao(self, v, tom):
        h = QHBoxLayout()
        h.setSpacing(12)
        if v.estado == "ok":
            h.addWidget(Icone("info", 20, theme.TEXTO_SECUNDARIO), 0, Qt.AlignmentFlag.AlignTop)
        else:
            h.addWidget(Icone("triangle-alert", 20, tom.texto), 0, Qt.AlignmentFlag.AlignTop)
        h.addWidget(Rotulo(v.orientacao, theme.T_CORPO_PEQ, N, theme.TEXTO_SUAVE, quebra=True), 1)
        return h

    def _acesso(self, lay, v, tom):
        if not v.pode_acessar:
            if v.estado != "ok":
                lay.addWidget(Rotulo("O acesso direto não é oferecido porque a análise não "
                                     "chegou ao destino final.", theme.T_NOTA, N,
                                     theme.TEXTO_SECUNDARIO, CENTRO, quebra=True))
            return
        if v.pergunta:                       # layout de alerta (Frame 3)
            lay.addWidget(linha_separadora())
            h = QHBoxLayout()
            col = QVBoxLayout()
            col.setSpacing(4)
            col.addWidget(Rotulo(v.pergunta, theme.T_CORPO, B, theme.TEXTO))
            col.addWidget(Rotulo(v.responsabilidade, theme.T_NOTA, N, theme.TEXTO_SECUNDARIO))
            h.addLayout(col)
            h.addStretch(1)
            b = Botao(v.acessar_rotulo, tom.botao, icone="arrow-up-right",
                      tam=theme.T_BOTAO_ALERTA, pad_x=24, pad_y=16)
            h.addWidget(b)
            lay.addLayout(h)
        else:                                # layout positivo (Frame 2)
            b = Botao(v.acessar_rotulo, tom.botao)
            lay.addWidget(b, 0, CENTRO)
        b.setToolTip(f"Abrirá no navegador (após confirmação): {v.acessar_url}")
        b.clicked.connect(lambda *_: self.acessar.emit())      # FUNCIONALIDADE

    # ---- coluna "Recomendações" ------------------------------------------------
    def _lateral(self, v, caminho, erro_salvar):
        c = Cartao(raio=theme.LATERAL_RAIO, fundo=qcor(theme.TEAL, 0.08),
                   borda=qcor(theme.TEAL, 0.20))
        c.setFixedWidth(theme.LATERAL_LARGURA)
        lay = QVBoxLayout(c)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        intro = QVBoxLayout()
        intro.setSpacing(12)
        intro.addWidget(selo("Recomendações", theme.ROXO, theme.TEXTO), 0,
                        Qt.AlignmentFlag.AlignLeft)
        intro.addWidget(Rotulo("Mais segurança e confiabilidade", theme.T_TITULO_LATERAL, B,
                               theme.TEXTO, quebra=True))
        intro.addWidget(Rotulo("Para maior tranquilidade, consulte os relatórios em sites "
                               "especializados antes de acessar o link.", theme.T_CORPO, N,
                               theme.TEXTO_SECUNDARIO, quebra=True))
        lay.addLayout(intro)

        # FUNCIONALIDADE: as URLs vêm do backend (mesmas referências do relatório)
        lay.addWidget(self._servico(
            "VT", "VirusTotal", "Análise de malware e reputação",
            "Consulte o relatório de antivírus e a reputação do link antes de acessar.",
            "virustotal.com", theme.TEAL, theme.TEAL, v.vt_url))
        lay.addWidget(self._servico(
            "US", "urlscan", "Análise de comportamento e rastreamento",
            "Verifique o histórico de acesso, redirecionamentos e possíveis sinais de risco.",
            "urlscan.io", theme.ROXO_CLARO, theme.ROXO, v.urlscan_url))

        # nota do relatório (DESVIO: o Figma fala em "pasta raiz do programa")
        nota = QHBoxLayout()
        nota.setSpacing(8)
        nota.addWidget(Icone("info", 16, theme.TEXTO_SECUNDARIO), 0, Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(4)
        if caminho:
            col.addWidget(Rotulo("Relatório completo salvo em:", theme.T_MICRO, N,
                                 theme.TEXTO_SECUNDARIO, quebra=True))
            col.addWidget(RotuloElidido(str(caminho), theme.T_MICRO))
        else:
            motivo = f" ({erro_salvar})" if erro_salvar else ""
            col.addWidget(Rotulo(f"O relatório não foi salvo automaticamente{motivo}. "
                                 "Use “Salvar como…”.", theme.T_MICRO, N,
                                 theme.TEXTO_SECUNDARIO, quebra=True))
        acoes = QHBoxLayout()
        acoes.setSpacing(14)
        b1 = BotaoTexto("Salvar como…", theme.ROXO_CLARO)
        b1.clicked.connect(lambda *_: self.salvar_como.emit())
        acoes.addWidget(b1)
        if caminho:
            b2 = BotaoTexto("Abrir pasta", theme.ROXO_CLARO)
            b2.clicked.connect(lambda *_: self.abrir_pasta.emit())
            acoes.addWidget(b2)
        acoes.addStretch(1)
        col.addLayout(acoes)
        nota.addLayout(col, 1)
        lay.addLayout(nota)
        lay.addStretch(1)
        return c

    def _servico(self, sigla, nome, especialidade, descricao, dominio, cor, tint, url):
        c = CartaoClicavel(raio=theme.SERVICO_RAIO, fundo=theme.FUNDO, borda=theme.BORDA)
        lay = QVBoxLayout(c)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        topo = QHBoxLayout()
        topo.setSpacing(12)
        ident = Cartao(raio=12, fundo=qcor(tint, 0.08), borda=None)
        ident.setFixedSize(40, 40)
        il = QHBoxLayout(ident)
        il.setContentsMargins(0, 0, 0, 0)
        il.addWidget(Rotulo(sigla, theme.T_CORPO_PEQ, B, cor, CENTRO))
        topo.addWidget(ident, 0, Qt.AlignmentFlag.AlignTop)
        info = QVBoxLayout()
        info.setSpacing(4)
        info.addWidget(Rotulo(nome, 16, B, theme.TEXTO))
        info.addWidget(Rotulo(especialidade, theme.T_NOTA, N, theme.TEXTO_SECUNDARIO,
                              quebra=True))
        topo.addLayout(info, 1)
        lay.addLayout(topo)
        lay.addWidget(Rotulo(descricao, theme.T_CORPO_PEQ, N, theme.TEXTO_SECUNDARIO,
                             quebra=True))
        acao = QHBoxLayout()
        acao.setSpacing(8)
        acao.addWidget(Rotulo("Consultar", theme.T_CORPO_PEQ, B, cor))
        acao.addWidget(Rotulo(dominio, theme.T_NOTA, N, theme.TEXTO_SECUNDARIO))
        acao.addStretch(1)
        acao.addWidget(Icone("arrow-up-right", 15, cor))
        lay.addLayout(acao)

        c.setToolTip(url)   # deixa claro qual endereço será aberto
        c.setAccessibleName(f"Consultar {nome} para este link")
        _fixar_transparente_ao_mouse(c)
        c.clicado.connect(lambda: self.abrir_servico.emit(url, nome))
        return c
