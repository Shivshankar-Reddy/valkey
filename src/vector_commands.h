#ifndef VALKEY_VECTOR_COMMANDS_H
#define VALKEY_VECTOR_COMMANDS_H

#include "server.h"

/* NGT C API includes - include this first */
#include "../deps/NGT/lib/NGT/Capi.h"

/* NGTQ C API includes - this depends on NGT headers */
#include "../deps/NGT/lib/NGT/NGTQ/Capi.h"

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

/* Quantized vector index structure */
typedef struct quantizedVectorIndex {
    NGTQGIndex index;  /* NGTQG::Index pointer */
    char *path;
    size_t dimension;
    int edge_size_for_creation;
    int edge_size_for_search;
    char *distance_type;
    char *object_type;
    char *graph_type;
    int zero_based_numbering;
    float dimension_of_subvector;
    size_t max_number_of_edges;
} quantizedVectorIndex;

/* Function declarations */
void initVectorIndices(void);
void initQuantizedVectorIndices(void);
vectorIndex *createVectorIndex(client *c, const char *name, size_t dimension, 
                              int edge_size_for_creation, int edge_size_for_search,
                              const char *distance_type, const char *object_type,
                              const char *graph_type);
void freeVectorIndex(vectorIndex *vindex);

/* Quantized vector index functions */
quantizedVectorIndex *createQuantizedVectorIndex(client *c, const char *name, size_t dimension,
                                                int edge_size_for_creation, int edge_size_for_search,
                                                const char *distance_type, const char *object_type,
                                                const char *graph_type, float dimension_of_subvector,
                                                size_t max_number_of_edges);
void freeQuantizedVectorIndex(quantizedVectorIndex *qvindex);

/* Command functions */
void vectorCreateCommand(client *c);
void vectorInsertCommand(client *c);
void vectorSearchCommand(client *c);
void vectorBuildCommand(client *c);
void vectorRefineCommand(client *c);
void vectorDropCommand(client *c);
void vectorInfoCommand(client *c);
void vectorListCommand(client *c);
void vectorBatchInsertCommand(client *c);
void vectorBatchSearchCommand(client *c);
void vectorReconstructGraphCommand(client *c);
void vectorQbgCreateQGCommand(client *c);
void vectorQbgBuildQGCommand(client *c);
void vectorQbgInsertCommand(client *c);

/* NGTQ Command functions */
void vectorQuantizeCommand(client *c);
void vectorQuantizedCreateCommand(client *c);
void vectorQuantizedInsertCommand(client *c);
void vectorQuantizedSearchCommand(client *c);
void vectorQuantizedBuildCommand(client *c);
void vectorQuantizedDropCommand(client *c);
void vectorQuantizedInfoCommand(client *c);
void vectorQuantizedListCommand(client *c);

bool valkey_ngt_reconstruct_graph(const char *input_path, const char *output_path, int outdegree, int indegree, double epsilon, double accuracy, NGTError error);

#endif /* VALKEY_VECTOR_COMMANDS_H */ 