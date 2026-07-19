import java.security.MessageDigest;
import java.util.logging.Logger;
import org.springframework.web.client.RestTemplate;

@Entity
public class ProntuarioVulneravel {
    private static final Logger logger =
        Logger.getLogger(ProntuarioVulneravel.class.getName());

    // Dados fictícios fixos no código.
    private String cpf = "123.456.789-00";
    private String diagnostico = "condicao-clinica-ficticia";

    public byte[] gerarIdentificadorLegado(String cpf) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-1");
        return digest.digest(cpf.getBytes());
    }

    public void registrarAcesso(String email, String cpf) {
        logger.info("Prontuario acessado por " + email + " para " + cpf);
    }

    public void atualizar(PacienteRequest request) {
        this.cpf = request.getCpf();
        this.diagnostico = request.getDiagnostico();
    }

    public void cadastrar(
        String nome,
        String email,
        String cpf,
        String telefone,
        String endereco,
        String diagnostico
    ) {
        // Operação com muitos parâmetros pessoais e de saúde.
    }

    public void compartilhar(String cpf, String diagnostico) {
        new RestTemplate().postForEntity(
            "https://laboratorio.exemplo.com/exames",
            new DadosPaciente(cpf, diagnostico),
            Void.class
        );
    }

    public void salvar() {
        // Simula persistência sem fluxo de exclusão ou anonimização.
    }
}
