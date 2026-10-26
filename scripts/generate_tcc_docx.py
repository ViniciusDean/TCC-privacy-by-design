from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "latex_tcc" / "assets" / "modelo-TCC-SEG-Prof. Adilson-20261S.docx"
TEX = ROOT / "latex_tcc" / "main.tex"
OUT = ROOT / "TCC_Vinicius_Dean_modelo_Adilson.docx"
LOGO = ROOT / "latex_tcc" / "assets" / "image1.png"

AUTHOR = "Vinicius Dean"
TITLE = "Privacy by Design no Ciclo de Desenvolvimento de Software"
TITLE_EN = "Privacy by Design in the Software Development Life Cycle"
CITY = "São Caetano do Sul"
YEAR = "2026"
ORIENTADOR = "Prof. Dr. Adilson Ferreira da Silva"
INSTITUTION = "Faculdade de Tecnologia de São Caetano do Sul – Antônio Russo"


def clean_inline(text: str) -> str:
    text = re.sub(r"\\textbf\{([^}]*)\}", r"\1", text)
    text = text.replace("\\noindent", "").strip()
    text = text.replace("\\%", "%")
    text = text.replace("\\$", "R$")
    text = text.replace("\\_", "_")
    text = text.replace("--", "–")
    text = text.replace("( General Data Protection Regulation – GDPR)", "(General Data Protection Regulation – GDPR)")
    text = text.replace("( privacy as default )", "(privacy as default)")
    text = text.replace("concentra -se", "concentra-se")
    text = text.replace("UNIAO EUROPEIA", "UNIÃO EUROPEIA")
    text = text.replace("\\", "")
    return re.sub(r"\s+", " ", text).strip()


def extract_latex_content():
    tex = TEX.read_text(encoding="utf-8")
    body_start = tex.find(r"\pagenumbering{arabic}")
    if body_start == -1:
        body_start = tex.find(r"\chapter{")
    refs_match = re.search(r"\\chapter\*\{REFER[^}]*\}", tex)
    if body_start == -1 or not refs_match:
        raise RuntimeError("Não consegui localizar o corpo ou as referências no main.tex")

    body = tex[body_start:refs_match.start()]
    refs_part = tex[refs_match.end():]
    refs_part = re.sub(r"\\addcontentsline\{toc\}\{chapter\}\{REFER[^}]*\}", "", refs_part)
    refs_part = re.sub(r"\\setstretch\{[^}]+\}", "", refs_part)
    refs_part = re.sub(r"\\setlength\{\\parindent\}\{[^}]+\}", "", refs_part)
    refs_part = re.sub(r"\\setlength\{\\parskip\}\{[^}]+\}", "", refs_part)
    refs_part = refs_part.split(r"\end{document}", 1)[0].strip()

    blocks = []
    list_mode = None
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(r"\pagenumbering") or line.startswith(r"\setcounter") or line.startswith(r"\pagestyle"):
            continue
        if line == r"\begin{enumerate}":
            list_mode = "number"
            continue
        if line == r"\begin{itemize}":
            list_mode = "bullet"
            continue
        if line in (r"\end{enumerate}", r"\end{itemize}"):
            list_mode = None
            continue

        match = re.match(r"\\chapter\{(.+)\}", line)
        if match:
            blocks.append(("chapter", clean_inline(match.group(1))))
            continue
        match = re.match(r"\\section\{(.+)\}", line)
        if match:
            blocks.append(("section", clean_inline(match.group(1))))
            continue
        match = re.match(r"\\subsection\{(.+)\}", line)
        if match:
            blocks.append(("subsection", clean_inline(match.group(1))))
            continue
        if line.startswith(r"\item "):
            blocks.append((list_mode or "bullet", clean_inline(line[6:])))
            continue
        blocks.append(("p", clean_inline(line)))

    merged_blocks = []
    for kind, text in blocks:
        if (
            kind == "p"
            and merged_blocks
            and merged_blocks[-1][0] == "p"
            and merged_blocks[-1][1]
            and not re.search(r"[.!?;:]$", merged_blocks[-1][1])
            and text[:1].islower()
        ):
            merged_blocks[-1] = ("p", merged_blocks[-1][1] + " " + text)
        else:
            merged_blocks.append((kind, text))

    references = [clean_inline(x) for x in re.split(r"\n\s*\n", refs_part) if clean_inline(x)]
    return merged_blocks, references


def clear_document(doc: Document):
    body_el = doc._body._element
    sect_pr = None
    for child in list(body_el):
        if child.tag == qn("w:sectPr"):
            sect_pr = child
            continue
        body_el.remove(child)
    if sect_pr is not None and sect_pr.getparent() is None:
        body_el.append(sect_pr)


def set_default_format(doc: Document):
    for section in doc.sections:
        section.top_margin = Cm(3)
        section.left_margin = Cm(3)
        section.right_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.header_distance = Cm(1.25)
        section.footer_distance = Cm(1.25)

    for style in doc.styles:
        if style.type != 1:
            continue
        if style.name in ("Normal", "1-Parágrafo", "1-Título", "1.1-Título", "List Bullet", "List Number"):
            style.font.name = "Arial"
            style.font.size = Pt(12)
            style.paragraph_format.space_after = Pt(0)
            style.paragraph_format.line_spacing = 1.5


def set_page_numbering(section):
    header = section.header
    p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_text = OxmlElement("w:t")
    fld_text.text = "1"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(fld_text)
    run._r.append(fld_end)


def add_toc_field(doc):
    p = doc.add_paragraph()
    run = p.add_run()

    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = r'TOC \h \z \t "1-Título,1,1.1-Título,2"'

    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")

    fallback = OxmlElement("w:t")
    fallback.text = "Atualize o sumário no Word: Ctrl+A e depois F9."

    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")

    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(fallback)
    run._r.append(fld_end)


def add_logo(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if LOGO.exists():
        p.add_run().add_picture(str(LOGO), width=Cm(16))


def add_center(doc, text="", bold=False, space_before=0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(text)
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(12)
    return p


def add_para(doc, text, style_name="1-Parágrafo", first_indent=True):
    try:
        p = doc.add_paragraph(style=style_name)
    except Exception:
        p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.first_line_indent = Cm(1.25) if first_indent else Cm(0)
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(12)
    return p


def add_title_page_heading(doc, title):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run(title)
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(12)


def page_break(doc):
    doc.add_page_break()


def add_cover(doc):
    add_logo(doc)
    add_center(doc, AUTHOR, space_before=36)
    for _ in range(7):
        doc.add_paragraph()
    add_center(doc, TITLE, bold=True)
    for _ in range(8):
        doc.add_paragraph()
    add_center(doc, CITY)
    add_center(doc, YEAR)
    page_break(doc)


def add_title_sheet(doc):
    add_logo(doc)
    add_center(doc, AUTHOR, space_before=36)
    for _ in range(7):
        doc.add_paragraph()
    add_center(doc, TITLE, bold=True)
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Cm(7.5)
    p.paragraph_format.line_spacing = 1.5
    p.add_run(
        f"Trabalho de Graduação apresentado à {INSTITUTION}, como requisito parcial para a obtenção do grau de Tecnólogo em Segurança da Informação."
    )
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(7.5)
    p.add_run(f"Orientador: {ORIENTADOR}")
    for _ in range(4):
        doc.add_paragraph()
    add_center(doc, CITY)
    add_center(doc, YEAR)
    page_break(doc)


def add_exam_sheet(doc):
    add_logo(doc)
    add_center(doc, AUTHOR, space_before=36)
    for _ in range(5):
        doc.add_paragraph()
    add_center(doc, TITLE, bold=True)
    for _ in range(3):
        doc.add_paragraph()
    doc.add_paragraph("Banca examinadora:")
    for name, role in (
        (ORIENTADOR, "Presidente da Banca"),
        ("Prof. Xxxxxxxxxxxxxxxxxxxxxxx", "Professor convidado"),
        ("Prof. Xxxxxxxxxxxxxxxxxxxxxxx", "Professor convidado"),
    ):
        doc.add_paragraph()
        doc.add_paragraph("________________________________________")
        doc.add_paragraph(name)
        doc.add_paragraph(role)
    for _ in range(2):
        doc.add_paragraph()
    add_center(doc, CITY)
    add_center(doc, YEAR)
    page_break(doc)


def add_pretext(doc):
    add_title_page_heading(doc, "RESUMO")
    add_para(doc, f"DEAN, Vinicius. {TITLE}. Trabalho de Graduação. FATEC São Caetano do Sul – Antônio Russo. 2026.", first_indent=False)
    add_para(
        doc,
        "Este trabalho aborda a aplicação do conceito de Privacy by Design no ciclo de desenvolvimento de software, com foco na construção de uma ferramenta de apoio à identificação de vulnerabilidades de privacidade em código-fonte e esquemas de banco de dados. A proposta considera os requisitos da Lei Geral de Proteção de Dados Pessoais (LGPD) e busca aproximar práticas de conformidade do cotidiano das equipes de desenvolvimento.",
    )
    add_para(doc, "Palavras-chave: Privacy by Design; LGPD; análise estática; privacidade; desenvolvimento de software.", first_indent=False)
    page_break(doc)

    add_title_page_heading(doc, "ABSTRACT")
    add_para(doc, f"DEAN, Vinicius. {TITLE_EN}. Undergraduate Final Paper. FATEC São Caetano do Sul – Antônio Russo. 2026.", first_indent=False)
    add_para(
        doc,
        "This work discusses the application of Privacy by Design in the software development life cycle, focusing on the construction of a tool to support the identification of privacy vulnerabilities in source code and database schemas. The proposal considers the requirements of the Brazilian General Data Protection Law (LGPD) and aims to bring compliance practices closer to software development teams.",
    )
    add_para(doc, "Keywords: Privacy by Design; LGPD; static analysis; privacy; software development.", first_indent=False)
    page_break(doc)

    add_title_page_heading(doc, "LISTA DE ABREVIATURAS E SIGLAS")
    for sigla, desc in (
        ("ABNT", "Associação Brasileira de Normas Técnicas"),
        ("GDPR", "General Data Protection Regulation"),
        ("LGPD", "Lei Geral de Proteção de Dados Pessoais"),
        ("PbD", "Privacy by Design"),
        ("SDLC", "Software Development Life Cycle"),
    ):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(sigla)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(12)
        p.add_run("\t" + desc)
    page_break(doc)

    add_title_page_heading(doc, "SUMÁRIO")
    add_toc_field(doc)
    page_break(doc)


def add_heading_manual(doc, level, number, text):
    style_name = "1-Título" if level == 1 else "1.1-Título"
    try:
        p = doc.add_paragraph(style=style_name)
    except Exception:
        p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(12 if level > 1 else 0)
    p.paragraph_format.space_after = Pt(6)
    rendered = f"{number} {text.upper() if level == 1 else text}".strip()
    run = p.add_run(rendered)
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(12)


def add_body(doc, blocks):
    chapter_no = 0
    section_no = 0
    subsection_no = 0
    for kind, text in blocks:
        if not text:
            continue
        if kind == "chapter":
            chapter_no += 1
            section_no = 0
            subsection_no = 0
            add_heading_manual(doc, 1, str(chapter_no), text)
        elif kind == "section":
            section_no += 1
            subsection_no = 0
            add_heading_manual(doc, 2, f"{chapter_no}.{section_no}", text)
        elif kind == "subsection":
            subsection_no += 1
            add_heading_manual(doc, 2, f"{chapter_no}.{section_no}.{subsection_no}", text)
        elif kind in ("number", "bullet"):
            style_name = "List Number" if kind == "number" else "List Bullet"
            try:
                p = doc.add_paragraph(style=style_name)
            except Exception:
                p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(text)
            run.font.name = "Arial"
            run.font.size = Pt(12)
        else:
            add_para(doc, text)


def add_references(doc, references):
    page_break(doc)
    add_heading_manual(doc, 1, "", "REFERÊNCIAS")
    for ref in references:
        add_para(doc, ref, first_indent=False)


def main():
    blocks, references = extract_latex_content()
    doc = Document(str(TEMPLATE))
    clear_document(doc)
    set_default_format(doc)

    add_cover(doc)
    add_title_sheet(doc)
    add_exam_sheet(doc)
    add_pretext(doc)

    section = doc.add_section(WD_SECTION_START.NEW_PAGE)
    section.header.is_linked_to_previous = False
    set_page_numbering(section)
    add_body(doc, blocks)
    add_references(doc, references)

    doc.save(str(OUT))
    print(OUT)


if __name__ == "__main__":
    main()
