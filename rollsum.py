# -*- coding: utf-8 -*-
""" Port of the original Rollsum code from Golang
    https://github.com/bradfitz/camlistore/blob/master/pkg/rollsum/rollsum.go
"""

WINDOW_SIZE = 64
CHAR_OFFSET = 31

BLOB_BITS = 13
BLOB_SIZE = 1 << BLOB_BITS


class Rollsum(object):
    def __init__(self):
        self.s1 = WINDOW_SIZE * CHAR_OFFSET
        self.s2 = WINDOW_SIZE * (WINDOW_SIZE - 1) * CHAR_OFFSET
        self.window = [0] * WINDOW_SIZE
        self.wofs = 0

    def add(self, drop, add):
        self.s1 += add - drop
        self.s2 += self.s1 - WINDOW_SIZE * int(drop + CHAR_OFFSET)

    def roll(self, ch):
        self.add(self.window[self.wofs], ch)
        self.window[self.wofs] = ch
        self.wofs = (self.wofs + 1) % WINDOW_SIZE

    def on_split(self):
        return (self.s2 & (BLOB_SIZE - 1)) == \
               (4294967295 & (BLOB_SIZE - 1))

    def on_split_with_bits(self, n):
        mask = (1 << n) - 1
        return self.s2 & mask == 4294967295 & mask

    def bits(self):
        bits = BLOB_BITS
        rsum = self.digest()
        rsum >>= BLOB_BITS
        while ((rsum >> 1) & 1) != 0:
            rsum >>= 1
            bits += 1
        return bits

    def digest(self):
        return (self.s1 << 16) | (self.s2 & 0xffff)

import random


def test_rollsum():
    buf = []
    for i in range(100000):
        buf.append(random.randint(0, 255))

    def rsum(offset, length):
        """ Test function that returns Rollsum digest. """
        rs = Rollsum()
        for b in buf[offset:length]:
            rs.roll(b)
        return rs.digest()

    sum1a = rsum(0, len(buf))
    sum1b = rsum(1, len(buf))
    assert sum1a == sum1b

    sum2a = rsum(len(buf) - WINDOW_SIZE * 5 / 2, len(buf) - WINDOW_SIZE)
    sum2b = rsum(0, len(buf) - WINDOW_SIZE)
    assert sum2a == sum2b

    sum3a = rsum(0, WINDOW_SIZE + 3)
    sum3b = rsum(3, WINDOW_SIZE + 3)
    assert sum3a == sum3b


def benchmark_rollsum():
    bytes_size = 1024 * 1024 * 5
    rs = Rollsum()
    splits = 0
    for i in range(bytes_size):
        rs.roll(random.randint(0, 255))
        if rs.on_split():
            rs.bits()
            splits += 1

    every = int(bytes_size / splits)
    print 'num splits: {0}; every {1} bytes.'.format(splits, every)

if __name__ == '__main__':
    test_rollsum()
    benchmark_rollsum()
