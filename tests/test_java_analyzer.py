"""Testes das regras conservadoras de análise estática para Java."""

from pathlib import Path

from code_analyzer import analisar_arquivo, analisar_diretorio


def analisar(tmp_path: Path, codigo: str):
    arquivo = tmp_path / "Exemplo.java"
    arquivo.write_text(codigo, encoding="utf-8")
    return analisar_arquivo(str(arquivo))


def categorias(resultados):
    return [resultado.categoria for resultado in resultados]


def test_detecta_dado_pessoal_hardcoded(tmp_path):
    resultados = analisar(
        tmp_path,
        'class Exemplo { private String cpf = "123.456.789-00"; '
        'public void anonimizar() {} }',
    )

    assert "DADO_HARDCODED" in categorias(resultados)


def test_ignora_inicializacao_vazia_e_null(tmp_path):
    resultados = analisar(
        tmp_path,
        "class Exemplo { private String email = \"\"; private String cpf = null; "
        "public void anonimizar() {} }",
    )

    assert "DADO_HARDCODED" not in categorias(resultados)
    assert "DADO_SEM_CRIPTOGRAFIA" not in categorias(resultados)


def test_ignora_codigo_comentado(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Exemplo {
            // private String cpf = "123.456.789-00";
            /* logger.info(email); */
        }
        """,
    )

    assert resultados == []


def test_detecta_md5_e_sha1(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Exemplo {
            void executar() throws Exception {
                MessageDigest.getInstance("MD5");
                MessageDigest.getInstance("SHA-1");
            }
        }
        """,
    )

    assert categorias(resultados).count("CRIPTOGRAFIA_FRACA") == 2


def test_detecta_digestutils_e_guava_hashing_fracos(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Exemplo {
            void executar(byte[] dados) {
                DigestUtils.md5Hex(dados);
                Hashing.sha1().hashBytes(dados);
            }
        }
        """,
    )

    assert categorias(resultados).count("CRIPTOGRAFIA_FRACA") == 2


def test_detecta_criptografia_fraca_em_instrucao_multilinha(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Exemplo {
            void executar() throws Exception {
                MessageDigest digest = MessageDigest.getInstance(
                    "MD5"
                );
            }
        }
        """,
    )

    assert "CRIPTOGRAFIA_FRACA" in categorias(resultados)


def test_sha256_nao_e_criptografia_fraca(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Exemplo {
            void executar() throws Exception {
                MessageDigest.getInstance("SHA-256");
            }
        }
        """,
    )

    assert "CRIPTOGRAFIA_FRACA" not in categorias(resultados)


def test_detecta_dado_em_logger_e_system_out(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Exemplo {
            void executar(String email, String cpf) {
                logger.info("E-mail: " + email);
                System.out.println("CPF: " + cpf);
            }
        }
        """,
    )

    assert categorias(resultados).count("DADO_EM_LOG") == 2


def test_ignora_mensagem_fixa_e_identificadores_tecnicos_no_log(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Exemplo {
            void executar(String userId, String userAgent, String ipAddress) {
                logger.info("Operação concluída");
                logger.info("Acesso: " + userId + userAgent + ipAddress);
            }
        }
        """,
    )

    assert "DADO_EM_LOG" not in categorias(resultados)


def test_detecta_transferencia_externa_com_dados_pessoais(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Exemplo {
            void enviar(String cpf, String email) {
                new RestTemplate().postForEntity(
                    "https://terceiro.exemplo",
                    new Payload(cpf, email),
                    Void.class
                );
            }
        }
        """,
    )

    assert "TRANSFERENCIA_SEM_BASE_LEGAL" in categorias(resultados)


def test_ignora_transferencia_de_dados_anonimizados(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Exemplo {
            void enviar(DadosAnonimizados dadosAnonimizados) {
                new RestTemplate().postForEntity(
                    "https://terceiro.exemplo", dadosAnonimizados, Void.class
                );
            }
        }
        """,
    )

    assert "TRANSFERENCIA_SEM_BASE_LEGAL" not in categorias(resultados)


def test_ignora_response_entity_body_como_transferencia_externa(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class EnderecoController {
            Object cadastrar(EnderecoDTO dto) {
                return ResponseEntity.status(HttpStatus.CREATED)
                    .body(enderecoService.cadastrarEndereco(dto));
            }
        }
        """,
    )

    assert "TRANSFERENCIA_SEM_BASE_LEGAL" not in categorias(resultados)


def test_detecta_coleta_excessiva_em_metodo(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Exemplo {
            void cadastrar(String nome, String email, String cpf, String telefone) {}
        }
        """,
    )

    assert "COLETA_EXCESSIVA" in categorias(resultados)


def test_detecta_coleta_excessiva_em_construtor(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Usuario {
            Usuario(String nome, String email, String cpf, String telefone) {}
        }
        """,
    )

    assert "COLETA_EXCESSIVA" in categorias(resultados)


def test_detecta_coleta_excessiva_em_record_de_entrada(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        public record UsuarioRequest(
            String nome,
            String email,
            String cpf,
            String celular,
            String senha
        ) {}
        """,
    )

    assert "COLETA_EXCESSIVA" in categorias(resultados)


def test_ignora_record_de_resposta_na_regra_de_coleta(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        public record UsuarioResponseDTO(
            String nome,
            String email,
            String cpf,
            String celular,
            String senha
        ) {}
        """,
    )

    assert "COLETA_EXCESSIVA" not in categorias(resultados)


def test_ignora_coleta_em_seeder_com_dados_sinteticos(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class DataSeeder {
            void criarCliente(String nome, String email, String cpf, String celular) {}
        }
        """,
    )

    assert "COLETA_EXCESSIVA" not in categorias(resultados)


def test_detecta_classe_sem_exclusao(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Usuario {
            private String cpf;
            private String email;
            void salvar() {}
        }
        """,
    )

    assert "AUSENCIA_EXCLUSAO" in categorias(resultados)


def test_aceita_metodo_de_exclusao_ou_anonimizacao(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Usuario {
            private String cpf;
            private String email;
            void anonimizarDados() {
                this.cpf = "000.000.000-00";
                this.email = "anonimo@exemplo.invalid";
            }
        }
        """,
    )

    assert "AUSENCIA_EXCLUSAO" not in categorias(resultados)
    assert "DADO_HARDCODED" not in categorias(resultados)


def test_ignora_name_em_anotacoes_jpa(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Avaliacao {
            @Column(name = "nota_cliente")
            private int notaCliente;

            @JoinColumn(name = "id_usuario")
            private Usuario usuario;

            @JoinTable(
                name = "profissao_profissional",
                joinColumns = @JoinColumn(name = "id_profissional")
            )
            private List<Profissao> profissoes;

            void anonimizar() {}
        }
        """,
    )

    assert "DADO_SEM_CRIPTOGRAFIA" not in categorias(resultados)


def test_ignora_dependencias_injetadas_para_ausencia_exclusao(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class SecurityFilter {
            private final TokenGeneratorService tokenGeneratorService;
            private final PasswordEncoder passwordEncoder;
            private final EnderecoRepository enderecoRepository;
        }
        """,
    )

    assert "AUSENCIA_EXCLUSAO" not in categorias(resultados)


def test_ignora_classes_operacionais_para_ausencia_exclusao(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class UsuarioService {
            private String apiKey;
            private Map<String, String[]> tokensSenha;
        }
        """,
    )

    assert "AUSENCIA_EXCLUSAO" not in categorias(resultados)


def test_detecta_atribuicao_sem_protecao(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Usuario {
            private String cpf;
            Usuario(String cpf) { this.cpf = cpf; }
            void atualizar(Request request) { this.cpf = request.getCpf(); }
            void anonimizar() {}
        }
        """,
    )

    assert categorias(resultados).count("DADO_SEM_CRIPTOGRAFIA") == 1


def test_limita_protecao_nao_evidenciada_a_campos_de_risco_elevado(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Usuario {
            private String nome;
            private String email;
            private String celular;
            private String cpf;
            void atualizar(Request request) {
                this.nome = request.getNome();
                this.email = request.getEmail();
                this.celular = request.getCelular();
                this.cpf = request.getCpf();
            }
            void anonimizar() {}
        }
        """,
    )

    achados = [item for item in resultados if item.categoria == "DADO_SEM_CRIPTOGRAFIA"]
    assert len(achados) == 1
    assert "cpf" in achados[0].descricao


def test_ignora_variaveis_locais_sensiveis_de_fluxo(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class SecurityFilter {
            void filtrar(Request request, TokenGeneratorService tokenGeneratorService) {
                String token = request.getHeader("Authorization").replace("Bearer ", "");
                String email = tokenGeneratorService.validarToken(token);
                boolean emailVerificado = false;
                int anoNascimento = LocalDate.now().getYear();
            }
        }
        """,
    )

    assert "DADO_SEM_CRIPTOGRAFIA" not in categorias(resultados)


def test_ignora_atribuicao_direta_de_parametro_do_construtor(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Usuario {
            private String email;
            Usuario(String email) { this.email = email; }
            void anonimizar() {}
        }
        """,
    )

    assert "DADO_SEM_CRIPTOGRAFIA" not in categorias(resultados)


def test_ignora_valor_protegido_por_criptografia(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Usuario {
            private String passwordHash;
            void salvar(String password) {
                this.passwordHash = passwordEncoder.encode(password);
            }
            void delete() {}
        }
        """,
    )

    assert "DADO_SEM_CRIPTOGRAFIA" not in categorias(resultados)


def test_exemplo_correto_nao_tem_achados():
    assert analisar_arquivo("exemplo_correto.java") == []


def test_exemplo_vulneravel_cobre_as_sete_regras():
    resultados = analisar_arquivo("exemplo_vulneravel.java")

    assert set(categorias(resultados)) == {
        "DADO_HARDCODED",
        "CRIPTOGRAFIA_FRACA",
        "DADO_EM_LOG",
        "TRANSFERENCIA_SEM_BASE_LEGAL",
        "COLETA_EXCESSIVA",
        "AUSENCIA_EXCLUSAO",
        "DADO_SEM_CRIPTOGRAFIA",
    }


def test_linhas_dos_achados_apontam_para_codigo(tmp_path):
    resultados = analisar(
        tmp_path,
        """
        class Exemplo {
            // Comentário antes do campo.
            private String cpf = "123.456.789-00";
            void anonimizar() {}
        }
        """,
    )

    hardcoded = next(
        resultado for resultado in resultados
        if resultado.categoria == "DADO_HARDCODED"
    )
    assert hardcoded.linha == 4
    assert "private String cpf" in hardcoded.trecho


def test_diretorio_analisa_python_e_java(tmp_path):
    (tmp_path / "exemplo.py").write_text(
        'cpf = "123.456.789-00"\n',
        encoding="utf-8",
    )
    (tmp_path / "Exemplo.java").write_text(
        'class Exemplo { String password = "senha123"; void delete() {} }',
        encoding="utf-8",
    )

    resultados = analisar_diretorio(str(tmp_path))

    extensoes = {resultado.arquivo.rsplit(".", 1)[-1] for resultado in resultados}
    assert extensoes == {"py", "java"}
