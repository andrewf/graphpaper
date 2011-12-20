#ifndef GRAPHPAPER_H
#define GRAPHPAPER_H

/* Welcome to GraphPaper.h. We're going to start with the data structures,
   then describe the operations on the data structures in the same order. */

#include "sqlite3.h"

#include "GPErrors.h"

typedef struct {
    sqlite3* connection;
    sqlite3_stmt* numcards_stmt;
} GPFile;

typedef struct {
    int id;
    int xpos;
    int ypos;
    int width;
    int height;
    char *title;
    char *text;
    int modified;
} GPCard;

typedef struct {
    int id;
    int modified;
} GPEdgeType;

typedef struct {
    int id;
    GPCard *origin_id;
    GPCard *dest_id;
    GPEdgeType *type;
    int modified;
} GPEdge;


int GPFile_Open(char*, GPFile**);
void GPFile_Close(GPFile*);
GPError GPFile_NumCards(GPFile*, int*);
int GPFile_NumEdges(GPFile*);
char *GPFile_ConfGet(char*); /* or out param? */
void GPFile_ConfSet(char *key, char *value);


GPCard* GPCard_New(GPFile* file);
void GPCard_SetXPos(GPCard* this, int new_x);
void GPCard_SetYPos(GPCard* this, int new_y);
void GPCard_SetWidth(GPCard* this, int new_width);
void GPCard_SetHeight(GPCard* this, int new_height);
void GPCard_SetTitle(GPCard* this, char* new_title);
void GPCard_SetText(GPCard* this, char* new_text);


GPEdgeType* GPEdgeType_New(GPFile* file);
/* etc... */


GPEdge* GPEdge_New(GPFile* file);
void GPCard_SetType(GPEdge* this, GPEdgeType* new_type);
void GPCard_SetOrigin(GPEdge* this, GPCard* new_origin);
void GPCard_SetDest(GPEdge* this, GPCard* new_dest);


#endif

