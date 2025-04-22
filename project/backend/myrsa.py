import secrets
import gmpy2

def GenerateRandomNumber(num_bytes=256): 
    random_bytes = secrets.token_bytes(num_bytes)
    random_bits = gmpy2.mpz.from_bytes(random_bytes, byteorder='big')

    msb_mask = (1 << (num_bytes * 8 - 1))
    second_bit_mask = msb_mask >> 1
    random_bits |= msb_mask | second_bit_mask | 1

    return random_bits

def miller_rabin(number_to_test, iterations=40) -> bool:

    exponent = 0
    odd_part = number_to_test - 1

    while odd_part & 1 == 0:
        exponent += 1
        odd_part = odd_part >> 1

    for _ in range(iterations):
        base = GenerateRandomNumber() % (number_to_test - 2) + 2
        x = pow(base, odd_part, number_to_test)

        if x == 1 or x == number_to_test - 1:
            continue
        for _ in range(exponent - 1):
            x = pow(x, 2, number_to_test)
            if x == number_to_test - 1:
                break
        else:
            return False

    return True

def tal_rabin(random_bits):
    lowPrimes = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503, 509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607, 613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691, 701, 709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787, 797, 809, 811, 821, 823, 827, 829, 839, 853, 857, 859, 863, 877, 881, 883, 887, 907, 911, 919, 929, 937, 941, 947, 953, 967, 971, 977, 983, 991, 997]   
    for prime in lowPrimes:
        if (random_bits % prime == 0):
            return False
    return True

def GeneratePrimeNumber(num_bytes=256):
    random_bits = GenerateRandomNumber(num_bytes)
    flag = tal_rabin(random_bits) and miller_rabin(random_bits)
    while not flag:
        random_bits += 2
        flag = tal_rabin(random_bits) and miller_rabin(random_bits)

    return random_bits
 
 
def GenerateRsaKey(num_bytes=256):
    e = gmpy2.mpz(65537) # this is the public exponent which is a spacial prime
    flag = False

    while not flag:
        q = GeneratePrimeNumber(num_bytes) 
        p = GeneratePrimeNumber(num_bytes)
        N = q * p # this is the modulus
        phi_n = (p-1)*(q-1) # Euler's totient function 

        flag = N % e != 0 and phi_n % e != 0 # only if e is a coprime with N and phi_n

    d = pow(e, -1, phi_n) # this is the private exponent which is a modular multiplicative inverse of e modulo φ(n)

    rsa_key = {
        'N': N,
        'e': e,
        'd': d
    }

    return rsa_key


def RSA_encrypt(messege, e, N):
    return pow(messege, e, N)

def RSA_decrypt(cipher, d, N):
    return pow(cipher, d, N)
