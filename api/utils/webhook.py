import hashlib
import hmac
import os


def get_signature_sections(signature):
    """
    Gets the individual sections of X-Stitch-Signature as a dictionary object
    """
    signature_parts = signature.split(',')
    parsed_signature = {}

    for signature_part in signature_parts:
        sections = signature_part.split('=')
        parsed_signature[sections[0]] = sections[1]

    return parsed_signature


def calculate_hmac_signature(to_sign):
    """
    Calculate the HMAC SHA256 hash from the input string
    Will read the secret key from environment variables
    """
    secret = os.environ['WEBHOOK_SECRET_KEY'].encode('utf-8')
    signature = hmac.new(secret, to_sign.encode('utf-8'), hashlib.sha256)

    return signature.hexdigest()


def compare_signatures(calculated_signature, incoming_signature):
    """
    Compares the computed HMAC SHA256 hash with the one in X-Stitch-Signature
    Tries to first use compare_digest() to reduce vulnerability to timing attacks
    Falls back to regular string comparison if it's not available
    https://docs.python.org/3/library/hmac.html#hmac.HMAC.hexdigest
    """
    try:
        return hmac.compare_digest(calculated_signature, incoming_signature)
    except AttributeError:
        return calculated_signature == incoming_signature
