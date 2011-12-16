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

/*
Call on GPFiles before exiting to release them.
*/
void GPFile_Close(GPFile* gpfile){
    /* close sqlite connection */
    sqlite3_close(gpfile->connection);
    /* free file object */
    free(gpfile);
}

/*
Returns the number of cards in the GraphPaper file/
*/
int GPFile_NumCards(GPFile* gpfile){
    int rc;
    int numcards;
    sqlite3_stmt* stmt;
    /* create statement 'select count() from cards' */
    rc = sqlite3_prepare_v2(
        gpfile->connection,
        "select count() from cards",
        -1,
        &stmt,
        NULL
    );
    /* I'm just going to assume it succeeded, since it has no reason not to */
    /* run the statement */
    numcards = 0;
    while(SQLITE_DONE != rc){
        rc = sqlite3_step(stmt);
        if(SQLITE_ROW == rc){
            numcards = sqlite3_column_int(stmt, 0);
        }
    }
    /* now clean stuff up */
    sqlite3_finalize(stmt); /* assume it succeeds */
    return numcards;
}


void TestSample(CuTest* tc){
    /* open file */
    GPFile* gpfile;
    if(GP_OK != GPFile_Open("sample.database", &gpfile)){
        CuFail(tc, "Failed to open sample database? What?");
    }
    /* test it for stuff */
    CuAssert(tc, "Wrong number of cards in sample", 6 == GPFile_NumCards(gpfile));
    /* close it */
    GPFile_Close(gpfile);
}
