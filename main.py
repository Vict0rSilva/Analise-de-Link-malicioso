"""Ponto de entrada do AnalisaLink (interface gráfica).

Uso:  python main.py [link] [--tor]
      (o link, se informado, apenas preenche o campo; a análise só começa ao clicar)
"""

import sys

from analisalink.app import executar

if __name__ == "__main__":
    sys.exit(executar(sys.argv))
