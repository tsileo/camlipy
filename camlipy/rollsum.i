%module rollsum

%{
#define SWIG_FILE_WITH_INIT
#include "rollsum.h"
%}

typedef struct {
    unsigned s1, s2;
    uint8_t window[BUP_WINDOWSIZE];
    int wofs;
    %extend {
    	Rollsum();
    	~Rollsum();
    	void add(int drop, int add);
    	void roll(int ch);
    	int digest();
    	int bits();
    	int on_split();
    }
} Rollsum;
