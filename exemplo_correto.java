import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.logging.Logger;

public class ExemploCorreto {
    private static final Logger logger = Logger.getLogger(ExemploCorreto.class.getName());

    private final String userId;

    public ExemploCorreto(String userId) {
        this.userId = userId;
    }

    public byte[] gerarHash(String valor) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        return digest.digest(valor.getBytes(StandardCharsets.UTF_8));
    }

    public void registrarOperacao() {
        logger.info("Operacao concluida para identificador tecnico: " + userId);
    }
}
