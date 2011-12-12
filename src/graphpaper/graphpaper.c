#include "CuTest.h"

void TestMeta(CuTest* tc){
    CuAssert(tc, "Fail! I mean, win on the fail... what?", 1 == 1 + 0);
}

