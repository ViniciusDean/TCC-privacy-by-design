CREATE TABLE titulares_protegidos (
    id INTEGER PRIMARY KEY,
    email_hash TEXT,
    cpf_hash TEXT,
    deleted_at TIMESTAMP,
    expires_at TIMESTAMP,
    consentimento BOOLEAN
);
