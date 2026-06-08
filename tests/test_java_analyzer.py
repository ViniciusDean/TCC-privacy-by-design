"""Testes da versão inicial do analisador Java."""

from code_analyzer import analisar_arquivo, analisar_diretorio


def test_detects_hardcoded_personal_data(temp_java_file):
    temp_java_file.write('private String cpf = "123.456.789-00";\n')
    temp_java_file.flush()

    results = analisar_arquivo(temp_java_file.name)

    assert any(v.categoria == "DADO_HARDCODED" for v in results)
    assert any(v.risco == "ALTO" for v in results)


def test_ignores_empty_java_initialization(temp_java_file):
    temp_java_file.write('private String email = "";\n')
    temp_java_file.flush()

    results = analisar_arquivo(temp_java_file.name)

    assert not any(v.categoria == "DADO_HARDCODED" for v in results)


def test_detects_java_md5(temp_java_file):
    temp_java_file.write('MessageDigest digest = MessageDigest.getInstance("MD5");\n')
    temp_java_file.flush()

    results = analisar_arquivo(temp_java_file.name)

    assert any(v.categoria == "CRIPTOGRAFIA_FRACA" for v in results)


def test_detects_personal_data_in_java_log(temp_java_file):
    temp_java_file.write('logger.info("Usuario: " + email);\n')
    temp_java_file.flush()

    results = analisar_arquivo(temp_java_file.name)

    assert any(v.categoria == "DADO_EM_LOG" for v in results)


def test_ignores_fixed_log_message_without_personal_variable(temp_java_file):
    temp_java_file.write('logger.info("Email enviado com sucesso");\n')
    temp_java_file.flush()

    results = analisar_arquivo(temp_java_file.name)

    assert not any(v.categoria == "DADO_EM_LOG" for v in results)


def test_java_correct_example_has_no_findings():
    results = analisar_arquivo("exemplo_correto.java")

    assert results == []


def test_directory_analyzes_python_and_java(tmp_path):
    (tmp_path / "exemplo.py").write_text('cpf = "123.456.789-00"\n', encoding="utf-8")
    (tmp_path / "Exemplo.java").write_text(
        'String password = "senha123";\n',
        encoding="utf-8",
    )

    results = analisar_diretorio(str(tmp_path))

    extensions = {v.arquivo.rsplit(".", 1)[-1] for v in results}
    assert extensions == {"py", "java"}
