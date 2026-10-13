"""
AnalisaLink - segue a cadeia de redirecionamentos de um link SEM baixar o
conteudo das paginas, procura sinais de golpe e gera um relatorio.

Uso:
    AnalisaLink.exe                      (pergunta o link)
    AnalisaLink.exe https://link         (analisa direto)
    AnalisaLink.exe https://link --tor   (sai pela rede Tor)

NOTA (versao com interface grafica): este modulo e o codigo original, com
alteracoes MINIMAS e compativeis, todas marcadas com "# GUI:" no codigo:
  - seguir_link() ganhou o parametro opcional on_salto (callback de progresso);
  - foram adicionados normalizar_link(), validar_entrada(), Resultado e
    analisar(), que a interface usa para consumir a mesma logica da CLI.
O modo terminal (main) continua funcionando como antes.
"""

import base64
import ipaddress
import socket
import sys
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests

TOR_PROXY = "socks5h://127.0.0.1:9050"  # use 9150 se for o Tor Browser
MAX_SALTOS = 10
TIMEOUT = (5, 10)  # (conexao, leitura) em segundos
REDIRECTS = (301, 302, 303, 307, 308)

ENCURTADORES = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "rb.gy",
    "ow.ly", "acesse.one", "shorturl.at", "tiny.cc", "buff.ly", "rebrand.ly",
    "t.ly", "bit.do", "s.id", "encurtador.com.br", "l.instagram.com",
}
TLDS_RISCO = (
    ".zip", ".mov", ".top", ".xyz", ".tk", ".ml", ".ga", ".cf", ".gq",
    ".click", ".country", ".work", ".support", ".rest", ".cyou", ".icu", ".buzz",
)
EXT_PERIGOSAS = (
    ".exe", ".apk", ".scr", ".bat", ".cmd", ".msi", ".jar", ".vbs", ".ps1",
    ".js", ".lnk", ".zip", ".rar", ".7z", ".iso", ".docm", ".xlsm",
)
TIPOS_DOWNLOAD = {
    "application/octet-stream", "application/x-msdownload",
    "application/x-msdos-program", "application/x-dosexec", "application/zip",
    "application/vnd.android.package-archive", "application/java-archive",
    "application/x-rar-compressed", "application/x-7z-compressed",
}
PALAVRAS_GOLPE = (
    "login", "verifica", "seguranca", "atualiza", "pix", "premio", "gratis",
    "senha", "boleto", "recadastr",
)


# ---------------------------------------------------------------- rede ----

def criar_sessao(usar_tor):
    sessao = requests.Session()
    sessao.trust_env = False  # ignora proxies do sistema
    sessao.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
    )
    if usar_tor:
        sessao.proxies = {"http": TOR_PROXY, "https": TOR_PROXY}
    return sessao


def url_permitida(url, usar_tor):
    """(True, "") se pode visitar; senao (False, motivo)."""
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        return False, "esquema inválido (só http/https)"
    if usar_tor:  # DNS e resolvido pelo Tor; nao resolvemos localmente
        return True, ""
    try:
        enderecos = socket.getaddrinfo(p.hostname, None)
    except socket.gaierror:
        return False, "o domínio não existe ou não resolve"
    for info in enderecos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            return False, f"aponta para endereço interno/reservado ({ip})"
    return True, ""


def seguir_link(url, usar_tor, on_salto=None):
    """Retorna (saltos, destino, info_final, erro).

    GUI: on_salto(numero, url) e chamado (opcional) antes de cada requisicao,
    para a interface mostrar progresso REAL. Sem callback, nada muda.
    """
    sessao = criar_sessao(usar_tor)
    saltos, atual = [], url

    for _ in range(MAX_SALTOS + 1):
        if on_salto:  # GUI: informa o salto que vai ser consultado
            on_salto(len(saltos) + 1, atual)
        ok, motivo = url_permitida(atual, usar_tor)
        if not ok:
            return saltos, None, {}, f"Bloqueado por segurança: {atual} ({motivo})"
        try:
            # stream=True + close(): nao baixa o corpo da pagina
            r = sessao.get(atual, allow_redirects=False, stream=True, timeout=TIMEOUT)
        except requests.RequestException as e:
            dica = " (o Tor está aberto? instale pysocks)" if "SOCKS" in str(e).upper() else ""
            return saltos, None, {}, f"Falha ao acessar {atual}: {e.__class__.__name__}{dica}"

        status = r.status_code
        local = r.headers.get("Location")
        tipo = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
        disp = r.headers.get("Content-Disposition", "").lower()
        r.close()

        if status in REDIRECTS and local:
            proximo = urljoin(atual, local)
            saltos.append({"status": status, "url": atual, "proximo": proximo})
            atual = proximo
        else:
            saltos.append({"status": status, "url": atual, "proximo": None})
            info = {
                "status": status,
                "tipo": tipo or "desconhecido",
                "download": "attachment" in disp or tipo in TIPOS_DOWNLOAD,
            }
            return saltos, atual, info, None

    return saltos, None, {}, f"Mais de {MAX_SALTOS} redirecionamentos (possível loop)"


# ------------------------------------------------------------- analise ----

def sinais_da_url(url):
    sinais = []
    p = urlparse(url)
    host = (p.hostname or "").lower()

    if p.scheme == "http":
        sinais.append((1, f"Conexão sem criptografia (http): {host}"))
    try:
        ipaddress.ip_address(host)
        sinais.append((2, f"Usa número de IP em vez de nome de site: {host}"))
    except ValueError:
        pass
    if "xn--" in host:
        sinais.append((2, f"Domínio com caracteres disfarçados (punycode): {host}"))
    if p.username:
        sinais.append((2, f"Endereço com '@' (esconde o domínio real): {host}"))
    if host.endswith(TLDS_RISCO):
        sinais.append((1, f"Terminação de domínio muito usada em golpes: {host}"))
    if any(w in host for w in PALAVRAS_GOLPE):
        sinais.append((1, f"Domínio com palavra típica de golpe: {host}"))
    if len(url) > 200:
        sinais.append((1, "Endereço muito longo (200+ caracteres)"))
    return sinais


def avaliar(saltos, destino, info, erro):
    achados = {}  # texto -> pontos (evita repetir)
    for s in saltos:
        for pts, txt in sinais_da_url(s["url"]):
            achados[txt] = pts

    hosts = [(urlparse(s["url"]).hostname or "").lower() for s in saltos]
    redirecionamentos = sum(1 for s in saltos if s["proximo"])
    qtd_enc = sum(1 for h in hosts if h in ENCURTADORES)

    if redirecionamentos >= 4:
        achados[f"Muitos redirecionamentos ({redirecionamentos})"] = 1
    if qtd_enc >= 2:
        achados[f"Passa por {qtd_enc} encurtadores em sequência"] = 1

    if destino:
        if urlparse(destino).path.lower().endswith(EXT_PERIGOSAS):
            achados["O destino final é um arquivo executável/compactado"] = 3
        if info.get("download"):
            achados["O destino final força o download de um arquivo"] = 3
    if erro and not destino:
        achados["Não foi possível chegar ao destino final"] = 1

    return achados


def hospedeiro(url):
    return (urlparse(url).hostname or "").lower()


def montar_relatorio(link, saltos, destino, info, erro, achados, usar_tor):
    pontos = sum(achados.values())
    L = []
    add = L.append

    add("=" * 62)
    add("  ANALISA LINK - RELATÓRIO")
    add("=" * 62)
    add(f"Data:    {datetime.now():%d/%m/%Y %H:%M:%S}")
    add(f"Link:    {link}")
    add(f"Modo:    {'rede Tor (IP oculto)' if usar_tor else 'conexão direta (seu IP é visível ao destino)'}")

    add("\n--- RELATÓRIO DE SALTOS ---")
    if not saltos:
        add("  (nenhum salto realizado)")
    for i, s in enumerate(saltos, 1):
        add(f"  {i}. [{s['status']}] {s['url']}")
        if s["proximo"]:
            add(f"       redireciona para -> {s['proximo']}")
    redir = sum(1 for s in saltos if s["proximo"])
    add(f"\n  Total de redirecionamentos: {redir}")

    if destino:
        add(f"\nDESTINO FINAL: {destino}")
        add(f"  Resposta: {info['status']} | Tipo: {info['tipo']}")
    if erro:
        add(f"\nPROBLEMA: {erro}")

    add("\n--- SINAIS ENCONTRADOS ---")
    if achados:
        for txt, pts in sorted(achados.items(), key=lambda x: -x[1]):
            add(f"  [+{pts}] {txt}")
    else:
        add("  Nenhum sinal de alerta encontrado.")

    add("\n--- VEREDITO (verificação automática) ---")
    if pontos >= 3:
        add("  [PERIGO] LINK MUITO SUSPEITO. NÃO ABRA no navegador.")
    elif pontos >= 1:
        add("  [ATENÇÃO] Há sinais suspeitos. Confirme nos serviços abaixo antes de abrir.")
    elif erro:
        add("  [?] Não foi possível concluir a análise.")
    else:
        add("  [OK] Nenhum sinal de alerta nesta checagem.")
        add("       Isso NÃO prova que o link é seguro: esta ferramenta só")
        add("       olha o caminho, não o conteúdo. Confirme nos serviços abaixo.")

    alvo = destino or (saltos[-1]["url"] if saltos else link)
    vt_id = base64.urlsafe_b64encode(alvo.encode()).decode().strip("=")
    add("\n--- COMO CONFIRMAR DE VERDADE ---")
    add("  1) VirusTotal  (virustotal.com)")
    add("     Cole o link na aba URL. Mostra quantos antivírus e motores de")
    add("     segurança marcam o endereço como malicioso (phishing, malware).")
    add(f"     Link direto: https://www.virustotal.com/gui/url/{vt_id}")
    add("  2) urlscan.io")
    add("     Cole o link em 'Scan'. Eles abrem a página num navegador isolado")
    add("     e mostram captura de tela, redirecionamentos, domínios contatados")
    add("     e país do servidor, sem você abrir nada no seu computador.")
    add(f"     Histórico do domínio: https://urlscan.io/domain/{hospedeiro(alvo)}")
    add("  Dicas: analise o link ORIGINAL e o DESTINO FINAL; nunca digite senha,")
    add("  dados de cartão ou PIX em páginas que chegou por link desconhecido.")
    add("=" * 62)
    return "\n".join(L)


# ------------------------------------------------- API para a interface ----
# GUI: tudo abaixo foi ACRESCENTADO; nada do codigo original acima foi removido.

from dataclasses import dataclass, field


def normalizar_link(link):
    """Mesma normalizacao do main() original: tira espacos e assume https://."""
    link = (link or "").strip()
    if link and "://" not in link:
        link = "https://" + link
    return link


def validar_entrada(link):
    """(True, "") se o texto parece um link analisavel; senao (False, motivo).

    So rejeita o que e claramente invalido (vazio, com espacos, sem dominio).
    Esquemas nao-http/https e destinos internos continuam sendo bloqueados
    por url_permitida(), exatamente como no original.
    """
    link = (link or "").strip()
    if not link:
        return False, "Cole um link para analisar."
    if any(c.isspace() for c in link):
        return False, "O link não pode conter espaços. Confira o texto colado."
    try:
        host = urlparse(normalizar_link(link)).hostname
    except ValueError:
        host = None
    if not host:
        return False, "Não foi possível identificar o endereço do site neste link."
    return True, ""


@dataclass
class Resultado:
    """Tudo que a analise produz, para a GUI (e o relatorio) consumirem."""
    link: str
    usar_tor: bool
    saltos: list = field(default_factory=list)
    destino: object = None
    info: dict = field(default_factory=dict)
    erro: object = None
    achados: dict = field(default_factory=dict)
    relatorio: str = ""

    @property
    def pontos(self):
        return sum(self.achados.values())


def analisar(link, usar_tor=False, on_salto=None):
    """Executa o fluxo completo do main() original e devolve um Resultado."""
    link = normalizar_link(link)
    saltos, destino, info, erro = seguir_link(link, usar_tor, on_salto)
    achados = avaliar(saltos, destino, info, erro)
    relatorio = montar_relatorio(link, saltos, destino, info, erro, achados, usar_tor)
    return Resultado(link, usar_tor, saltos, destino, info, erro, achados, relatorio)


def urls_de_confirmacao(alvo):
    """(url_virustotal, url_urlscan) - as mesmas referencias do relatorio."""
    vt_id = base64.urlsafe_b64encode(alvo.encode()).decode().strip("=")
    return (f"https://www.virustotal.com/gui/url/{vt_id}",
            f"https://urlscan.io/domain/{hospedeiro(alvo)}")


# ---------------------------------------------------------------- main ----

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    usar_tor = "--tor" in sys.argv

    print("=== ANALISA LINK ===\n")
    if args:
        link = args[0].strip()
    else:
        link = input("Cole o link para analisar: ").strip()
        resp = input("Sair pela rede Tor para ocultar seu IP? (s/N): ").strip().lower()
        usar_tor = resp in ("s", "sim")

    if not link:
        print("Nenhum link informado.")
        return
    if "://" not in link:
        link = "https://" + link

    print("\nAnalisando (sem baixar o conteúdo)...\n")
    saltos, destino, info, erro = seguir_link(link, usar_tor)
    achados = avaliar(saltos, destino, info, erro)
    relatorio = montar_relatorio(link, saltos, destino, info, erro, achados, usar_tor)
    print(relatorio)

    nome = f"relatorio_{datetime.now():%Y%m%d_%H%M%S}.txt"
    try:
        with open(nome, "w", encoding="utf-8") as f:
            f.write(relatorio + "\n")
        print(f"\nRelatório salvo em: {nome}")
    except OSError:
        print("\n(Não foi possível salvar o relatório em arquivo.)")


if __name__ == "__main__":
    main()
    try:
        input("\nPressione Enter para sair...")
    except EOFError:
        pass