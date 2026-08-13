# OCR Batch

Converte todos os PDFs da pasta `pdfs` em arquivos de texto na pasta `textos`.
Funciona com PDFs que já contêm texto, PDFs digitalizados e documentos mistos.

## Preparação no Windows

1. Instale Python 3.10 ou mais recente.
2. Instale o Tesseract OCR e o pacote do idioma português (`por`).
3. Adicione a pasta do Tesseract ao `PATH` do Windows.
4. Na pasta do programa, execute:

```powershell
py -m pip install -r requirements.txt
```

O Poppler não é necessário.

## Uso simples

1. Coloque os documentos na pasta `pdfs`.
2. Dê duplo clique em `iniciar.bat` para abrir a interface gráfica.
3. Clique em **Converter PDFs**.
4. Consulte os resultados na pasta `textos`.

Também é possível usar o programa pelo terminal:

```powershell
py ocr_batch.py
```

Subpastas existentes em `pdfs` são reproduzidas em `textos`, evitando conflito entre
arquivos de mesmo nome. Arquivos já convertidos não são sobrescritos por padrão.

## Opções

```powershell
py ocr_batch.py --help
py ocr_batch.py --overwrite
py ocr_batch.py --dpi 300 --lang por --verbose
py ocr_batch.py "C:\entrada" --out "C:\saida"
```

O programa retorna código `0` quando tudo termina corretamente, `1` quando algum PDF
falha e `2` quando há erro de configuração ou dependência.
