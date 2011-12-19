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
Sets its second param to the number of cards in the file. Return GP_OK
or GP_ERROR.
*/
GPError GPFile_NumCards(GPFile* gpfile, int* out_num){
    int rc;
    sqlite3_stmt* stmt;
    /* create statement 'select count() from cards' */
    rc = sqlite3_prepare_v2(
        gpfile->connection,
        "select count() from cards",
        -1,
        &stmt,
        NULL
    );
    /* Bail if it failed */
    if(rc != SQLITE_OK){
        sqlite3_finalize(stmt);
        return GP_ERROR;
    }
    /* run the statement */
    *out_num = 0;
    while(SQLITE_DONE != rc){
        rc = sqlite3_step(stmt);
        if(SQLITE_ROW == rc){
            *out_num = sqlite3_column_int(stmt, 0);
        }
    }
    /* now clean stuff up */
    sqlite3_finalize(stmt); /* assume it succeeds */
    return GP_OK;
}


void TestSample(CuTest* tc){
    /* open file */
    GPFile* gpfile;
    if(GP_OK != GPFile_Open("sample.database", &gpfile)){
        CuFail(tc, "Failed to open sample database? What?");
    }
    /* test it for stuff */
    int num_cards;
    CuAssert(tc, "GPFile_NumCards failed", GPFile_NumCards(gpfile, &num_cards)==GP_OK);
    CuAssert(tc, "Wrong number of cards in sample", 6 == num_cards);
    /* close it */
    GPFile_Close(gpfile);
}
