# OCR Batch

Aplicação desktop e CLI para converter, em lote, PDFs pesquisáveis, digitalizados ou
mistos em arquivos de texto UTF-8.

## Recursos

- interface gráfica nativa com Tkinter;
- extração direta de texto com PyMuPDF;
- OCR página a página com Tesseract;
- suporte a documentos mistos;
- processamento recursivo com preservação de subpastas;
- escrita atômica para evitar resultados incompletos;
- proteção contra sobrescrita acidental;
- resumo de conversões, arquivos ignorados e falhas;
- ferramenta para agrupar os resultados em um único TXT.

## Requisitos

- Windows;
- Python 3.10 ou mais recente;
- Tesseract OCR com o pacote do idioma desejado, como `por`;
- Tesseract disponível no `PATH` ou instalado em um diretório reconhecido.

O Poppler não é necessário.

## Instalação

Clone o repositório e instale as dependências:

```powershell
git clone https://github.com/edsonlima2000/Ocr-batch.git
cd Ocr-batch
py -m pip install -r requirements.txt
```

## Interface gráfica

1. Coloque os documentos na pasta `pdfs`.
2. Dê duplo clique em `iniciar.bat`.
3. Confira as pastas de entrada e saída.
4. Clique em **Converter PDFs**.
5. Consulte os arquivos gerados na pasta `textos`.

A janela permite escolher outras pastas, definir idioma e DPI, acompanhar mensagens e
decidir se resultados existentes podem ser sobrescritos.

## Linha de comando

Uso padrão:

```powershell
py ocr_batch.py
```

Exemplos:

```powershell
py ocr_batch.py --overwrite
py ocr_batch.py --dpi 300 --lang por --verbose
py ocr_batch.py "C:\entrada" --out "C:\saida"
```

Consulte todas as opções com `py ocr_batch.py --help`.

O programa retorna `0` quando tudo termina corretamente, `1` quando algum PDF falha e
`2` quando existe um problema de configuração ou dependência.

## Agrupar resultados

Para reunir todos os arquivos da pasta `textos` em um único documento, ajuste o nome
de saída em `agrupar_textos.py` se necessário e execute:

```powershell
py agrupar_textos.py
```

## Privacidade

Os conteúdos de `pdfs` e `textos` são ignorados pelo Git. Não publique documentos com
informações confidenciais e confira sempre o conteúdo preparado antes de um commit.

## Testes

```powershell
py -m unittest -v
```

## Licença

Distribuído sob a licença MIT. Consulte [LICENSE](LICENSE).
