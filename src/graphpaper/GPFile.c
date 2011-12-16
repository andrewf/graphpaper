#include "CuTest.h"
#include "GraphPaper.h"

#include <stdlib.h>

/*
Opens a GraphPaper file specified by the passed filename, or an
empty file if filename is NULL.
*/
int GPFile_Open(char* filename, GPFile** outfile){
    /* Create GPFile object */
    GPFile* gpfile = (GPFile*) malloc(sizeof(GPFile));
    if(0 == gpfile){
        /* memory fail */
        return GP_ERROR;
    }
    /* open connection */
    int error;
    if(0 == filename){
        sqlite3_open(":memory:", &(gpfile->connection));
    } else {
        sqlite3_open(filename, &(gpfile->connection));
    }
    if(SQLITE_OK != error){
        return GP_ERROR;
    }
    /* all good */
    *outfile = gpfile;
    return GP_OK;
}

void GPFile_Close(GPFile* gpfile){
    /* close sqlite connection */
    sqlite3_close(gpfile->connection);
    /* free file object */
    free(gpfile);
}

void TestSample(CuTest* tc){
    /* open file */
    GPFile* gpfile;
    if(GP_OK != GPFile_Open("sample.database", &gpfile)){
        CuFail(tc, "Failed to open sample database? What?");
    }
    /* test it for stuff */

    /* close it */
    GPFile_Close(gpfile);
}
