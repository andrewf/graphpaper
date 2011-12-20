#include "CuTest.h"
#include "GraphPaper.h"

#include <stdlib.h>
#include <string.h> /* for memset */

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
    /* zero out the structure, makes checking easier later */
    memset(gpfile, 0, sizeof(GPFile));
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
    /* macro just for this context, automates all that error crap */
#define PREPARE_STATEMENT(field, sql) \
    do{ \
        rc = sqlite3_prepare_v2(gpfile->connection, sql, -1, &gpfile->field, NULL); \
        if(rc != SQLITE_OK){ goto error_exit; } \
    } while(0)
    /* num cards statement */
    PREPARE_STATEMENT(numcards_stmt, "select count() from cards");
    PREPARE_STATEMENT(numedges_stmt, "select count() from edges");
    /* all good */
    *outfile = gpfile;
    return GP_OK;
    /* go here if stuff went south */
    error_exit:
    if(gpfile->numcards_stmt) { sqlite3_finalize(gpfile->numcards_stmt); }
    if(gpfile->numedges_stmt) { sqlite3_finalize(gpfile->numedges_stmt); }
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
    sqlite3_finalize(gpfile->numedges_stmt);
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

/*
Sets its second param to the number of edges in the file. Return GP_OK
or GP_ERROR
*/
GPError GPFile_NumEdges(GPFile* gpfile, int* out_num){
    int rc;
    *out_num = 0;
    while(SQLITE_DONE != rc){
        rc = sqlite3_step(gpfile->numedges_stmt);
        if(SQLITE_ROW == rc){
            *out_num = sqlite3_column_int(gpfile->numedges_stmt, 0);
        } else {
            return GP_ERROR;
        }
    }
    /* reset it so it can be reused next call */
    if(SQLITE_OK != sqlite3_reset(gpfile->numedges_stmt))
        { return GP_ERROR; }
    return GP_OK;
}

/********************************************************************
 * TESTS
 ********************************************************************/

GPFile* OpenTestFile(CuTest* tc){
    GPFile* gpfile;
    if(GP_OK != GPFile_Open("sample.database", &gpfile)){
        CuFail(tc, "Failed to open sample database? What?");
    }
    return gpfile;
}

void TestNumCards(CuTest* tc){
    /* open file */
    GPFile* gpfile = OpenTestFile(tc);
    /* test it for stuff */
    int num_cards;
    CuAssert(tc, "GPFile_NumCards failed", GPFile_NumCards(gpfile, &num_cards)==GP_OK);
    CuAssert(tc, "Wrong number of cards in sample (should be 6)", 6 == num_cards);
    /* close it */
    GPFile_Close(gpfile);
}

void TestNumEdges(CuTest* tc){
    GPFile* gpfile = OpenTestFile(tc);
    int num_edges;
    /* actual test */
    CuAssert(tc, "GPFile_NumEdges failed", GPFile_NumEdges(gpfile, &num_edges)==GP_OK);
    CuAssert(tc, "Wrong number of cards in sample (should be 4)", 4 == num_edges);
    /* done */
    GPFile_Close(gpfile);
}
