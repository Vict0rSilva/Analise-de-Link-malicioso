"""
Presenter: converte o Resultado do backend nos textos/estados que a tela mostra.

Não depende do Qt (por isso é testável em qualquer ambiente). Toda decisão
"o que escrever na tela" fica aqui; a interface só desenha o que recebe.

Regras (prioridade 1 = backend/segurança):
  - O veredito usa os MESMOS limiares do relatório original:
        pontos >= 3  -> perigo   |   pontos >= 1 -> atenção   |   0 -> sem alertas
  - Nunca se afirma que o link é "seguro" só porque nada foi encontrado.
"""

from dataclasses import dataclass, field
from urllib.parse import urlparse

from . import backend

# Mesmo texto que o backend usa quando não chega ao destino. Esse achado vale
# +1 ponto, mas NÃO é um "sinal de golpe" — é só falha de acesso.
_SINAL_SEM_DESTINO = "Não foi possível chegar ao destino final"


@dataclass
class Etapa:
    titulo: str      # Entrada / Intermediária / Destino
    descricao: str   # host + status
    url: str


@dataclass
class ResultadoView:
    estado: str                 # ok | atencao | perigo | bloqueado | erro
    tom: str                    # chave de theme.TONS
    selo: str                   # texto do selo do cabeçalho
    titulo: str
    explicacao: str
    classificacao: str          # selo do cartão "Resumo da análise"
    rotas: str                  # "3 rotas"
    status: str                 # "Acesso não recomendado"
    etapas: list = field(default_factory=list)
    sinais: list = field(default_factory=list)       # [(pontos, texto)]
    orientacao: str = ""
    problema: str = ""
    pode_acessar: bool = False
    acessar_rotulo: str = "ACESSAR"
    acessar_url: str = ""
    destino_url: str = ""
    pergunta: str = ""
    responsabilidade: str = ""
    relatorio: str = ""
    vt_url: str = ""
    urlscan_url: str = ""
    link: str = ""


ORIENTACAO_RISCO = ("Não informe senhas ou dados pessoais e não baixe arquivos. "
                    "Confirme a origem do link antes de continuar.")
ORIENTACAO_OK = ("Esta análise observa o caminho e os cabeçalhos do link, não o conteúdo da "
                 "página. Nunca digite senhas, dados de cartão ou PIX em páginas que chegou "
                 "por link desconhecido.")
ORIENTACAO_FALHA = ("Nenhuma página foi aberta. Se confia na origem do link, tente novamente; "
                    "caso contrário, confirme com quem o enviou.")


def _plural(n, singular, plural):
    return f"{n} {singular if n == 1 else plural}"


def _etapas(saltos, destino):
    etapas = []
    total = len(saltos)
    for i, s in enumerate(saltos):
        if i == 0 and total == 1:
            titulo = "Destino" if destino else "Entrada"
        elif i == 0:
            titulo = "Entrada"
        elif i == total - 1 and destino:
            titulo = "Destino"
        else:
            titulo = "Intermediária"
        host = backend.hospedeiro(s["url"]) or s["url"]
        if s["proximo"]:
            desc = f"{host} · redireciona ({s['status']})"
        else:
            desc = f"{host} · resposta {s['status']}"
        etapas.append(Etapa(titulo, desc, s["url"]))
    return etapas


def _dica_tor(res):
    if res.usar_tor and res.erro and res.erro.startswith("Falha ao acessar"):
        return (" Verifique se o Tor está aberto (porta 9050; use 9150 no Tor Browser) "
                "e se o pacote PySocks está instalado.")
    return ""


def construir_view(res):
    """Resultado (backend) -> ResultadoView (tela)."""
    pontos = res.pontos
    reais = pontos - (1 if _SINAL_SEM_DESTINO in res.achados else 0)
    bloqueado = bool(res.erro) and res.erro.startswith("Bloqueado por segurança")
    alvo = res.destino or (res.saltos[-1]["url"] if res.saltos else res.link)
    vt_url, us_url = backend.urls_de_confirmacao(alvo)
    sinais = sorted(((p, t) for t, p in res.achados.items() if t != _SINAL_SEM_DESTINO),
                    key=lambda x: -x[0])
    n_sinais = len(sinais)
    rotas = _plural(len(res.saltos), "rota", "rotas")

    v = ResultadoView(
        estado="", tom="", selo="Resultado da análise", titulo="", explicacao="",
        classificacao="", rotas=rotas, status="",
        etapas=_etapas(res.saltos, res.destino), sinais=sinais,
        problema=(res.erro or "") + _dica_tor(res),
        relatorio=res.relatorio, vt_url=vt_url, urlscan_url=us_url, link=res.link,
        destino_url=res.destino or "",
    )

    if pontos >= 3:
        v.estado, v.tom = "perigo", "perigo"
        v.titulo = "LINK NÃO CONFIÁVEL"
        v.explicacao = (f"A análise encontrou {_plural(n_sinais, 'sinal', 'sinais')} de alerta no "
                        "percurso deste link e sua segurança não está garantida. "
                        "Evite acessar ou compartilhar.")
        v.classificacao, v.status = "Não confiável", "Acesso não recomendado"
        v.orientacao = ORIENTACAO_RISCO
    elif bloqueado:
        v.estado, v.tom = "bloqueado", "neutro"
        v.selo, v.titulo = "Análise interrompida", "ANÁLISE BLOQUEADA"
        v.explicacao = ("Por segurança, o programa não visitou este endereço. "
                        "Nenhuma página foi acessada.")
        v.classificacao, v.status = "Bloqueado", "Bloqueado por regra de segurança"
        v.orientacao = ORIENTACAO_FALHA
    elif reais >= 1:
        v.estado, v.tom = "atencao", "atencao"
        v.titulo = "SINAIS SUSPEITOS"
        v.explicacao = (f"A análise encontrou {_plural(n_sinais, 'sinal', 'sinais')} de alerta. "
                        "Confirme nos serviços ao lado antes de abrir o link.")
        v.classificacao, v.status = "Atenção", "Confirme antes de acessar"
        v.orientacao = ORIENTACAO_RISCO
    elif res.erro:
        v.estado, v.tom = "erro", "neutro"
        v.selo, v.titulo = "Análise incompleta", "NÃO FOI POSSÍVEL CONCLUIR"
        v.explicacao = "O programa não conseguiu chegar ao destino final deste link."
        v.classificacao, v.status = "Inconclusivo", "Segurança não verificada"
        v.orientacao = ORIENTACAO_FALHA
    else:
        v.estado, v.tom = "ok", "ok"
        # DESVIO DO FIGMA (documentado): o Figma diz "LINK CONFIÁVEL ... com
        # segurança". O backend original afirma que "isso NÃO prova que o link é
        # seguro", então o texto foi ajustado para não prometer segurança.
        v.titulo = "SEM SINAIS DE ALERTA"
        v.explicacao = ("O link foi analisado e nenhum sinal de alerta foi encontrado no caminho. "
                        "Isso não prova que seja seguro: o conteúdo da página não é verificado.")
        v.classificacao, v.status = "Sem alertas", "Sem alertas detectados"
        v.orientacao = ORIENTACAO_OK

    # Acesso: só quando o destino final foi alcançado e a análise não foi barrada.
    if res.destino and v.estado in ("ok", "atencao", "perigo"):
        v.pode_acessar = True
        v.acessar_url = res.link
        if v.estado == "ok":
            v.acessar_rotulo = "ACESSAR LINK"
        else:
            v.acessar_rotulo = "ACESSAR"
            v.pergunta = "Ainda deseja continuar?"
            v.responsabilidade = "O acesso é por sua conta e risco."
    return v


def host_curto(url, limite=60):
    h = urlparse(url).hostname or url
    return h if len(h) <= limite else h[: limite - 1] + "…"
