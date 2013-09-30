from cffi import FFI

WINDOW_SIZE = 64


def get_rollsum():
    ffi = FFI()
    ffi.cdef("""
    typedef struct {
        unsigned s1, s2;
        uint8_t window[64];
        int wofs;
    } Rollsum;
    Rollsum *new_Rollsum();
    void delete_Rollsum(Rollsum *r);
    void Rollsum_add(Rollsum *r, unsigned int drop, unsigned int add);
    void  Rollsum_roll(Rollsum *r, unsigned int ch);
    unsigned int Rollsum_digest(Rollsum *r);
    unsigned int Rollsum_bits(Rollsum * r);
    int Rollsum_on_split(Rollsum *r);
    """)
    lib = ffi.dlopen('/work/opensource/camlipy/camlipy/rollsum.so')
    return lib


class Rollsum(object):
    def __init__(self):
        self._rollsum = get_rollsum()
        self.rollsum = self._rollsum.new_Rollsum()

#    def destroy(self):
#        self._rollsum.delete_Rollsum(self.rollsum)

    def add(self, drop, add):
        self._rollsum.Rollsum_add(self.rollsum, drop, add)

    def roll(self, ch):
        """ rs.roll(ord(tf.read(1))) """
        self._rollsum.Rollsum_roll(self.rollsum, ch)

    def on_split(self):
        return self._rollsum.Rollsum_on_split(self.rollsum)

    def bits(self):
        return self._rollsum.Rollsum_bits(self.rollsum)

    def digest(self):
        return self._rollsum.Rollsum_digest(self.rollsum)
