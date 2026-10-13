"""Apoio dos testes: respostas HTTP falsas (nenhum teste acessa a rede)."""
import socket
from unittest import mock


class RespostaFalsa:
    def __init__(self, status=200, headers=None):
        self.status_code = status
        self.headers = headers or {}
        self.fechada = False

    def close(self):
        self.fechada = True


class SessaoFalsa:
    """get(url) devolve a resposta registrada para a url (ou levanta a exceção)."""

    def __init__(self, mapa):
        self.mapa = mapa
        self.visitadas = []
        self.kwargs = []

    def get(self, url, **kw):
        self.visitadas.append(url)
        self.kwargs.append(kw)
        r = self.mapa[url]
        if isinstance(r, Exception):
            raise r
        return r


def dns_publico(ip="93.184.216.34"):
    """Faz o DNS devolver um IP público."""
    return mock.patch("socket.getaddrinfo",
                      return_value=[(socket.AF_INET, 0, 0, "", (ip, 0))])
