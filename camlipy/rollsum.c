#include "rollsum.h"
#include <stdint.h>
#include <memory.h>
#include <stdlib.h>
#include <stdio.h>

#define CHAR_OFFSET 31
#define BLOB_BITS (13)
#define BLOB_SIZE (1 << BLOB_BITS)


Rollsum *new_Rollsum() {
    Rollsum *r;
    r = (Rollsum *) malloc(sizeof(Rollsum));
    r->s1 = BUP_WINDOWSIZE * CHAR_OFFSET;
    r->s2 = BUP_WINDOWSIZE * (BUP_WINDOWSIZE-1) * CHAR_OFFSET;
    r->wofs = 0;
    memset(r->window, 0, BUP_WINDOWSIZE);
    return r;
}

void delete_Rollsum(Rollsum *r) {
    free(r);
}

void Rollsum_add(Rollsum *r, uint8_t drop, uint8_t add) {
    r->s1 += add - drop;
    r->s2 += r->s1 - (BUP_WINDOWSIZE * (drop + CHAR_OFFSET));
}

void  Rollsum_roll(Rollsum *r, uint8_t ch) {
    Rollsum_add(r, r->window[r->wofs], ch);
    r->window[r->wofs] = ch;
    r->wofs = (r->wofs + 1) % BUP_WINDOWSIZE;
}

uint32_t Rollsum_digest(Rollsum *r)
{
    return (r->s1 << 16) | (r->s2 & 0xffff);
}

uint32_t Rollsum_bits(Rollsum * r)
{
    unsigned rsum = Rollsum_digest(r);
    int bits = BLOB_BITS;
    rsum >>= BLOB_BITS;
    for (bits = BLOB_BITS; (rsum >>= 1) & 1; (bits)++)
        ;
    return bits;
}

unsigned int Rollsum_on_split(Rollsum *r)
{
    if ((r->s2 & (BLOB_SIZE-1)) == ((~0) & (BLOB_SIZE-1)))
        return 1;
    return 0;
}
