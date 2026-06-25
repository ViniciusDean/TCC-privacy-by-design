import hashlib


def proteger(email):
    email_hash = hashlib.sha256(email.encode()).hexdigest()
    return email_hash
