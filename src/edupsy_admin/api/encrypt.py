import base64
import os
import keyring
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def fernet_from_pw(username: str):
    """Use a password with Fernet to derive a key
    (see https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet)
    """
    password=keyring.get_password("edupsy", username)
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    f = Fernet(key)
    return f

def encrypt(data: bytes, username: str):
    f = fernet_from_pw(username)
    token = f.encrypt(data)
    return token

def decrypt(token: bytes, username: str):
    f = fernet_from_pw(username)
    data=f.decrypt(token)
    return data
