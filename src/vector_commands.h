#ifndef VALKEY_VECTOR_COMMANDS_H
#define VALKEY_VECTOR_COMMANDS_H

#include "server.h"

/* Vector index structure */
typedef struct vectorIndex {
    void *index;  /* NGT::Index pointer */
    char *path;
    size_t dimension;
    int edge_size_for_creation;
    int edge_size_for_search;
    char *distance_type;
    char *object_type;
    char *graph_type;
    int zero_based_numbering;
} vectorIndex;

/* Function declarations */
void initVectorIndices(void);
vectorIndex *createVectorIndex(const char *name, size_t dimension, 
                              int edge_size_for_creation, int edge_size_for_search,
                              const char *distance_type, const char *object_type,
                              const char *graph_type);
void freeVectorIndex(vectorIndex *vindex);

/* Command functions */
void vectorCreateCommand(client *c);
void vectorInsertCommand(client *c);
void vectorSearchCommand(client *c);
void vectorBuildCommand(client *c);
void vectorRefineCommand(client *c);
void vectorDropCommand(client *c);
void vectorInfoCommand(client *c);
void vectorListCommand(client *c);

#endif /* VALKEY_VECTOR_COMMANDS_H */ 