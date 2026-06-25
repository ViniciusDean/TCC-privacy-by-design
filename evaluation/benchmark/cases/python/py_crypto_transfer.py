import hashlib
import requests


def enviar(email):
    hashlib.md5(email.encode()).hexdigest()
    requests.post("https://terceiro.example", json={"email": email})
