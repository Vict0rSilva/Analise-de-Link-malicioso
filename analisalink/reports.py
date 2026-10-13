"""
Gravação do relatório .txt (sem Qt).

O original gravava na pasta atual. No Windows, a pasta do .exe pode não ter
permissão de escrita; por isso a interface grava numa pasta de documentos do
usuário (informada pelo chamador) e oferece "Salvar como...".
"""

from datetime import datetime
from pathlib import Path


def nome_arquivo(agora=None):
    """Mesmo padrão do original: relatorio_AAAAMMDD_HHMMSS.txt"""
    agora = agora or datetime.now()
    return f"relatorio_{agora:%Y%m%d_%H%M%S}.txt"


def salvar_em_pasta(texto, pasta, agora=None):
    """Grava o relatório em <pasta>/relatorio_*.txt. Devolve o Path gravado.

    Cria a pasta se preciso. Levanta OSError (permissão, disco, caminho
    inválido...) para o chamador mostrar uma mensagem compreensível.
    """
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome_arquivo(agora)
    caminho.write_text(texto + "\n", encoding="utf-8")
    return caminho


def salvar_em_arquivo(texto, caminho):
    """Grava o relatório num caminho escolhido pelo usuário (Salvar como...)."""
    caminho = Path(caminho)
    caminho.write_text(texto + "\n", encoding="utf-8")
    return caminho


def explicar_erro(exc):
    """Mensagem curta e compreensível para uma falha ao salvar."""
    if isinstance(exc, PermissionError):
        return "Sem permissão para gravar nessa pasta."
    if isinstance(exc, FileNotFoundError):
        return "A pasta de destino não existe."
    return f"Não foi possível gravar o arquivo ({exc.__class__.__name__})."
