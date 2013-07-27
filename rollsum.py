# -*- coding: utf-8 -*-

WINDOW_SIZE = 64
CHAR_OFFSET = 31

BLOB_BITS = 13
BLOB_SIZE = 1 << BLOB_BITS


class Rollsum(object):
    def __init__(self):
        self.s1 = WINDOW_SIZE * CHAR_OFFSET
        self.s2 = WINDOW_SIZE * (WINDOW_SIZE -1) * CHAR_OFFSET
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
        return (self.s2 & (BLOB_SIZE - 1)) == (4294967295 & (BLOB_SIZE - 1))  # 4294967295 => ??

    def on_split_with_bits(self, n):
        mask = (1 << n) - 1
        return self.s2 & mask == 4294967295 & mask  # ^0 => ??

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
