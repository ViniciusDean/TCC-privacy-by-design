"""
Create a small external workspace for manual VS Code extension testing.

The generated folder is intentionally outside the extension project so the
Extension Development Host opens a normal user project, not the scanner source.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = Path.home() / "OneDrive" / "Documents" / "privacy-scanner-testes"


def copy_examples(target: Path) -> None:
    for filename in (
        "exemplo_vulneravel.py",
        "exemplo_correto.py",
        "exemplo_parcial.py",
        "exemplo_vulneravel.java",
        "exemplo_correto.java",
    ):
        shutil.copy2(PROJECT_ROOT / filename, target / filename)

    vulnerable_examples = target / "novos_exemplos_vulneraveis"
    shutil.copytree(
        PROJECT_ROOT / "examples" / "vulnerable",
        vulnerable_examples,
        dirs_exist_ok=True,
    )


def create_vulnerable_database(target: Path) -> None:
    db_path = target / "banco_vulneravel.db"
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE usuarios (
                cpf TEXT PRIMARY KEY,
                nome TEXT,
                email TEXT,
                telefone TEXT,
                endereco TEXT,
                status TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE pagamentos (
                id INTEGER PRIMARY KEY,
                cartao TEXT,
                cvv TEXT,
                nome_titular TEXT,
                valor REAL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def write_readme(target: Path) -> None:
    (target / "README_TESTE.md").write_text(
        """# Workspace de Teste - Privacy Scanner LGPD

Use esta pasta para testar a extensao VS Code sem abrir o proprio projeto da extensao.

Arquivos:

- `exemplo_vulneravel.py`: deve gerar vulnerabilidades.
- `exemplo_correto.py`: deve gerar poucos ou nenhum alerta.
- `exemplo_parcial.py`: deve gerar achados intermediarios.
- `exemplo_vulneravel.java`: exemplo Java cobrindo as sete categorias.
- `exemplo_correto.java`: exemplo Java sem alertas esperados.
- `novos_exemplos_vulneraveis/`: cenarios adicionais de cadastro de clientes,
  folha de pagamento e prontuario Java.
- `banco_vulneravel.db`: banco SQLite com schema propositalmente vulneravel.

Comandos no VS Code:

- `Privacy Scanner: Analisar arquivo atual`
- `Privacy Scanner: Analisar projeto inteiro`
- `Privacy Scanner: Analisar banco SQLite`
- `Privacy Scanner: Exportar relatorio HTML`
- `Privacy Scanner: Exportar relatorio JSON`
""",
        encoding="utf-8",
    )


def main() -> None:
    target = DEFAULT_TARGET
    target.mkdir(parents=True, exist_ok=True)
    copy_examples(target)
    create_vulnerable_database(target)
    write_readme(target)
    print(f"Workspace de teste criado em: {target}")


if __name__ == "__main__":
    main()
