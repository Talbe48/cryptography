import re 
import multiprocessing
import struct
import secrets
from hashlib import blake2b
from six import BytesIO
from compress import compress, xor1024


def ValidateUser(input) -> bool:
    pattern = r'^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z0-9_]{3,12}$'
    if re.match(pattern, input):
        return True
    else:
        return False

def ValidateRePass(truepass, repass) -> bool:
    return truepass == repass

def ValidatePass(input) -> bool:
    pattern = r'^(?=.*[A-Za-z])(?=.*\d)[^\s]{6,25}$'
    if re.match(pattern, input):
        return True
    else:
        return False

def Argon2id(password, salt = None):
    if salt != None:
        return myArgon2id(password, salt)
    
    salt = secrets.token_bytes(32)
    return myArgon2id(password, salt), salt   


def myArgon2id(password, salt):
    parallelism = 4              # Number of prosses
    memory_cost = 4 * 1024         # Memory usage in kibibytes 
    iterations = 2                    # Number of iterations
    hash_length = 32         # Desired hash length in bytes (256 bits)
    password = password.encode('utf-8')
    
    #Memory Matrix Setup
    lane_length = memory_cost // parallelism  
    segment_length = lane_length // 4

    #Compute the pre-hasing digest
    hash = blake2b(digest_size=hash_length)

    hash.update(struct.pack("<IIII", parallelism, hash_length, memory_cost, iterations))
    hash.update(password)
    hash.update(salt)
    #hash.update(key)

    H0 = hash.digest()
    
    #Memory Matrix 
    Memory= []
    for lane_index in range(parallelism):
        new_lane = [None] * lane_length
        Memory.append(new_lane)

    #intalizing prossesrs
    process_pool = multiprocessing.Pool(parallelism)
    
    for t in range(iterations):
        for segment in range(4):

            handles = [None]*parallelism

            for lane_index in range(parallelism):
                handles[lane_index] = process_pool.apply_async(fill_segment, (Memory, t, segment, lane_index, segment_length, H0, lane_length, parallelism))

            for lane_index in range(parallelism):

                new_segment = handles[lane_index].get()            
                for index in range(segment_length):
                    Memory[lane_index][segment * segment_length + index] = new_segment[index]
    if process_pool:
        process_pool.close()

    final_value = b'\0' * 1024

    for lane in range(parallelism):
        final_value = xor1024(final_value, Memory[lane][lane_length-1])
    
    final_hash = blake2b(digest_size=hash_length)
    final_hash.update(final_value)

    return final_hash.digest()

def fill_segment(Memory, t, segment, lane_index, segment_length, H0, lane_length, parallelism):
    for block_segment in range(segment_length):

        block_lane = segment * segment_length + block_segment
        if t == 0 and block_lane < 2:
            Memory[lane_index][block_lane] = blake2b_1024(H0 + struct.pack('<II', block_lane, block_segment))
            continue
        
        J1, J2 = struct.unpack_from('<II', Memory[lane_index][block_lane-1][:8])
        i_prime = lane_index if t == 0 and segment == 0 else J2 % parallelism

        if t == 0:
            if segment == 0 or block_segment == i_prime:
                ref_area_size = block_lane - 1
            elif block_segment == 0:
                ref_area_size = segment * segment_length - 1
            else:
                ref_area_size = segment * segment_length
                
        elif lane_index == i_prime:# same_lane  
            ref_area_size = lane_length - segment_length + block_segment - 1
        elif block_segment == 0:
            ref_area_size = lane_length - segment_length - 1
        else:
            ref_area_size = lane_length - segment_length

        rel_pos = (J1 ** 2) >> 32
        rel_pos = ref_area_size - 1 - ((ref_area_size * rel_pos) >> 32)
        start_pos = 0

        if t != 0 and segment != 3:
            start_pos = (segment + 1) * segment_length
        j_prime = (start_pos + rel_pos) % lane_length

        new_block = compress(Memory[lane_index][(block_lane-1)%lane_length], Memory[i_prime][j_prime])
        if t != 0:
            new_block = xor1024(Memory[lane_index][block_segment], new_block)

        Memory[lane_index][block_lane] = new_block    
    return Memory[lane_index][segment*segment_length:(segment+1)*segment_length]


def blake2b_1024(X):
    buf = BytesIO()
    V = blake2b(X).digest()  # V_1
    buf.write(V[:32])
    todo = 1024 - 32
    while todo > 64:  
        V = blake2b(V).digest()  # V_2, ..., V_r
        buf.write(V[:32])
        todo -= 32

    buf.write(blake2b(V, digest_size=todo).digest())  # V_{r+1}
    return buf.getvalue()
