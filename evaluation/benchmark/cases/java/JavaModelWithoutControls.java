@interface Entity {}

@Entity
class Usuario {
    private String cpf;

    void atualizar(Request request) {
        this.cpf = request.getCpf();
    }
}
