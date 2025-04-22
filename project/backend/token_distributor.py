import datetime
from hashlib import sha256
from myrsa import GenerateRsaKey
from myjwt import create_access_token,verfiy_access_token,get_decoded_token_data

current_key = None
key_expire_date = None
valid_minutes_time = 50

alg = {
  "alg": "RSA256",
  "typ": "JWT"
}

def init_token_key():
    global current_key
    global key_expire_date
    current_key = GenerateRsaKey()
    key_expire_date = datetime.datetime.now() + datetime.timedelta(minutes = valid_minutes_time)

def is_valid_key():
    if current_key == None or key_expire_date < datetime.datetime.now():
        return False
    return True

def give_access_token(payload):
    if not is_valid_key():
        init_token_key()

    current_time = datetime.datetime.now()
    unix_time = int(current_time.timestamp())
    payload['iat'] = f'{unix_time}'

    user_token = create_access_token(alg, payload, rsa_key=current_key)
    
    return user_token

def validate_access_token(token):
    if not is_valid_key():
        return False
    if token is None:
        return False
    if is_token_expired(token):
        return False
    if not verfiy_access_token(token, current_key):
        return False
    
    return True

def is_token_expired(token):
    header,payload = get_decoded_token_data(token)
    unix_time = float(payload['iat'])
    activation_date = datetime.datetime.fromtimestamp(unix_time)
    
    if activation_date + datetime.timedelta(minutes = valid_minutes_time) > datetime.datetime.now():
        return False
    
    return True

def give_token_payload(token):
    header,payload = get_decoded_token_data(token)
    return payload