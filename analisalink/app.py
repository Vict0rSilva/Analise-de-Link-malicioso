"""
Inicialização do aplicativo: fontes, tema global, log e janela principal.

# DESIGN: TIPOGRAFIA - as fontes Inter ficam em assets/fonts e são carregadas aqui.
# DESIGN: CORES - o estilo global (diálogos e dicas) usa theme.py.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import __version__, theme

log = logging.getLogger("analisalink")


def caminho_recurso(relativo):
    """Funciona tanto rodando do código-fonte quanto dentro do .exe (PyInstaller)."""
    base = getattr(sys, "_MEIPASS", None)
    base = Path(base) if base else Path(__file__).resolve().parent.parent
    return base / relativo


def pasta_de_log():
    if os.name == "nt":
        raiz = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        raiz = Path.home() / ".local" / "share"
    return raiz / "AnalisaLink" / "logs"


def configurar_log():
    """Grava erros em arquivo (o .exe não tem console). Devolve o caminho do log."""
    try:
        pasta = pasta_de_log()
        pasta.mkdir(parents=True, exist_ok=True)
        arquivo = pasta / "analisalink.log"
        h = RotatingFileHandler(arquivo, maxBytes=500_000, backupCount=2, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(h)
        log.setLevel(logging.INFO)
        return arquivo
    except OSError:
        return None


ESTILO_GLOBAL = f"""
QMessageBox, QFileDialog {{ background:{theme.FUNDO}; }}
QMessageBox QLabel {{ color:{theme.TEXTO}; font-size:14px; }}
QMessageBox QPushButton {{ background:{theme.ROXO}; color:#FFFFFF; border:none;
    border-radius:10px; padding:8px 18px; font-weight:700; min-width:96px; }}
QMessageBox QPushButton:hover {{ background:#8B5CF6; }}
QMessageBox QPushButton:focus {{ border:2px solid {theme.FOCO}; }}
QToolTip {{ background:#0F172A; color:{theme.TEXTO}; border:1px solid {theme.BORDA};
    padding:4px 6px; }}
"""


def executar(argv):
    # Importa o Qt só aqui, para o resto do pacote funcionar sem Qt (testes).
    from PySide6.QtGui import QFontDatabase, QIcon
    from PySide6.QtCore import QStandardPaths
    from PySide6.QtWidgets import QApplication, QMessageBox

    arquivo_log = configurar_log()

    args = [a for a in argv[1:] if not a.startswith("--")]
    tor = "--tor" in argv
    link_inicial = args[0] if args else ""

    app = QApplication(argv)
    app.setApplicationName("AnalisaLink")
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")
    app.setStyleSheet(ESTILO_GLOBAL)

    for nome in ("Inter-Regular.otf", "Inter-Bold.otf"):
        if QFontDatabase.addApplicationFont(str(caminho_recurso(f"assets/fonts/{nome}"))) < 0:
            log.warning("Fonte não carregada: %s", nome)

    icone = caminho_recurso("assets/icon.ico")
    if icone.exists():
        app.setWindowIcon(QIcon(str(icone)))

    def erro_nao_tratado(tipo, valor, tb):
        log.error("Erro não tratado", exc_info=(tipo, valor, tb))
        try:
            QMessageBox.critical(None, "AnalisaLink",
                                 "Ocorreu um erro inesperado.\n"
                                 + (f"Detalhes em:\n{arquivo_log}" if arquivo_log else ""))
        except Exception:
            pass

    sys.excepthook = erro_nao_tratado

    # Pasta de relatórios: Documentos\AnalisaLink (não depende da pasta do .exe)
    docs = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    pasta_relatorios = Path(docs or Path.home()) / "AnalisaLink"

    from .ui.main_window import JanelaPrincipal
    janela = JanelaPrincipal(pasta_relatorios, link_inicial, tor)
    janela.show()
    return app.exec()
