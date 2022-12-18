import secrets
import hashlib
import base64


def generate_code_verifier_challenge_pair():
    code_verifier = secrets.token_urlsafe(96)[:43]
    hashed = hashlib.sha256(code_verifier.encode('ascii')).digest()
    encoded = base64.urlsafe_b64encode(hashed)
    code_challenge = encoded.decode('ascii')[:-1]

    return code_verifier, code_challenge
