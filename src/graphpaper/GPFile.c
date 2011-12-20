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
    int rc;
    if(0 == filename){
        rc = sqlite3_open(":memory:", &(gpfile->connection));
    } else {
        rc = sqlite3_open(filename, &(gpfile->connection));
    }
    if(SQLITE_OK != rc){
        return GP_ERROR;
    }
    /* prepare statements */
    /* num cards statement */
    rc = sqlite3_prepare_v2(
        gpfile->connection,
        "select count() from cards",
        -1,
        &gpfile->numcards_stmt,
        NULL
    );
    if(rc != SQLITE_OK){
        goto error_exit;
    }
    /* all good */
    *outfile = gpfile;
    return GP_OK;
    /* go here if stuff went south */
    error_exit:
    sqlite3_close(gpfile->connection);
    free(gpfile);
    return GP_ERROR;
}

/*
Call on GPFiles before exiting to release them.
*/
void GPFile_Close(GPFile* gpfile){
    /* delete prepared statements */
    sqlite3_finalize(gpfile->numcards_stmt);
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
    /* run the statement */
    *out_num = 0;
    while(SQLITE_DONE != rc){
        rc = sqlite3_step(gpfile->numcards_stmt);
        if(SQLITE_ROW == rc){
            *out_num = sqlite3_column_int(gpfile->numcards_stmt, 0);
        } else {
            return GP_ERROR;
        }
    }
    /* now clean stuff up */
    if(SQLITE_OK != sqlite3_reset(gpfile->numcards_stmt))
        { return GP_ERROR; }
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
