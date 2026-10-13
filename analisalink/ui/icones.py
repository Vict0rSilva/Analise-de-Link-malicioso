"""
Ícones (estilo Lucide, os mesmos do Figma) desenhados a partir de SVG embutido.

# NOVOS ELEMENTOS: para adicionar um ícone, inclua o conteúdo interno do <svg>
# (viewBox 24x24, traço sem preenchimento) em _ICONES e use
# `pixmap("nome", tamanho, cor)`.
"""

from PySide6.QtCore import QByteArray
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_SHIELD = ('<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 '
           '1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 '
           '1 0 0 1 1 1z"/>')

_ICONES = {
    "shield-check": _SHIELD + '<path d="m9 12 2 2 4-4"/>',
    "shield-alert": _SHIELD + '<path d="M12 8v4"/><path d="M12 16h.01"/>',
    "triangle-alert": ('<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 '
                       '0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>'),
    "rotate-ccw": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "arrow-up-right": '<path d="M7 7h10v10"/><path d="M7 17 17 7"/>',
    "link": ('<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>'
             '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>'),
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
}

_cache = {}


def svg_texto(nome, cor):
    """SVG completo do ícone com a cor de traço pedida (útil também para testes)."""
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
            f'fill="none" stroke="{cor}" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round">{_ICONES[nome]}</svg>')


def pixmap(nome, tamanho, cor):
    """QPixmap nítido (respeita telas de alta densidade). `cor` = '#RRGGBB'."""
    app = QGuiApplication.instance()
    dpr = app.devicePixelRatio() if app is not None else 1.0
    chave = (nome, tamanho, cor, dpr)
    if chave in _cache:
        return _cache[chave]
    lado = max(1, int(round(tamanho * dpr)))
    pm = QPixmap(lado, lado)
    pm.fill(QColor(0, 0, 0, 0))
    render = QSvgRenderer(QByteArray(svg_texto(nome, cor).encode("utf-8")))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    render.render(p)
    p.end()
    pm.setDevicePixelRatio(dpr)
    _cache[chave] = pm
    return pm
