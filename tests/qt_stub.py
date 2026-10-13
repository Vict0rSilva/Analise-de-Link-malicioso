"""
Stub MÍNIMO do PySide6 — só para um teste de FUMAÇA do código Python da GUI
em ambientes sem Qt (como o da sessão de desenvolvimento).

ATENÇÃO: isto NÃO testa o Qt de verdade (layout, pintura, eventos). Só detecta
erros de Python (nomes, atributos, argumentos, lógica de sinais) ao importar e
montar as telas. A verificação real exige PySide6 instalado (ver README).
"""
import sys
import types


class _Meta(type):
    def __getattr__(cls, nome):          # Qt.AlignmentFlag.AlignLeft etc.
        return _Dummy()

    def __or__(cls, o):
        return _Dummy()


class _Dummy(metaclass=_Meta):
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, nome):
        if nome.startswith("__"):
            raise AttributeError(nome)
        return _Dummy()

    def __call__(self, *a, **k):
        return _Dummy()

    def __iter__(self):
        return iter(())

    def __or__(self, o):
        return _Dummy()

    __ror__ = __or__


class _SinalInst:
    def __init__(self):
        self._cbs = []

    def connect(self, cb):
        self._cbs.append(cb)

    def emit(self, *a):
        for cb in list(self._cbs):
            cb(*a)


class _Sinal:
    """Signal(...) falso, um por instância (como no Qt): connect() guarda, emit() chama."""

    def __init__(self, *tipos):
        self._nome = None

    def __set_name__(self, dono, nome):
        self._nome = "_sig_" + nome

    def __get__(self, obj, tipo=None):
        if obj is None:
            return self
        return obj.__dict__.setdefault(self._nome, _SinalInst())


def instalar():
    nomes = {
        "PySide6": [],
        "PySide6.QtCore": ["QByteArray", "QObject", "QPointF", "QRectF", "QSize", "Qt", "QTimer", "QUrl",
                           "QStandardPaths"],
        "PySide6.QtGui": ["QColor", "QDesktopServices", "QFont", "QFontDatabase",
                          "QFontMetrics", "QGuiApplication", "QIcon", "QPainter", "QPen",
                          "QPixmap"],
        "PySide6.QtSvg": ["QSvgRenderer"],
        "PySide6.QtWidgets": ["QApplication", "QCheckBox", "QFileDialog", "QFrame",
                              "QGraphicsDropShadowEffect", "QHBoxLayout", "QLabel",
                              "QLineEdit", "QMainWindow", "QMessageBox", "QPushButton",
                              "QScrollArea", "QSizePolicy", "QStackedWidget", "QVBoxLayout",
                              "QWidget"],
    }
    for mod, classes in nomes.items():
        m = types.ModuleType(mod)
        for c in classes:
            setattr(m, c, type(c, (_Dummy,), {}))
        if mod == "PySide6.QtCore":
            m.Signal = _Sinal
        sys.modules[mod] = m
