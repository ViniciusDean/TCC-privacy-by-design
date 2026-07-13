class Model:
    pass


class Usuario(Model):
    cpf = None

    def atualizar(self, request):
        self.cpf = request.get_cpf()
