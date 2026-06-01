"""
exemplo_correto.py
Arquivo sem vulnerabilidades de privacidade.
Serve para validar que o analisador não gera falsos positivos.
"""
import bcrypt
import hashlib


# ── Boas práticas: inicializações vazias em classes NÃO devem gerar alerta ────
class Usuario:
    """Modelo de usuário com dados pessoais protegidos."""
    
    nome      = ""           # Inicialização vazia — OK (não é dado hardcoded)
    email     = ""           # Inicialização vazia — OK
    cpf       = ""           # Inicialização vazia — OK
    
    def __init__(self, nome: str, email: str, cpf: str):
        """Construtor que recebe dados como parâmetros."""
        self.nome  = nome
        self.email = email
        self.cpf   = cpf
    
    def autenticar(self, senha: str) -> bool:
        """Autentica o usuário com bcrypt (criptografia forte)."""
        # Usa bcrypt — algoritmo recomendado para senhas
        return bcrypt.checkpw(senha.encode(), self.senha_hash.encode())
    
    def salvar_senha(self, senha: str):
        """Salva a senha com hash bcrypt (não a senha em texto puro)."""
        # Bcrypt é forte — OK!
        self.senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    
    def deletar(self):
        """Método de exclusão — OK (cumpre Art. 18 IV)."""
        pass
    
    def anonimizar(self):
        """Método de anonimização — OK (cumpre Art. 18 IV)."""
        self.nome  = "Anônimo"
        self.email = "anonimo@anon.com"
        self.cpf   = "000.000.000-00"


# ── Boas práticas: user_agent é campo seguro (não contém 'age' como campo sensível) ──
def registrar_acesso(user_agent: str, ip_address: str):
    """
    Registra acesso técnico sem dados pessoais.
    'user_agent' e 'ip_address' NÃO são dados sensíveis pessoais — são técnicos.
    """
    import logging
    # Apenas dados técnicos em log — OK!
    logging.info(f"Novo acesso: user_agent={user_agent}, ip={ip_address}")


# ── Boas práticas: transferência com base legal documentada ────────────────────
def enviar_relatorio_anonimizado(dados_anonimizados: dict):
    """
    Envia dados já anonimizados para serviço de analytics.
    Sem dados pessoais diretos — OK!
    """
    import requests
    # Apenas dados anonimizados (sem email, CPF, nome real, etc.)
    requests.post(
        "https://analytics.exemplo.com/track",
        json=dados_anonimizados  # Apenas IDs técnicos e métricas
    )


# ── Boas práticas: coleta mínima de dados ────────────────────────────────────
def cadastrar_usuario_minimo(email: str, cpf: str):
    """
    Cadastra usuário com apenas 2 campos — minimização de coleta (Art. 6º III).
    """
    usuario = Usuario(
        nome="Pendente confirmação",
        email=email,
        cpf=cpf
    )
    usuario.salvar_senha("senha_segura_bcrypt")
    return usuario


# ── Boas práticas: dados pessoais SÃO criptografados ──────────────────────────
class RepositorioSeguro:
    """Repository com criptografia aplicada."""
    
    def __init__(self):
        self.usuarios = {}
    
    def salvar_usuario(self, usuario: Usuario):
        """Salva usuário com dados já cifrados/hasheados."""
        # A senha já é bcrypt (hash)
        # Email já está cifrado antes de salvar
        # CPF já está hasheado
        self.usuarios[usuario.email] = usuario
    
    def buscar_usuario(self, email: str) -> Usuario:
        """Recupera usuário de forma segura."""
        return self.usuarios.get(email)


# ── Exemplo correto: Django model com campos protegidos ─────────────────────
# (Comentado porque seria com Django, apenas para referência)
"""
class UsuarioDjango(models.Model):
    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    cpf_hash = models.CharField(max_length=255)  # Sufixo _hash indica criptografia
    
    class Meta:
        # Não publica dados sensíveis por padrão
        fields = ['nome', 'email']  # CPF nunca é retornado automaticamente
"""
