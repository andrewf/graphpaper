#include "CuTest.h"
#include "GraphPaper.h"

#include <stdlib.h>
#include <string.h> /* for memset */
#include <stdio.h>

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
    PREPARE_STATEMENT(confget_stmt, "select value from config where key = ?");
    /* all good */
    *outfile = gpfile;
    return GP_OK;
    /* go here if stuff went south */
    error_exit:
    if(gpfile->numcards_stmt) { sqlite3_finalize(gpfile->numcards_stmt); }
    if(gpfile->numedges_stmt) { sqlite3_finalize(gpfile->numedges_stmt); }
    if(gpfile->confget_stmt) { sqlite3_finalize(gpfile->confget_stmt); }
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
    sqlite3_finalize(gpfile->confget_stmt);
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
    int rc, done = 0;
    sqlite3_stmt* stmt = gpfile->numcards_stmt;
    /* run the statement */
    *out_num = 0;
    while(!done){
        rc = sqlite3_step(stmt);
        switch(rc){
            case SQLITE_DONE:
                printf("NumCards done\n");
                done = 1;
                break;
            case SQLITE_ROW:
                *out_num = sqlite3_column_int(stmt, 0);
                printf("NumCards row %d\n", *out_num);
                break;
            case SQLITE_BUSY:
                break;
            default:
                printf("NumCards, rc = %d, erroring\n", rc);
                sqlite3_reset(stmt);
                return GP_ERROR;
        }
    }
    /* now clean stuff up */
    if(SQLITE_OK != sqlite3_reset(stmt))
        { return GP_ERROR; }
    return GP_OK;
}

/*
Sets its second param to the number of edges in the file. Return GP_OK
or GP_ERROR
*/
GPError GPFile_NumEdges(GPFile* gpfile, int* out_num){
    int rc, done = 0;
    *out_num = 0;
    sqlite3_stmt* stmt = gpfile->numedges_stmt;
    while(!done){
        rc = sqlite3_step(stmt);
        switch(rc){
            case SQLITE_DONE:
                done = 1;
                break;
            case SQLITE_ROW:
                *out_num = sqlite3_column_int(stmt, 0);
                break;
            case SQLITE_BUSY:
                break;
            default:
                sqlite3_reset(stmt);
                return GP_ERROR;
        }
    }
    /* reset it so it can be reused next call */
    if(SQLITE_OK != sqlite3_reset(stmt))
        { return GP_ERROR; }
    return GP_OK;
}

/*
Set out param to config value. Return GP_KEY_MISSING if the key does not exist,
and set out param to null.
*/
GPError GPFile_ConfGet(GPFile* gpfile, char* key, char** out_value){
    int rc, done = 0;
    *out_value = NULL;
    sqlite3_stmt* stmt = gpfile->confget_stmt;
    /* bind key to first param of statement */
    if(sqlite3_bind_text(stmt, 1, key, -1, SQLITE_TRANSIENT) != SQLITE_OK){ /* length of key is unknown, sqlite should make its own copy */
        return GP_ERROR;
    }
    /* run the statement */
    while(!done){
        rc = sqlite3_step(stmt);
        switch(rc){
            case SQLITE_DONE:
                done = 1;
                break;
            case SQLITE_ROW:
                /* get out the string, copy it */
                *out_value = strdup(sqlite3_column_text(stmt, 0));
                break;
            case SQLITE_BUSY:
                break;
            default:
                sqlite3_reset(stmt);
                goto error_exit;
        }
    }
    /* reset statement (and clear bindings) */
    sqlite3_clear_bindings(stmt);
    if(sqlite3_reset(stmt) != SQLITE_OK)
        return GP_ERROR;
    /* return appropriate value */
    if(0 == *out_value)
        return GP_KEY_MISSING;
    return GP_OK;

    error_exit:
    if(NULL != *out_value)
        { free(*out_value); }
    return GP_ERROR;
}

void GPFree(void* p){
    free(p);
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
    printf("num_cards: %d\n", num_cards);
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

void TestConfGet_KeyPresent(CuTest* tc){
    GPFile* gpfile = OpenTestFile(tc);
    char *value = 0;
    /* actual test */
    CuAssert(tc, "GPFile_ConfGet failed", GPFile_ConfGet(gpfile, "color", &value)==GP_OK);
    CuAssert(tc, "GPFile_ConfGet returned wrong value", strcmp(value, "blue")==0);
    /* done */
    GPFree(value);
    GPFile_Close(gpfile);
}

void TestConfGet_KeyMissing(CuTest* tc){
    GPFile* gpfile = OpenTestFile(tc);
    char *value = (void*)0xdeadbeef;
    /* test */
    CuAssert(tc, "GPFile_ConfGet failed (should return GP_KEY_MISSING)",
                GP_KEY_MISSING == GPFile_ConfGet(gpfile, "ohnoyoudint", &value));
    CuAssert(tc, "GPFile_ConfGet didn't set param to null", 0 == value);
    /* done */
    GPFile_Close(gpfile);
}

