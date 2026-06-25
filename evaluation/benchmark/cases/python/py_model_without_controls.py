class Usuario:
    cpf = None

    def atualizar(self, request):
        self.cpf = request.get_cpf()
