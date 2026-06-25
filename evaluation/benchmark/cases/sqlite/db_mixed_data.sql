CREATE TABLE cadastro_completo (
    id INTEGER PRIMARY KEY,
    email TEXT,
    cpf TEXT,
    telefone TEXT,
    status TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
    expires_at TIMESTAMP,
    consentimento BOOLEAN
);
