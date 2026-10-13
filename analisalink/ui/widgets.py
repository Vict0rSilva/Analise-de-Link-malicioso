"""
Componentes visuais reutilizáveis (DESIGN: COMPONENTES).

Tudo é desenhado/estilizado aqui a partir de analisalink/theme.py. Para criar
um novo cartão, botão ou selo, reaproveite estas classes em vez de repetir
estilos nas páginas.
"""

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QSizePolicy, QWidget)

from .. import theme
from . import icones

ESQ = Qt.AlignmentFlag.AlignLeft
CENTRO = Qt.AlignmentFlag.AlignHCenter
DIR = Qt.AlignmentFlag.AlignRight


# DESIGN: TIPOGRAFIA ---------------------------------------------------------
def fonte(px, peso=theme.PESO_NORMAL):
    f = QFont(theme.FONTE)
    f.setPixelSize(int(px))
    f.setWeight(QFont.Weight.Bold if peso >= 600 else QFont.Weight.Normal)
    return f


def qcor(hexa, alpha=1.0):
    c = QColor(hexa)
    c.setAlphaF(alpha)
    return c


def sombra(widget, cor, alpha, dy, blur):
    """Sombra projetada como no Figma (cor, alpha, deslocamento Y, blur)."""
    ef = QGraphicsDropShadowEffect(widget)
    ef.setColor(qcor(cor, alpha))
    ef.setOffset(0, dy)
    ef.setBlurRadius(blur)
    widget.setGraphicsEffect(ef)


class Rotulo(QLabel):
    """Texto com tamanho/peso/cor do tema. `quebra=True` quebra linhas."""

    def __init__(self, texto, tam=theme.T_CORPO, peso=theme.PESO_NORMAL,
                 cor=theme.TEXTO, alinhamento=ESQ, quebra=False, parent=None):
        super().__init__(texto, parent)
        self.setFont(fonte(tam, peso))
        self.setStyleSheet(f"color:{cor}; background:transparent;")
        self.setAlignment(alinhamento | Qt.AlignmentFlag.AlignVCenter)
        self.setWordWrap(quebra)
        if quebra:  # evita que palavras muito longas forcem a largura do layout
            self.setMinimumWidth(10)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

    def definir_cor(self, cor):
        self.setStyleSheet(f"color:{cor}; background:transparent;")


class RotuloElidido(QLabel):
    """Linha única que abrevia o meio com "…" (URLs longas não estouram o layout)."""

    def __init__(self, texto, tam=theme.T_NOTA, peso=theme.PESO_NORMAL,
                 cor=theme.TEXTO_SECUNDARIO, parent=None):
        super().__init__(parent)
        self._completo = texto
        self.setFont(fonte(tam, peso))
        self.setStyleSheet(f"color:{cor}; background:transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setToolTip(texto)
        self._reduzir()

    def minimumSizeHint(self):
        return QSize(10, QFontMetrics(self.font()).height() + 2)

    def sizeHint(self):
        return QSize(200, QFontMetrics(self.font()).height() + 2)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._reduzir()

    def _reduzir(self):
        fm = QFontMetrics(self.font())
        self.setText(fm.elidedText(self._completo, Qt.TextElideMode.ElideMiddle,
                                   max(10, self.width())))


class TituloAjustavel(QLabel):
    """Título grande de uma linha que reduz a fonte até caber na largura."""

    def __init__(self, texto, tam, cor=theme.TEXTO, minimo=26, parent=None):
        super().__init__(texto, parent)
        self._tam, self._min = tam, minimo
        self.setStyleSheet(f"color:{cor}; background:transparent;")
        self.setAlignment(CENTRO | Qt.AlignmentFlag.AlignVCenter)
        self.setFont(fonte(tam, theme.PESO_NEGRITO))
        self.setMinimumHeight(int(tam * 1.21))
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

    def minimumSizeHint(self):
        return QSize(10, int(self._tam * 1.21))

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        tam = self._tam
        while tam > self._min:
            fm = QFontMetrics(fonte(tam, theme.PESO_NEGRITO))
            if fm.horizontalAdvance(self.text()) <= self.width() - 4:
                break
            tam -= 1
        self.setFont(fonte(tam, theme.PESO_NEGRITO))


class Icone(QLabel):
    def __init__(self, nome, tam, cor, parent=None):
        super().__init__(parent)
        self.setFixedSize(tam, tam)
        self.setPixmap(icones.pixmap(nome, tam, cor))
        self.setStyleSheet("background:transparent;")

    def trocar(self, nome, tam, cor):
        self.setPixmap(icones.pixmap(nome, tam, cor))


class Cartao(QFrame):
    """Retângulo arredondado com preenchimento e borda do tema.

    raio=None  -> formato de pílula (raio = metade da altura), como os selos.
    """

    def __init__(self, raio=theme.CARTAO_RAIO, fundo=theme.FUNDO, borda=theme.BORDA,
                 parent=None):
        super().__init__(parent)
        self._raio = raio
        self._fundo = QColor(fundo) if isinstance(fundo, str) else fundo
        self._borda = QColor(borda) if isinstance(borda, str) else borda

    def definir_cores(self, fundo, borda):
        self._fundo = QColor(fundo) if isinstance(fundo, str) else fundo
        self._borda = QColor(borda) if isinstance(borda, str) else borda
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        raio = r.height() / 2 if self._raio is None else self._raio
        p.setBrush(self._fundo)
        if self._borda is not None:
            p.setPen(QPen(self._borda, 1))
        else:
            p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, raio, raio)
        p.end()


def selo(texto, fundo, cor_texto, borda=None, icone=None, tam=theme.T_CORPO_PEQ):
    """Selo em pílula (padding 14x8 do Figma), com ícone opcional de 16 px."""
    c = Cartao(raio=None, fundo=fundo, borda=borda)
    lay = QHBoxLayout(c)
    lay.setContentsMargins(14, 8, 14, 8)
    lay.setSpacing(8)
    if icone:
        lay.addWidget(Icone(icone, 16, cor_texto))
    lay.addWidget(Rotulo(texto, tam, theme.PESO_NEGRITO, cor_texto))
    c.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    return c


class Botao(QPushButton):
    """Botão principal (roxo/vermelho/âmbar) com cantos 14 e brilho colorido."""

    def __init__(self, texto, cor=theme.ROXO, icone=None, tam=theme.T_BOTAO,
                 pad_x=28, pad_y=16, brilho=True, parent=None):
        super().__init__(texto, parent)
        self._cor = QColor(cor)
        self._icone, self._tam = icone, tam
        self._pad = (pad_x, pad_y)
        self.setFont(fonte(tam, theme.PESO_NEGRITO))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        if brilho:
            cor_sombra = cor if cor != theme.ROXO else theme.SOMBRA_BOTAO[0]
            sombra(self, cor_sombra, theme.SOMBRA_BOTAO[1], theme.SOMBRA_BOTAO[2],
                   theme.SOMBRA_BOTAO[3])

    def definir_cor(self, cor):
        self._cor = QColor(cor)
        self.update()

    def _icone_px(self):
        return 16 if self._tam <= theme.T_NAV else 18

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        larg = fm.horizontalAdvance(self.text()) + 2 * self._pad[0]
        if self._icone:
            larg += self._icone_px() + (10 if self._icone == "arrow-up-right" else 8)
        return QSize(larg, fm.height() + 2 * self._pad[1])

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cor = QColor(self._cor)
        if not self.isEnabled():
            cor.setAlphaF(0.45)
        elif self.isDown():
            cor = cor.darker(120)
        elif self.underMouse():
            cor = cor.lighter(112)
        r = QRectF(self.rect())
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cor)
        p.drawRoundedRect(r, theme.BOTAO_RAIO, theme.BOTAO_RAIO)
        if self.hasFocus():  # anel de foco para navegação por teclado
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(theme.FOCO), 2))
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), theme.BOTAO_RAIO, theme.BOTAO_RAIO)
        # conteúdo centralizado: [ícone] texto
        fm = QFontMetrics(self.font())
        larg_texto = fm.horizontalAdvance(self.text())
        ic = self._icone_px() if self._icone else 0
        gap = 10 if self._icone == "arrow-up-right" else 8   # Figma: 10 (Acessar) / 8 (Nova análise)
        total = larg_texto + (ic + gap if ic else 0)
        x = (r.width() - total) / 2
        branco = "#FFFFFF"
        if self._icone and self._icone != "arrow-up-right":
            p.drawPixmap(int(x), int((r.height() - ic) / 2),
                         icones.pixmap(self._icone, ic, branco))
            x += ic + gap
        p.setPen(QColor(branco) if self.isEnabled() else qcor(branco, 0.7))
        p.setFont(self.font())
        # linha de base do texto, centralizada na vertical (sem flags de alinhamento)
        base_y = (r.height() - fm.height()) / 2 + fm.ascent()
        p.drawText(QPointF(x, base_y), self.text())
        if self._icone == "arrow-up-right":  # no Figma a seta vem DEPOIS do texto
            p.drawPixmap(int(x + larg_texto + gap), int((r.height() - ic) / 2),
                         icones.pixmap(self._icone, ic, branco))
        p.end()

    def enterEvent(self, ev):
        super().enterEvent(ev)
        self.update()

    def leaveEvent(self, ev):
        super().leaveEvent(ev)
        self.update()


class BotaoTexto(QPushButton):
    """Link de texto pequeno (ex.: "Salvar como…")."""

    def __init__(self, texto, cor=theme.ROXO_CLARO, parent=None):
        super().__init__(texto, parent)
        self.setFont(fonte(theme.T_MICRO, theme.PESO_NEGRITO))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setStyleSheet(
            f"QPushButton{{color:{cor}; background:transparent; border:none; padding:2px 0;"
            f" text-align:left;}} QPushButton:hover{{text-decoration:underline;}}"
            f"QPushButton:focus{{border-bottom:1px solid {theme.FOCO};}}")


class CampoTexto(QLineEdit):
    """QLineEdit que avisa quando ganha/perde o foco (para o contorno do campo)."""

    foco = Signal(bool)

    def focusInEvent(self, ev):
        super().focusInEvent(ev)
        self.foco.emit(True)

    def focusOutEvent(self, ev):
        super().focusOutEvent(ev)
        self.foco.emit(False)


class CartaoClicavel(Cartao):
    """Cartão que reage a clique, Enter e Espaço (teclado acessível)."""

    clicado = Signal()

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self.rect().contains(ev.position().toPoint()):
            self.clicado.emit()
        super().mouseReleaseEvent(ev)

    def keyPressEvent(self, ev):
        if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicado.emit()
        else:
            super().keyPressEvent(ev)

    def paintEvent(self, ev):
        super().paintEvent(ev)
        if self.hasFocus():
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(theme.FOCO), 2))
            r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
            p.drawRoundedRect(r, self._raio, self._raio)
            p.end()


def linha_separadora():
    f = QFrame()
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{theme.BORDA}; border:none;")
    return f


class PaginaBase(QWidget):
    """Fundo da janela: cor sólida + dois círculos decorativos (Figma)."""

    def __init__(self, blob_teal=theme.BLOB_TEAL, blob_roxo=theme.BLOB_ROXO,
                 deslocamento_roxo=(215, -110), parent=None):
        super().__init__(parent)
        self._teal, self._roxo = blob_teal, blob_roxo
        self._desl = deslocamento_roxo  # centro do círculo roxo: (w/2 + dx, h + dy)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(theme.FUNDO))
        p.setPen(Qt.PenStyle.NoPen)
        r = theme.BLOB_RAIO
        p.setBrush(qcor(*self._teal))
        p.drawEllipse(QRectF(40 - r, 40 - r, 2 * r, 2 * r))
        cx = self.width() / 2 + self._desl[0]
        cy = self.height() + self._desl[1]
        p.setBrush(qcor(*self._roxo))
        p.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))
        p.end()


class BarraIndeterminada(QWidget):
    """Barra de progresso fina e animada (DESIGN: ANIMAÇÕES).

    O backend não informa porcentagem, então a barra é "indeterminada": só
    indica que a análise está em andamento. Não simula progresso.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self._pos = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._passo)

    def iniciar(self):
        self._timer.start()

    def parar(self):
        self._timer.stop()

    def showEvent(self, ev):
        super().showEvent(ev)
        self.iniciar()

    def hideEvent(self, ev):
        super().hideEvent(ev)
        self.parar()

    def _passo(self):
        # um ciclo completo dura theme.ANIM_PROGRESSO_MS
        self._pos = (self._pos + 16.0 / theme.ANIM_PROGRESSO_MS) % 1.0
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(theme.BORDA))
        r = QRectF(self.rect())
        p.drawRoundedRect(r, 2, 2)
        seg = r.width() * 0.3
        x = -seg + (r.width() + seg) * self._pos
        p.setBrush(QColor(theme.ROXO))
        p.setClipRect(r)
        p.drawRoundedRect(QRectF(x, 0, seg, r.height()), 2, 2)
        p.end()
