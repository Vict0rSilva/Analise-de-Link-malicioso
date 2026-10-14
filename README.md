# AnalisaLink

O AnalisaLink é uma ferramenta desenvolvida com auxílio de Inteligência Artificial (IA), utilizando Python para analisar URLs e identificar possíveis sinais de risco, como domínios suspeitos e redirecionamentos.

<p align="center">
  <img src="https://github.com/Vict0rSilva/Analise-de-Link-malicioso/blob/e561c76326792559d3863f4ecef8aded0521b0c3/Untitled-1.jpg" alt="Descrição da imagem">
</p>

## Funcionalidades

- Análise de URLs e redirecionamentos.
- Identificação de possíveis indicadores de risco.
- Classificação dos resultados da análise.
- Geração de relatórios em texto.
- Suporte opcional ao Tor.

## Instalação

1. Baixe e extraia os arquivos do projeto.
2. Abra a pasta do projeto.
3. Execute o arquivo `build.bat` com dois cliques.
4. Aguarde a conclusão da compilação.
5. Localize o executável gerado na pasta de saída.

**Requisito:** Python instalado no Windows, caso necessário para executar o script de compilação.

## Como usar

1. Execute o arquivo `AnalisaLink.exe`.
2. Informe a URL que deseja analisar.
3. Inicie a análise.
4. Consulte os resultados apresentados.

## Tecnologias utilizadas

- Python
- Inteligência Artificial (IA) como auxílio no desenvolvimento
- Análise de URLs e redirecionamentos
- Interface gráfica para Windows

## Segurança e privacidade

O AnalisaLink foi desenvolvido para execução local no computador do usuário, sem exigir que a aplicação seja hospedada em um servidor público.

A execução local reduz a exposição associada à hospedagem externa, mas **não garante ausência de vulnerabilidades**. A segurança depende da implementação, das dependências utilizadas e das conexões realizadas durante a análise.

A ferramenta identifica possíveis indicadores de risco, mas não garante que uma URL seja segura.

## Observações

- O arquivo `build.bat` deve estar presente na pasta do projeto.
- O nome e o local do executável dependem da configuração de compilação.
- O uso do Tor depende de configuração e dependências compatíveis.
- Relatorios são gerados na pasta do programa, o arquivo é acumulativo!! Necessario apagar ao executar um link.(correção em breve)
- O arquivo não ter uma licença do Windows é necessário adicionar a pasta em exclusões no Defender.
