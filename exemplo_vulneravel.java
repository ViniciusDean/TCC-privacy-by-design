import java.net.http.HttpClient;
import java.security.MessageDigest;
import java.util.logging.Logger;
import org.springframework.web.client.RestTemplate;

public class ExemploVulneravel {
    private static final Logger logger =
        Logger.getLogger(ExemploVulneravel.class.getName());

    // DADO_HARDCODED: dados pessoais fixos no código-fonte.
    private String cpf = "123.456.789-00";
    private String password = "senha123";

    public byte[] gerarHashFraco(String valor) throws Exception {
        // CRIPTOGRAFIA_FRACA: MD5 não deve proteger dados pessoais.
        MessageDigest digest = MessageDigest.getInstance("MD5");
        return digest.digest(valor.getBytes());
    }

    public void autenticar(String email) {
        // DADO_EM_LOG: dados identificáveis são enviados ao log.
        logger.info("Usuário autenticado: " + email);
        System.out.println("CPF cadastrado: " + cpf);
    }

    public void atualizarCadastro(Requisicao requisicao) {
        // DADO_SEM_CRIPTOGRAFIA: valor recebido é armazenado sem proteção.
        this.cpf = requisicao.getCpf();
    }

    public void cadastrar(
        String nome,
        String email,
        String cpf,
        String telefone,
        String endereco
    ) {
        // COLETA_EXCESSIVA: muitos dados pessoais em uma única operação.
    }

    public void enviarParaTerceiro(String cpf, String email) {
        // TRANSFERENCIA_SEM_BASE_LEGAL: envio externo sem marcador de base legal.
        new RestTemplate().postForEntity(
            "https://analytics.exemplo.com/coleta",
            new DadosPessoais(cpf, email),
            Void.class
        );
    }

    // AUSENCIA_EXCLUSAO: a classe possui dados pessoais, mas não oferece
    // método para excluir ou anonimizar os dados do titular.
}
