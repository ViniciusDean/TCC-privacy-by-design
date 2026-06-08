import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.logging.Logger;
import org.springframework.web.client.RestTemplate;

public class ExemploCorreto {
    private static final Logger logger =
        Logger.getLogger(ExemploCorreto.class.getName());

    private String email = "";
    private String cpf = "";
    private final String userId;

    public ExemploCorreto(String email, String cpf, String userId) {
        // Atribuições diretas de parâmetros do construtor não são tratadas
        // isoladamente como falhas de armazenamento.
        this.email = email;
        this.cpf = cpf;
        this.userId = userId;
    }

    public byte[] gerarHashSeguro(String valor) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        return digest.digest(valor.getBytes(StandardCharsets.UTF_8));
    }

    public void registrarOperacao() {
        // Apenas um identificador técnico é registrado.
        logger.info("Operação concluída para userId: " + userId);
    }

    public void enviarDadosAnonimizados(DadosAnonimizados dadosAnonimizados) {
        // O próprio nome documenta que o payload já foi anonimizado.
        new RestTemplate().postForEntity(
            "https://analytics.exemplo.com/metricas",
            dadosAnonimizados,
            Void.class
        );
    }

    public void anonimizar() {
        this.email = "anonimo@exemplo.invalid";
        this.cpf = "000.000.000-00";
    }
}
