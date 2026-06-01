"""
exemplo_parcial.py
Arquivo com boas práticas parciais — mistura de código correto e incorreto.
Demonstra implementação incompleta de medidas de privacidade.
"""
import bcrypt
import hashlib
import logging
import json


# ── Boas práticas: senha com bcrypt (OK) ────────────────────────────────────
class Usuario:
    """Classe usuário com algumas proteções implementadas."""
    
    def __init__(self, email: str, nome: str):
        self.email = email
        self.nome = nome
        self.senha_hash = None
    
    def definir_senha(self, senha: str):
        """Usa bcrypt — algoritmo forte ✅"""
        self.senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    
    # ❌ MAS PROBLEMA: log expõe email (dado pessoal) mesmo com bcrypt
    def autenticar(self, senha: str) -> bool:
        """Autentica mas registra em log — VULNERÁVEL."""
        if bcrypt.checkpw(senha.encode(), self.senha_hash.encode()):
            # PROBLEMA: logging.info registra dados pessoais (email)
            logging.info(f"Usuário {self.email} autenticado com sucesso")
            return True
        else:
            logging.info(f"Falha de autenticação para {self.email}")
            return False


# ── Problema: CPF hardcoded mesmo com criptografia ──────────────────────────
cpf_usuario = "123.456.789-00"  # ❌ Dado hardcoded (mesmo que depois seja criptografado)

# Depois criptografa (mas já expôs no código)
cpf_hash = hashlib.sha256(cpf_usuario.encode()).hexdigest()


# ── Boas práticas: soft delete implementado ✅ ─────────────────────────────
class Repository:
    """Repository com exclusão lógica (soft delete)."""
    
    def __init__(self):
        self.usuarios = {}
        self.deleted_usuarios = {}
    
    def salvar(self, usuario: Usuario):
        """Salva novo usuário."""
        self.usuarios[usuario.email] = usuario
    
    def deletar(self, email: str):
        """Soft delete — move para tabela de deletados ✅"""
        if email in self.usuarios:
            self.deleted_usuarios[email] = self.usuarios.pop(email)
            logging.info(f"Usuário deletado: {email}")  # ❌ Expõe email
    
    # ❌ PROBLEMA: retorna objeto completo com dados sensíveis sem filtragem
    def listar_usuarios(self):
        """Retorna objetos completos — expõe TODOS os dados ❌"""
        return self.usuarios.values()


# ── Problema: coleta parcialmente excessiva ────────────────────────────────
def cadastrar_usuario_simples(email: str, nome: str, cpf: str, telefone: str):
    """
    Coleta 4 campos sensíveis.
    ✅ Poderia ser menor (só email + nome)
    ❌ Mas está bem documentada a finalidade (resgistro básico)
    """
    usuario = Usuario(email, nome)
    # cpf e telefone coletados mas não usados aqui
    return usuario


# ── Boas práticas: sem dados sensíveis em logs técnicos ✅ ──────────────────
def processar_pagamento(valor: float, usuario_id: str):
    """
    Usa ID técnico (UUID) em lugar de CPF.
    Log contém só dados técnicos ✅
    """
    logging.info(f"Processando pagamento de R${valor:.2f} para usuario_id={usuario_id}")
    # (resto do processamento...)


# ── Problema: serialização expõe dados ❌ ────────────────────────────────────
def exportar_usuario_json(usuario: Usuario) -> str:
    """
    ❌ Serializa TUDO, incluindo senha_hash (sensível)
    Melhor: usar pydantic ou manualmente filtrar campos
    """
    return json.dumps(usuario.__dict__)  # Expõe TUDO


# ── Boas práticas: filtro de campos sensíveis ✅ ───────────────────────────
def exportar_usuario_seguro(usuario: Usuario) -> str:
    """
    ✅ Filtra apenas campos públicos
    Senha_hash NÃO é incluída
    """
    return json.dumps({
        'email': usuario.email,
        'nome': usuario.nome
        # senha_hash NÃO incluído
    })


# ── Status: Parcialmente implementado
# ✅ Senhas com bcrypt
# ✅ Soft delete
# ✅ IDs técnicos para logs
# ✅ Filtragem de serialização
# ❌ Ainda expõe dados em alguns logs
# ❌ CPF hardcoded no início
# ❌ Coleta poderia ser menor
