import os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analisalink import backend as b, presenter as p, reports


def salto(url, status=200, prox=None):
    return {"status": status, "url": url, "proximo": prox}


def res(saltos, destino, achados=None, erro=None, tor=False, info=None, link=None):
    link = link or saltos[0]["url"]
    achados = b.avaliar(saltos, destino, info or {"status": 200, "tipo": "text/html", "download": False}, erro) \
        if achados is None else achados
    return b.Resultado(link, tor, saltos, destino, info or {}, erro, achados,
                       b.montar_relatorio(link, saltos, destino, info or {"status": 200, "tipo": "x"},
                                          erro, achados, tor))


class TestPresenter(unittest.TestCase):
    def test_ok_nao_promete_seguranca(self):
        v = p.construir_view(res([salto("https://exemplo.com")], "https://exemplo.com"))
        self.assertEqual((v.estado, v.tom), ("ok", "ok"))
        self.assertEqual(v.rotas, "1 rota")
        self.assertEqual(v.sinais, [])
        self.assertTrue(v.pode_acessar)
        self.assertEqual(v.acessar_rotulo, "ACESSAR LINK")
        texto = (v.titulo + v.explicacao + v.status + v.orientacao).lower()
        self.assertNotIn("confiável", texto.replace("não confiável", ""))
        self.assertNotIn("com segurança", texto)
        self.assertIn("não prova", v.explicacao)

    def test_perigo_usa_textos_do_figma(self):
        s = [salto("http://bit.ly/a", 301, "http://1.2.3.4/a.exe"), salto("http://1.2.3.4/a.exe")]
        r = res(s, "http://1.2.3.4/a.exe", info={"status": 200, "tipo": "application/octet-stream", "download": True})
        v = p.construir_view(r)
        self.assertEqual(v.estado, "perigo")
        self.assertEqual(v.titulo, "LINK NÃO CONFIÁVEL")
        self.assertEqual(v.status, "Acesso não recomendado")
        self.assertEqual(v.rotas, "2 rotas")
        self.assertEqual(v.pergunta, "Ainda deseja continuar?")
        self.assertEqual(v.responsabilidade, "O acesso é por sua conta e risco.")
        self.assertEqual([e.titulo for e in v.etapas], ["Entrada", "Destino"])
        self.assertTrue(v.sinais and v.sinais[0][0] >= v.sinais[-1][0])
        self.assertEqual(v.acessar_url, "http://bit.ly/a")
        self.assertEqual(v.destino_url, "http://1.2.3.4/a.exe")

    def test_atencao(self):
        v = p.construir_view(res([salto("http://exemplo.com")], "http://exemplo.com"))
        self.assertEqual((v.estado, v.tom), ("atencao", "atencao"))
        self.assertTrue(v.pode_acessar)
        self.assertEqual(v.pergunta, "Ainda deseja continuar?")

    def test_tres_etapas(self):
        s = [salto("https://a.com", 301, "https://b.com"), salto("https://b.com", 302, "https://c.com"),
             salto("https://c.com")]
        v = p.construir_view(res(s, "https://c.com"))
        self.assertEqual([e.titulo for e in v.etapas], ["Entrada", "Intermediária", "Destino"])

    def test_bloqueado(self):
        r = res([], None, erro="Bloqueado por segurança: https://x (aponta para endereço interno/reservado (127.0.0.1))",
                link="https://x")
        v = p.construir_view(r)
        self.assertEqual((v.estado, v.tom), ("bloqueado", "neutro"))
        self.assertFalse(v.pode_acessar)
        self.assertIn("Bloqueado por segurança", v.problema)
        self.assertEqual(v.titulo, "ANÁLISE BLOQUEADA")

    def test_erro_de_rede_e_dica_tor(self):
        r = res([], None, erro="Falha ao acessar https://x: ConnectionError (o Tor está aberto? instale pysocks)",
                tor=True, link="https://x")
        v = p.construir_view(r)
        self.assertEqual(v.estado, "erro")
        self.assertFalse(v.pode_acessar)
        self.assertIn("9050", v.problema)
        # sem Tor: sem a dica extra
        r2 = res([], None, erro="Falha ao acessar https://x: Timeout", link="https://x")
        self.assertNotIn("9050", p.construir_view(r2).problema)

    def test_falha_com_sinal_real_vira_atencao(self):
        r = res([salto("http://x.com", 301, "http://y.com")], None, erro="Falha ao acessar http://y.com: Timeout")
        v = p.construir_view(r)
        self.assertEqual(v.estado, "atencao")
        self.assertFalse(v.pode_acessar)   # destino nao alcancado: sem botao de acesso

    def test_urls_de_servico(self):
        v = p.construir_view(res([salto("https://exemplo.com")], "https://exemplo.com"))
        self.assertTrue(v.vt_url.startswith("https://www.virustotal.com/gui/url/"))
        self.assertEqual(v.urlscan_url, "https://urlscan.io/domain/exemplo.com")
        self.assertIn("ANALISA LINK - RELATÓRIO", v.relatorio)


class TestReports(unittest.TestCase):
    def test_salva_cria_pasta_e_conteudo(self):
        with tempfile.TemporaryDirectory() as d:
            c = reports.salvar_em_pasta("conteudo ç ã", Path(d) / "sub" / "pasta")
            self.assertTrue(c.name.startswith("relatorio_") and c.suffix == ".txt")
            self.assertEqual(c.read_text(encoding="utf-8"), "conteudo ç ã\n")

    def test_falha_de_gravacao(self):
        with tempfile.TemporaryDirectory() as d:
            arquivo = Path(d) / "eh_arquivo"
            arquivo.write_text("x")
            with self.assertRaises(OSError) as cm:
                reports.salvar_em_pasta("t", arquivo / "sub")   # pasta dentro de um arquivo
            self.assertTrue(reports.explicar_erro(cm.exception))
            with self.assertRaises(OSError):
                reports.salvar_em_arquivo("t", Path(d) / "naoexiste" / "r.txt")
        self.assertIn("permissão", reports.explicar_erro(PermissionError()))

    def test_salvar_como(self):
        with tempfile.TemporaryDirectory() as d:
            c = reports.salvar_em_arquivo("abc", Path(d) / "meu.txt")
            self.assertEqual(c.read_text(encoding="utf-8"), "abc\n")


if __name__ == "__main__":
    unittest.main()
