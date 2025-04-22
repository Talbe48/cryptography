import base64
import json
import gmpy2
from hashlib import sha256
from myrsa import RSA_encrypt,RSA_decrypt,GenerateRsaKey


def base64url_encode(data:str) -> str:
    base64_encoded = base64.b64encode(data).decode('utf-8')
    base64url_encoded = base64_encoded.replace('+', '-').replace('/', '_').replace('=', '')
    return base64url_encoded

def base64url_decode(base64url_str: str) -> bytes:
    base64_str = base64url_str.replace('-', '+').replace('_', '/')
    padding = '=' * (4 - len(base64_str) % 4)
    base64_str += padding
    decoded_bytes = base64.b64decode(base64_str)
    return decoded_bytes


def int_to_base64url(n: int) -> str:
    byte_length = (n.bit_length() + 7) // 8
    byte_array = n.to_bytes(byte_length, 'big')

    base64url_bytes = base64.urlsafe_b64encode(byte_array)
    base64url_str = base64url_bytes.decode('utf-8').rstrip('=')

    return base64url_str

def base64url_to_int(base64url_str: str) -> int:
    padding = '=' * (-len(base64url_str) % 4)
    byte_array = base64.urlsafe_b64decode(base64url_str + padding)

    integer = gmpy2.mpz.from_bytes(byte_array, byteorder='big')
    return integer

def jwt_base64url_encode_json(json_data):
    json_data = json.dumps(json_data, separators=(',', ':'))
    byte_data = json_data.encode('utf-8')
    base64url_header = base64url_encode(byte_data)
    return base64url_header

def jwt_base64url_decode_json(base64url_str: str):
    decoded_bytes = base64url_decode(base64url_str)
    decoded_str = decoded_bytes.decode('utf-8')
    json_data = json.loads(decoded_str)
    return json_data

def create_access_token(header:str, payload:str, rsa_key):
    encoded_header = jwt_base64url_encode_json(header)
    encoded_payload = jwt_base64url_encode_json(payload)
    token_body = f"{encoded_header}.{encoded_payload}".encode('utf-8')
    
    token_body = sha256(token_body).digest()
    signature = gmpy2.mpz.from_bytes(token_body, byteorder='big')
    signature = RSA_decrypt(signature,rsa_key['d'],rsa_key['N'])
    encoded_signature= int_to_base64url(signature)
    
    full_token = f"{encoded_header}.{encoded_payload}.{encoded_signature}"
    return full_token

def verfiy_access_token(token:str, rsa_key) -> bool:
    token_body,user_signature = token.rsplit('.', 1)

    hashed_body = sha256(token_body.encode('utf-8')).digest()
    my_signature = gmpy2.mpz.from_bytes(hashed_body, byteorder='big')
    my_signature = RSA_decrypt(my_signature,rsa_key['d'],rsa_key['N'])
    my_signature = int_to_base64url(my_signature)

    return my_signature == user_signature

def user_verfier(token:str, public_key):
    token_body,server_signature = token.rsplit('.', 1)
    hashed_body = sha256(token_body.encode('utf-8')).digest()
    hashed_body = gmpy2.mpz.from_bytes(hashed_body, byteorder='big')

    server_signature = base64url_to_int(server_signature)
    jwt_body = RSA_encrypt(server_signature, public_key['e'], public_key['N'])

    return jwt_body == hashed_body

def get_decoded_token_data(token:str):
    encoded_parts = token.split('.')
    header = jwt_base64url_decode_json(encoded_parts[0])
    payload = jwt_base64url_decode_json(encoded_parts[1])
    
    return (header,payload)
