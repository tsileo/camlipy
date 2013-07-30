# -*- coding: utf-8 -*-
import random
from camlipy.rollsum import Rollsum, WINDOW_SIZE


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
