# LaTeX do TCC

Fonte LaTeX do TCC, baseada no modelo Word `assets/modelo-TCC-SEG-Prof. Adilson-20261S.docx`. A versão final compilada está em `../entrega/`.

- `main.tex`: arquivo principal em LaTeX, baseado no modelo do professor.
- `assets/image1.png`: imagem institucional extraída do modelo Word.

## Observações

1. O modelo Word usa A4, Arial 12, margem superior/esquerda de 3 cm, margem inferior/direita de 2 cm, texto justificado e espaçamento 1,5. Esses parâmetros foram reproduzidos no LaTeX.
2. Para manter a fonte Arial exatamente, compile com XeLaTeX ou LuaLaTeX. Com pdfLaTeX, o arquivo usa Helvetica como substituta.
3. O PDF original tinha alguns textos fora da ordem esperada pelo sumário; esta versão preserva a ordem em que o texto apareceu na extração do PDF.
4. Recomenda-se revisar manualmente quebras de parágrafo, referências e eventuais palavras separadas pela extração do PDF.

## Compilação

Comando recomendado:

```bash
xelatex main.tex
xelatex main.tex
```

Também é possível abrir a pasta no Overleaf e escolher XeLaTeX como compilador.
