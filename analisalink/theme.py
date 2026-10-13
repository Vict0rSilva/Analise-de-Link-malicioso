"""
Tema / design tokens do AnalisaLink (valores extraídos de figma_estrutura_completa.json).

Este módulo NÃO depende do Qt: é só dados. Para mudar a aparência do app,
edite aqui. A interface (analisalink/ui) lê tudo daqui.

Cores com transparência são guardadas como (hex, alpha), como no Figma.
"""

from dataclasses import dataclass

# DESIGN: CORES -------------------------------------------------------------
FUNDO = "#1E293B"            # fundo da janela e dos painéis
BORDA = "#334155"            # contorno de painéis, campo e cartões
TEXTO = "#F1F5F9"            # texto principal
TEXTO_SECUNDARIO = "#94A3B8"  # descrições
TEXTO_SUAVE = "#CBD5E1"      # orientações / ícone do escudo
CARTAO_ROTA = "#192536"      # fundo do cartão "rotas no percurso"

TEAL = "#0F766E"             # marca / estado "sem alertas"
TEAL_TEXTO = "#E6F7F5"       # texto sobre fundo teal
ROXO = "#7C3AED"             # botões primários
ROXO_CLARO = "#B69AFF"       # sigla/ação do urlscan
ROXO_BLOB = "#6D28D9"        # círculo decorativo
PERIGO = "#DC3545"           # botão e tint de risco
PERIGO_TEXTO = "#FDA4AF"     # texto de risco
AZUL_ICONE = "#93C5FD"       # ícone de link do campo

# DESIGN: CORES (EXTENSÃO - não existem no Figma; criadas no mesmo padrão)
ATENCAO = "#D97706"          # botão do estado "atenção"
ATENCAO_TINT = "#F59E0B"     # fundo/borda translúcidos do estado "atenção"
ATENCAO_TEXTO = "#FCD34D"    # texto do estado "atenção"
NEUTRO_TINT = "#94A3B8"      # estados "bloqueado" / "erro"
FOCO = "#A78BFA"             # anel de foco do teclado (acessibilidade)

SOMBRA_PAINEL = ("#000000", 0.20, 24, 48)   # (cor, alpha, deslocamento_y, blur)
SOMBRA_BOTAO = ("#7C3AED", 0.30, 10, 24)     # brilho roxo dos botões primários

# Círculos decorativos do fundo: (cor, opacidade) — Frame 1/2 do Figma
BLOB_TEAL = (TEAL, 0.45)
BLOB_ROXO = (ROXO_BLOB, 0.50)
# Na tela de alerta (Frame 3) os círculos são mais discretos:
BLOB_TEAL_ALERTA = (TEAL, 0.25)
BLOB_ROXO_ALERTA = (ROXO_BLOB, 0.18)
BLOB_RAIO = 180

# DESIGN: TIPOGRAFIA --------------------------------------------------------
FONTE = "Inter"              # arquivos em assets/fonts (Regular 400 / Bold 700)
PESO_NORMAL = 400
PESO_NEGRITO = 700
# tamanhos em px, como no Figma
T_HERO = 56            # "ANALISA LINK" / resultado positivo
T_HERO_ALERTA = 46     # "LINK NÃO CONFIÁVEL"
T_SUBTITULO = 18
T_SUBTITULO_ALERTA = 17
T_TITULO_CARTAO = 18   # "Resumo da análise"
T_TITULO_LATERAL = 24  # "Mais segurança e confiabilidade"
T_CORPO = 15
T_CORPO_PEQ = 14
T_NOTA = 13
T_MICRO = 12
T_BOTAO = 18
T_BOTAO_ALERTA = 16
T_NAV = 15

# DESIGN: ESPAÇAMENTOS ------------------------------------------------------
PAINEL_LARGURA = 730
LATERAL_LARGURA = 320
PAINEL_PADDING_ENTRADA = 56
PAINEL_PADDING_RESULTADO = 40
PAINEL_RAIO = 32
CARTAO_RAIO = 20
LATERAL_RAIO = 24
SERVICO_RAIO = 18
CAMPO_RAIO = 18
BOTAO_RAIO = 14
GAP_SECAO = 28          # entre blocos do painel de entrada
GAP_RESULTADO = 24      # entre blocos do painel de resultado
GAP_COLUNAS = 20        # entre painel e recomendações
MARGEM_JANELA = 24
CAMPO_ALTURA = 64

# Tamanhos de janela de referência (Figma): entrada 950x675 / resultado 1280x760
JANELA_ENTRADA = (950, 675)
JANELA_RESULTADO = (1280, 800)
JANELA_MINIMA = (940, 640)

# DESIGN: ANIMAÇÕES ---------------------------------------------------------
# O Figma só define navegação (SMART_ANIMATE). No app, a única animação é a
# barra de progresso indeterminada durante a análise.
ANIM_PROGRESSO_MS = 1200


@dataclass(frozen=True)
class Tom:
    """Paleta de um estado de resultado (usada no resumo, selo e botões)."""
    tint: str             # cor-base dos fundos translúcidos
    tint_alpha: float     # alpha do fundo do resumo
    borda_alpha: float    # alpha da borda do resumo
    texto: str            # cor do texto de destaque
    selo_solido: bool     # True: selo sólido (teal); False: translúcido
    selo_fundo: str       # cor do selo sólido
    selo_texto: str
    botao: str            # cor do botão principal do estado
    icone: str            # ícone do selo do cabeçalho
    ok: bool = False


TONS = {
    # Frame 2 (resultado positivo)
    "ok": Tom(TEAL, 0.08, 0.20, TEAL_TEXTO, True, TEAL, TEAL_TEXTO, ROXO, "shield-check", True),
    # Frame 3 (resultado de alerta)
    "perigo": Tom(PERIGO, 0.07, 0.30, PERIGO_TEXTO, False, PERIGO, PERIGO_TEXTO, PERIGO, "shield-alert"),
    # EXTENSÕES (no padrão do Figma)
    "atencao": Tom(ATENCAO_TINT, 0.07, 0.30, ATENCAO_TEXTO, False, ATENCAO, ATENCAO_TEXTO, ATENCAO, "triangle-alert"),
    "neutro": Tom(NEUTRO_TINT, 0.07, 0.30, TEXTO_SUAVE, False, NEUTRO_TINT, TEXTO_SUAVE, ROXO, "info"),
}
