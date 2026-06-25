CREATE TABLE contatos (
    id INTEGER PRIMARY KEY,
    email_hash TEXT,
    deleted_at TIMESTAMP,
    consentimento BOOLEAN
);
