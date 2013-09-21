#include <stdint.h>
#define BUP_WINDOWSIZE (64)

#ifndef ROLLSUM_H
#define ROLLSUM_H

typedef struct {
    unsigned s1, s2;
    uint8_t window[BUP_WINDOWSIZE];
    int wofs;
} Rollsum;

#endif
