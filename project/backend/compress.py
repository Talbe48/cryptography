import struct

def xor1024(a, b):
        return (int.from_bytes(a, byteorder='little') ^ int.from_bytes(b, byteorder='little')).to_bytes(1024, byteorder='little')

def compress(X, Y):
    """ Argon2's compression function G.

    This function is based on Blake2's compression function.
    For the definition, see section 3.4 of Argon2's specification. """
    R = xor1024(X, Y)
    Q = []
    Z = [None]*64
    for i in range(0, 64, 8):
        Q.extend(_P(R[i    *16:(i+1)*16],
                    R[(i+1)*16:(i+2)*16],
                    R[(i+2)*16:(i+3)*16],
                    R[(i+3)*16:(i+4)*16],
                    R[(i+4)*16:(i+5)*16],
                    R[(i+5)*16:(i+6)*16],
                    R[(i+6)*16:(i+7)*16],
                    R[(i+7)*16:(i+8)*16]))
    for i in range(8):
        out = _P(Q[i], Q[i+8], Q[i+16], Q[i+24],
                    Q[i+32], Q[i+40], Q[i+48], Q[i+56])
        for j in range(8):
            Z[i + j*8] = out[j]
    return xor1024(b''.join(Z), R)


def _P(S0, S1, S2, S3, S4, S5, S6, S7):
    """ Permutation used in Argon2's compression function G.

    It is a modification of the permutation used in Blake2.
    See Appendix A of the specification of Argon2. """
    S = (S0, S1, S2, S3, S4, S5, S6, S7)
    v = [None] * 16
    for i in range(8):
        tmp1, tmp2 = struct.unpack_from('<QQ', S[i])
        v[2*i] = tmp1
        v[2*i+1] = tmp2
    _G(v, 0, 4, 8, 12)
    _G(v, 1, 5, 9, 13)
    _G(v, 2, 6, 10, 14)
    _G(v, 3, 7, 11, 15)
    _G(v, 0, 5, 10, 15)
    _G(v, 1, 6, 11, 12)
    _G(v, 2, 7, 8, 13)
    _G(v, 3, 4, 9, 14)
    ret =  [struct.pack("<QQ", v[2*i], v[2*i+1]) for i in range(8)]
    return ret


def _G(v, a, b, c, d):
    """ Quarter-round of the permutation used in the compression of Argon2.

    It is a modification of the quarter-round used in Blake2, which in turn
    is a modification of ChaCha.  See Appendix A of the specification of
    Argon2. """
    va, vb, vc, vd = v[a], v[b], v[c], v[d]
    va = (va + vb + 2 * (va & 0xffffffff) * (vb & 0xffffffff)
                ) & 0xffffffffffffffff
    tmp = vd ^ va
    vd = (tmp >> 32) | ((tmp & 0xffffffff) << 32)
    vc = (vc + vd + 2 * (vc & 0xffffffff) * (vd & 0xffffffff)
                ) & 0xffffffffffffffff
    tmp = vb ^ vc
    vb = (tmp >> 24) | ((tmp & 0xffffff) << 40)
    va = (va + vb + 2 * (va & 0xffffffff) * (vb & 0xffffffff)
                ) & 0xffffffffffffffff
    tmp = vd ^ va
    vd = (tmp >> 16) | ((tmp & 0xffff) << 48)
    vc = (vc + vd + 2 * (vc & 0xffffffff) * (vd & 0xffffffff)
                ) & 0xffffffffffffffff
    tmp = vb ^ vc
    vb = (tmp >> 63) | ((tmp << 1) & 0xffffffffffffffff)
    v[a], v[b], v[c], v[d] = va, vb, vc, vd