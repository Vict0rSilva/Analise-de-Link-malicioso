import os, sys, unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from analisalink import backend as b
from helpers import RespostaFalsa as R, SessaoFalsa, dns_publico


def com_sessao(mapa):
    s = SessaoFalsa(mapa)
    return s, mock.patch.object(b, "criar_sessao", return_value=s)


class TestEntrada(unittest.TestCase):
    def test_normaliza(self):
        self.assertEqual(b.normalizar_link("  exemplo.com "), "https://exemplo.com")
        self.assertEqual(b.normalizar_link("http://x.com"), "http://x.com")
        self.assertEqual(b.normalizar_link(""), "")

    def test_validar(self):
        self.assertFalse(b.validar_entrada("")[0])
        self.assertFalse(b.validar_entrada("   ")[0])
        self.assertFalse(b.validar_entrada("ex emplo.com")[0])
        self.assertFalse(b.validar_entrada("https://")[0])
        self.assertTrue(b.validar_entrada("exemplo.com")[0])
        self.assertTrue(b.validar_entrada("ftp://x.com")[0])  # bloqueio fica no backend


class TestSeguirLink(unittest.TestCase):
    def test_cadeia_de_redirects_e_callback(self):
        mapa = {
            "https://bit.ly/a": R(301, {"Location": "https://meio.com/x"}),
            "https://meio.com/x": R(302, {"Location": "/final"}),
            "https://meio.com/final": R(200, {"Content-Type": "text/html; charset=utf-8"}),
        }
        s, p = com_sessao(mapa)
        vistos = []
        with p, dns_publico():
            saltos, destino, info, erro = b.seguir_link("https://bit.ly/a", False,
                                                       lambda n, u: vistos.append((n, u)))
        self.assertIsNone(erro)
        self.assertEqual(destino, "https://meio.com/final")
        self.assertEqual(len(saltos), 3)
        self.assertEqual(vistos[0], (1, "https://bit.ly/a"))
        self.assertEqual(vistos[-1][0], 3)
        self.assertEqual(info["tipo"], "text/html")
        self.assertFalse(info["download"])
        # nao baixa corpo e nao segue redirect sozinho
        self.assertTrue(all(k["stream"] and k["allow_redirects"] is False for k in s.kwargs))

    def test_bloqueia_ip_interno(self):
        s, p = com_sessao({})
        with p, dns_publico("127.0.0.1"):
            saltos, destino, info, erro = b.seguir_link("https://local.test", False)
        self.assertIn("Bloqueado por segurança", erro)
        self.assertIsNone(destino)
        self.assertEqual(s.visitadas, [])  # nenhuma requisição saiu

    def test_redirect_para_rede_interna_e_bloqueado(self):
        mapa = {"https://ok.com": R(302, {"Location": "http://192.168.0.1/admin"})}
        s, p = com_sessao(mapa)
        enderecos = {"ok.com": "93.184.216.34", "192.168.0.1": "192.168.0.1"}
        import socket
        def dns(host, *a, **k):
            return [(socket.AF_INET, 0, 0, "", (enderecos[host], 0))]
        with p, mock.patch("socket.getaddrinfo", side_effect=dns):
            saltos, destino, info, erro = b.seguir_link("https://ok.com", False)
        self.assertIn("Bloqueado por segurança", erro)
        self.assertEqual(s.visitadas, ["https://ok.com"])

    def test_esquema_invalido(self):
        s, p = com_sessao({})
        with p:
            _, destino, _, erro = b.seguir_link("ftp://x.com/a", False)
        self.assertIn("esquema inválido", erro)

    def test_dominio_inexistente(self):
        import socket
        s, p = com_sessao({})
        with p, mock.patch("socket.getaddrinfo", side_effect=socket.gaierror):
            _, destino, _, erro = b.seguir_link("https://nao-existe.test", False)
        self.assertIn("não existe", erro)

    def test_loop_de_redirects(self):
        mapa = {"https://a.com/": R(302, {"Location": "https://a.com/"})}
        s, p = com_sessao(mapa)
        with p, dns_publico():
            saltos, destino, info, erro = b.seguir_link("https://a.com/", False)
        self.assertIn("possível loop", erro)
        self.assertEqual(len(saltos), b.MAX_SALTOS + 1)

    def test_download_por_content_disposition_e_tipo(self):
        for hdr in ({"Content-Disposition": "attachment; filename=a.bin"},
                    {"Content-Type": "application/octet-stream"}):
            s, p = com_sessao({"https://a.com/f": R(200, hdr)})
            with p, dns_publico():
                _, destino, info, erro = b.seguir_link("https://a.com/f", False)
            self.assertTrue(info["download"], hdr)

    def test_falha_de_rede_e_dica_socks(self):
        mapa = {"https://a.com": requests.ConnectionError("Failed SOCKS5 proxy")}
        s, p = com_sessao(mapa)
        with p:   # modo Tor: nao resolve DNS local
            saltos, destino, info, erro = b.seguir_link("https://a.com", True)
        self.assertIn("Falha ao acessar", erro)
        self.assertIn("Tor", erro)

    def test_timeout(self):
        mapa = {"https://a.com": requests.Timeout()}
        s, p = com_sessao(mapa)
        with p, dns_publico():
            _, destino, _, erro = b.seguir_link("https://a.com", False)
        self.assertIn("Timeout", erro)

    def test_tor_nao_resolve_dns_local(self):
        s, p = com_sessao({"https://a.com": R(200, {})})
        with p, mock.patch("socket.getaddrinfo", side_effect=AssertionError("DNS local!")):
            _, destino, _, erro = b.seguir_link("https://a.com", True)
        self.assertEqual(destino, "https://a.com")

    def test_sessao_tor_usa_proxy_socks(self):
        sess = b.criar_sessao(True)
        self.assertEqual(sess.proxies["https"], b.TOR_PROXY)
        self.assertFalse(sess.trust_env)
        self.assertFalse(b.criar_sessao(False).proxies)


class TestAvaliar(unittest.TestCase):
    def test_sinais(self):
        s = dict(b.sinais_da_url("http://192.168.1.1/x"))
        txt = " ".join(t for _, t in b.sinais_da_url("http://192.168.1.1/x"))
        self.assertIn("sem criptografia", txt)
        self.assertIn("IP", txt)
        txt = " ".join(t for _, t in b.sinais_da_url("https://xn--pypal-4ve.com/"))
        self.assertIn("punycode", txt)
        txt = " ".join(t for _, t in b.sinais_da_url("https://user@site.com/"))
        self.assertIn("@", txt)
        txt = " ".join(t for _, t in b.sinais_da_url("https://meu-login-pix.top/"))
        self.assertIn("golpe", txt)
        self.assertEqual(b.sinais_da_url("https://exemplo.com/"), [])
        self.assertTrue(b.sinais_da_url("https://a.com/" + "x" * 250))

    def test_pontuacao_exe_download(self):
        saltos = [{"status": 200, "url": "https://a.com/setup.exe", "proximo": None}]
        ach = b.avaliar(saltos, "https://a.com/setup.exe", {"download": True}, None)
        self.assertEqual(sum(ach.values()), 6)

    def test_muitos_redirects_e_encurtadores(self):
        hosts = ["bit.ly", "tinyurl.com", "a.com", "b.com", "c.com"]
        saltos = [{"status": 301, "url": f"https://{h}/", "proximo": "x"} for h in hosts]
        ach = b.avaliar(saltos, None, {}, "erro")
        txt = " ".join(ach)
        self.assertIn("Muitos redirecionamentos", txt)
        self.assertIn("encurtadores", txt)


class TestAnalisarERelatorio(unittest.TestCase):
    def test_relatorio_ok(self):
        mapa = {"https://exemplo.com": R(200, {"Content-Type": "text/html"})}
        s, p = com_sessao(mapa)
        with p, dns_publico():
            r = b.analisar("exemplo.com", False)
        self.assertEqual(r.pontos, 0)
        t = r.relatorio
        for trecho in ("ANALISA LINK - RELATÓRIO", "Link:    https://exemplo.com",
                       "conexão direta", "RELATÓRIO DE SALTOS", "DESTINO FINAL",
                       "Nenhum sinal de alerta", "[OK]", "NÃO prova", "VirusTotal",
                       "urlscan.io/domain/exemplo.com", "virustotal.com/gui/url/"):
            self.assertIn(trecho, t)

    def test_relatorio_perigo(self):
        mapa = {"http://1.2.3.4/a.exe": R(200, {"Content-Type": "application/octet-stream"})}
        s, p = com_sessao(mapa)
        with p, dns_publico("1.2.3.4"):
            r = b.analisar("http://1.2.3.4/a.exe", True)
        self.assertGreaterEqual(r.pontos, 3)
        self.assertIn("[PERIGO]", r.relatorio)
        self.assertIn("rede Tor", r.relatorio)

    def test_urls_de_confirmacao(self):
        vt, us = b.urls_de_confirmacao("https://exemplo.com/p")
        self.assertTrue(vt.startswith("https://www.virustotal.com/gui/url/"))
        self.assertNotIn("=", vt)
        self.assertEqual(us, "https://urlscan.io/domain/exemplo.com")


if __name__ == "__main__":
    unittest.main()
