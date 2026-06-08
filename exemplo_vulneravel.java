import java.security.MessageDigest;
import java.util.logging.Logger;

public class ExemploVulneravel {
    private static final Logger logger = Logger.getLogger(ExemploVulneravel.class.getName());

    // Dado pessoal fixo no codigo.
    private String cpf = "123.456.789-00";
    private String password = "senha123";

    public byte[] gerarHashFraco(String valor) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("MD5");
        return digest.digest(valor.getBytes());
    }

    public void autenticar(String email) {
        logger.info("Usuario autenticado: " + email);
        System.out.println("CPF cadastrado: " + cpf);
    }
}
