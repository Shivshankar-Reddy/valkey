#include "server.h"
#include "vector_commands.h"
#include "sds.h"
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <float.h>
#include <unistd.h>
#include <omp.h>

/* NGT C API includes */
#include "../deps/NGT/lib/NGT/Capi.h"
/* NGTQ C API includes */
#include "../deps/NGT/lib/NGT/NGTQ/Capi.h"

/* Global vector indices storage */
static dict *vector_indices = NULL;

/* Initialize vector indices storage */
void initVectorIndices(void) {
    if (vector_indices == NULL) {
        vector_indices = dictCreate(&sdsHashDictType);
    }
}

/* Create a new vector index */
vectorIndex *createVectorIndex(client *c, const char *name, size_t dimension, 
                              int edge_size_for_creation, int edge_size_for_search,
                              const char *distance_type, const char *object_type,
                              const char *graph_type) {
    vectorIndex *vindex = zmalloc(sizeof(vectorIndex));
    
    vindex->dimension = dimension;
    vindex->edge_size_for_creation = edge_size_for_creation;
    vindex->edge_size_for_search = edge_size_for_search;
    vindex->distance_type = sdsnew(distance_type);
    vindex->object_type = sdsnew(object_type);
    vindex->graph_type = sdsnew(graph_type);
    vindex->zero_based_numbering = 1;
    
    /* Create path for the index */
    vindex->path = sdsnew(name);
    
    /* Create NGT property */
    NGTError error = ngt_create_error_object();
    NGTProperty prop = ngt_create_property(error);
    
    if (prop == NULL) {
        addReplyError(c, "Failed to create NGT property");
        ngt_destroy_error_object(error);
        return NULL;
    }
    
    /* Set dimension */
    if (!ngt_set_property_dimension(prop, dimension, error)) {
        addReplyError(c, "Failed to set dimension");
        ngt_destroy_property(prop);
        ngt_destroy_error_object(error);
        return NULL;
    }
    
    /* Set edge sizes */
    if (!ngt_set_property_edge_size_for_creation(prop, edge_size_for_creation, error)) {
        addReplyError(c, "Failed to set edge size for creation");
        ngt_destroy_property(prop);
        ngt_destroy_error_object(error);
        return NULL;
    }
    
    if (!ngt_set_property_edge_size_for_search(prop, edge_size_for_search, error)) {
        addReplyError(c, "Failed to set edge size for search");
        ngt_destroy_property(prop);
        ngt_destroy_error_object(error);
        return NULL;
    }
    
    /* Set object type */
    if (strcmp(object_type, "Float") == 0 || strcmp(object_type, "float") == 0) {
        if (!ngt_set_property_object_type_float(prop, error)) {
            addReplyError(c, "Failed to set object type to float");
            ngt_destroy_property(prop);
            ngt_destroy_error_object(error);
            return NULL;
        }
    } else if (strcmp(object_type, "Byte") == 0 || strcmp(object_type, "byte") == 0) {
        if (!ngt_set_property_object_type_integer(prop, error)) {
            addReplyError(c, "Failed to set object type to byte");
            ngt_destroy_property(prop);
            ngt_destroy_error_object(error);
            return NULL;
        }
    } else {
        addReplyError(c, "Invalid object type");
        ngt_destroy_property(prop);
        ngt_destroy_error_object(error);
        return NULL;
    }
    
    /* Set distance type */
    if (strcmp(distance_type, "L1") == 0) {
        if (!ngt_set_property_distance_type_l1(prop, error)) {
            addReplyError(c, "Failed to set distance type to L1");
            ngt_destroy_property(prop);
            ngt_destroy_error_object(error);
            return NULL;
        }
    } else if (strcmp(distance_type, "L2") == 0) {
        if (!ngt_set_property_distance_type_l2(prop, error)) {
            addReplyError(c, "Failed to set distance type to L2");
            ngt_destroy_property(prop);
            ngt_destroy_error_object(error);
            return NULL;
        }
    } else if (strcmp(distance_type, "Normalized L2") == 0) {
        if (!ngt_set_property_distance_type_normalized_l2(prop, error)) {
            addReplyError(c, "Failed to set distance type to Normalized L2");
            ngt_destroy_property(prop);
            ngt_destroy_error_object(error);
            return NULL;
        }
    } else if (strcmp(distance_type, "Hamming") == 0) {
        if (!ngt_set_property_distance_type_hamming(prop, error)) {
            addReplyError(c, "Failed to set distance type to Hamming");
            ngt_destroy_property(prop);
            ngt_destroy_error_object(error);
            return NULL;
        }
    } else if (strcmp(distance_type, "Jaccard") == 0) {
        if (!ngt_set_property_distance_type_jaccard(prop, error)) {
            addReplyError(c, "Failed to set distance type to Jaccard");
            ngt_destroy_property(prop);
            ngt_destroy_error_object(error);
            return NULL;
        }
    } else if (strcmp(distance_type, "Cosine") == 0) {
        if (!ngt_set_property_distance_type_cosine(prop, error)) {
            addReplyError(c, "Failed to set distance type to Cosine");
            ngt_destroy_property(prop);
            ngt_destroy_error_object(error);
            return NULL;
        }
    } else if (strcmp(distance_type, "Inner Product") == 0) {
        if (!ngt_set_property_distance_type_inner_product(prop, error)) {
            addReplyError(c, "Failed to set distance type to Inner Product");
            ngt_destroy_property(prop);
            ngt_destroy_error_object(error);
            return NULL;
        }
    } else {
        addReplyError(c, "Invalid distance type");
        ngt_destroy_property(prop);
        ngt_destroy_error_object(error);
        return NULL;
    }
    
    /* Create NGT index */
    vindex->index = ngt_create_graph_and_tree(vindex->path, prop, error);
    if (vindex->index == NULL) {
        addReplyError(c, "Failed to create NGT index");
        ngt_destroy_property(prop);
        ngt_destroy_error_object(error);
        return NULL;
    }
    
    ngt_destroy_property(prop);
    ngt_destroy_error_object(error);
    
    return vindex;
}

/* Free vector index */
void freeVectorIndex(vectorIndex *vindex) {
    if (vindex) {
        if (vindex->index) {
            NGTError error = ngt_create_error_object();
            ngt_close_index(vindex->index);
            ngt_destroy_error_object(error);
        }
        sdsfree(vindex->distance_type);
        sdsfree(vindex->object_type);
        sdsfree(vindex->graph_type);
        sdsfree(vindex->path);
        zfree(vindex);
    }
}

/* VECTOR.CREATE command */
void vectorCreateCommand(client *c) {
    if (c->argc < 3) {
        addReplyError(c, "VECTOR.CREATE requires at least index name and dimension");
        return;
    }
    
    /* Ensure vector indices are initialized */
    if (vector_indices == NULL) {
        initVectorIndices();
    }
    
    char *index_name = c->argv[1]->ptr;
    long dimension;
    
    if (getLongFromObjectOrReply(c, c->argv[2], &dimension, NULL) != C_OK) {
        return;
    }
    
    if (dimension <= 0) {
        addReplyError(c, "Dimension must be positive");
        return;
    }
    
    /* Check if index already exists */
    if (dictFind(vector_indices, index_name)) {
        addReplyError(c, "Vector index already exists");
        return;
    }
    
    /* Parse optional parameters */
    int edge_size_for_creation = 10;
    int edge_size_for_search = 40;
    char *distance_type = "L2";
    char *object_type = "Float";
    char *graph_type = "ANNG";
    
    for (int j = 3; j < c->argc; j += 2) {
        if (j + 1 >= c->argc) {
            addReplyError(c, "Invalid number of arguments");
            return;
        }
        
        char *param = c->argv[j]->ptr;
        char *value = c->argv[j + 1]->ptr;
        
        if (!strcasecmp(param, "EDGE_SIZE_FOR_CREATION")) {
            long val;
            if (getLongFromObjectOrReply(c, c->argv[j + 1], &val, NULL) != C_OK) {
                return;
            }
            edge_size_for_creation = val;
        } else if (!strcasecmp(param, "EDGE_SIZE_FOR_SEARCH")) {
            long val;
            if (getLongFromObjectOrReply(c, c->argv[j + 1], &val, NULL) != C_OK) {
                return;
            }
            edge_size_for_search = val;
        } else if (!strcasecmp(param, "DISTANCE_TYPE")) {
            distance_type = value;
        } else if (!strcasecmp(param, "OBJECT_TYPE")) {
            object_type = value;
        } else if (!strcasecmp(param, "GRAPH_TYPE")) {
            graph_type = value;
        } else {
            addReplyError(c, "Unknown parameter");
            return;
        }
    }
    
    vectorIndex *vindex = createVectorIndex(c, index_name, dimension, 
                                          edge_size_for_creation, edge_size_for_search,
                                          distance_type, object_type, graph_type);
    if (!vindex) {
        return;
    }
    
    dictAdd(vector_indices, sdsnew(index_name), vindex);
    addReply(c, shared.ok);
}

/* VECTOR.INSERT command */
void vectorInsertCommand(client *c) {
    if (c->argc != 4) {
        addReplyError(c, "VECTOR.INSERT requires index name, vector ID, and vector data");
        return;
    }
    
    /* Ensure vector indices are initialized */
    if (vector_indices == NULL) {
        initVectorIndices();
    }
    
    char *index_name = c->argv[1]->ptr;
    char *vector_data = c->argv[3]->ptr;
    
    /* Find the index */
    dictEntry *de = dictFind(vector_indices, index_name);
    if (!de) {
        addReplyError(c, "Vector index not found");
        return;
    }
    
    vectorIndex *vindex = dictGetVal(de);
    
    /* Parse vector data (comma-separated floats) */
    char *token = strtok(vector_data, ",");
    float *vector = zmalloc(vindex->dimension * sizeof(float));
    size_t i = 0;
    
    while (token != NULL && i < vindex->dimension) {
        vector[i] = atof(token);
        token = strtok(NULL, ",");
        i++;
    }
    
    if (i != vindex->dimension) {
        addReplyError(c, "Vector dimension mismatch");
        zfree(vector);
        return;
    }
    
    /* Insert vector into NGT index */
    NGTError error = ngt_create_error_object();
    ObjectID id = ngt_insert_index_as_float(vindex->index, vector, vindex->dimension, error);
    
    if (id == 0) {
        addReplyError(c, "Failed to insert vector");
        zfree(vector);
        ngt_destroy_error_object(error);
        return;
    }
    
    zfree(vector);
    ngt_destroy_error_object(error);
    addReply(c, shared.ok);
}

/* VECTOR.SEARCH command */
void vectorSearchCommand(client *c) {
    if (c->argc != 4) {
        addReplyError(c, "VECTOR.SEARCH requires index name, query vector, and k");
        return;
    }
    
    /* Ensure vector indices are initialized */
    if (vector_indices == NULL) {
        initVectorIndices();
    }
    
    char *index_name = c->argv[1]->ptr;
    char *query_vector_str = c->argv[2]->ptr;
    long k;
    
    if (getLongFromObjectOrReply(c, c->argv[3], &k, NULL) != C_OK) {
        return;
    }
    
    if (k <= 0) {
        addReplyError(c, "k must be positive");
        return;
    }
    
    /* Find the index */
    dictEntry *de = dictFind(vector_indices, index_name);
    if (!de) {
        addReplyError(c, "Vector index not found");
        return;
    }
    
    vectorIndex *vindex = dictGetVal(de);
    
    /* Parse query vector */
    char *token = strtok(query_vector_str, ",");
    float *query_vector = zmalloc(vindex->dimension * sizeof(float));
    size_t i = 0;
    
    while (token != NULL && i < vindex->dimension) {
        query_vector[i] = atof(token);
        token = strtok(NULL, ",");
        i++;
    }
    
    if (i != vindex->dimension) {
        addReplyError(c, "Query vector dimension mismatch");
        zfree(query_vector);
        return;
    }
    
    /* Search in NGT index */
    NGTError error = ngt_create_error_object();
    NGTObjectDistances results = ngt_create_empty_results(error);
    
    if (!ngt_search_index_as_float(vindex->index, query_vector, vindex->dimension, k, 0.1, FLT_MAX, results, error)) {
        addReplyError(c, "Search failed");
        zfree(query_vector);
        ngt_destroy_results(results);
        ngt_destroy_error_object(error);
        return;
    }
    
    /* Get results */
    uint32_t result_size = ngt_get_result_size(results, error);
    
    addReplyArrayLen(c, result_size);
    for (uint32_t j = 0; j < result_size; j++) {
        NGTObjectDistance result = ngt_get_result(results, j, error);
        
        addReplyArrayLen(c, 2);
        addReplyLongLong(c, result.id);
        addReplyDouble(c, result.distance);
    }
    
    zfree(query_vector);
    ngt_destroy_results(results);
    ngt_destroy_error_object(error);
}

/* VECTOR.BUILD command */
void vectorBuildCommand(client *c) {
    if (c->argc != 2) {
        addReplyError(c, "VECTOR.BUILD requires index name");
        return;
    }
    
    char *index_name = c->argv[1]->ptr;
    
    /* Find the index */
    dictEntry *de = dictFind(vector_indices, index_name);
    if (!de) {
        addReplyError(c, "Vector index not found");
        return;
    }
    
    vectorIndex *vindex = dictGetVal(de);
    
    /* Build the index */
    NGTError error = ngt_create_error_object();
    uint32_t size = ngt_get_number_of_objects(vindex->index, error);
    
    if (!ngt_create_index(vindex->index, size, error)) {
        addReplyError(c, "Failed to build index");
        ngt_destroy_error_object(error);
        return;
    }
    
    /* Save the index to disk so quantization can see the objects */
    if (!ngt_save_index(vindex->index, vindex->path, error)) {
        addReplyError(c, "Failed to save index after build");
        ngt_destroy_error_object(error);
        return;
    }
    
    ngt_destroy_error_object(error);
    addReply(c, shared.ok);
}

/* VECTOR.REFINE command */
void vectorRefineCommand(client *c) {
    if (c->argc != 2) {
        addReplyError(c, "VECTOR.REFINE requires index name");
        return;
    }
    
    char *index_name = c->argv[1]->ptr;
    
    /* Find the index */
    dictEntry *de = dictFind(vector_indices, index_name);
    if (!de) {
        addReplyError(c, "Vector index not found");
        return;
    }
    
    vectorIndex *vindex = dictGetVal(de);
    
    /* Refine the index */
    NGTError error = ngt_create_error_object();
    
    if (!ngt_refine_anng(vindex->index, 0.1, 0.95, 100, vindex->edge_size_for_search, 1000, error)) {
        addReplyError(c, "Failed to refine index");
        ngt_destroy_error_object(error);
        return;
    }
    
    ngt_destroy_error_object(error);
    addReply(c, shared.ok);
}

/* VECTOR.DROP command */
void vectorDropCommand(client *c) {
    if (c->argc != 2) {
        addReplyError(c, "VECTOR.DROP requires index name");
        return;
    }
    
    char *index_name = c->argv[1]->ptr;
    
    /* Find and remove the index */
    dictEntry *de = dictFind(vector_indices, index_name);
    if (!de) {
        addReplyError(c, "Vector index not found");
        return;
    }
    
    vectorIndex *vindex = dictGetVal(de);
    freeVectorIndex(vindex);
    dictDelete(vector_indices, index_name);
    
    addReply(c, shared.ok);
}

/* VECTOR.INFO command */
void vectorInfoCommand(client *c) {
    if (c->argc != 2) {
        addReplyError(c, "VECTOR.INFO requires index name");
        return;
    }
    
    char *index_name = c->argv[1]->ptr;
    
    /* Find the index */
    dictEntry *de = dictFind(vector_indices, index_name);
    if (!de) {
        addReplyError(c, "Vector index not found");
        return;
    }
    
    vectorIndex *vindex = dictGetVal(de);
    
    /* Get index information */
    NGTError error = ngt_create_error_object();
    
    addReplyArrayLen(c, 8);
    addReplyBulkCString(c, "dimension");
    addReplyLongLong(c, vindex->dimension);
    addReplyBulkCString(c, "edge_size_for_creation");
    addReplyLongLong(c, vindex->edge_size_for_creation);
    addReplyBulkCString(c, "edge_size_for_search");
    addReplyLongLong(c, vindex->edge_size_for_search);
    addReplyBulkCString(c, "distance_type");
    addReplyBulkCString(c, vindex->distance_type);
    addReplyBulkCString(c, "object_type");
    addReplyBulkCString(c, vindex->object_type);
    addReplyBulkCString(c, "graph_type");
    addReplyBulkCString(c, vindex->graph_type);
    addReplyBulkCString(c, "number_of_objects");
    addReplyLongLong(c, ngt_get_number_of_objects(vindex->index, error));
    addReplyBulkCString(c, "number_of_indexed_objects");
    addReplyLongLong(c, ngt_get_number_of_indexed_objects(vindex->index, error));
    
    ngt_destroy_error_object(error);
}

/* VECTOR.LIST command */
void vectorListCommand(client *c) {
    if (c->argc != 1) {
        addReplyError(c, "VECTOR.LIST takes no arguments");
        return;
    }
    
    if (!vector_indices) {
        addReplyArrayLen(c, 0);
        return;
    }
    
    dictIterator *di = dictGetIterator(vector_indices);
    dictEntry *de;
    int count = 0;
    
    /* Count indices */
    while ((de = dictNext(di)) != NULL) {
        count++;
    }
    dictReleaseIterator(di);
    
    addReplyArrayLen(c, count);
    
    /* Add index names */
    di = dictGetIterator(vector_indices);
    while ((de = dictNext(di)) != NULL) {
        addReplyBulkCString(c, dictGetKey(de));
    }
    dictReleaseIterator(di);
} 

/* Global quantized vector indices storage */
static dict *quantized_vector_indices = NULL;

/* Initialize quantized vector indices storage */
void initQuantizedVectorIndices(void) {
    if (quantized_vector_indices == NULL) {
        quantized_vector_indices = dictCreate(&sdsHashDictType);
    }
}

/* Create a new quantized vector index */
quantizedVectorIndex *createQuantizedVectorIndex(client *c, const char *name, size_t dimension,
                                                int edge_size_for_creation, int edge_size_for_search,
                                                const char *distance_type, const char *object_type,
                                                const char *graph_type, float dimension_of_subvector,
                                                size_t max_number_of_edges) {
    (void)c; // Suppress unused parameter warning
    quantizedVectorIndex *qvindex = zmalloc(sizeof(quantizedVectorIndex));
    
    qvindex->dimension = dimension;
    qvindex->edge_size_for_creation = edge_size_for_creation;
    qvindex->edge_size_for_search = edge_size_for_search;
    qvindex->distance_type = sdsnew(distance_type);
    qvindex->object_type = sdsnew(object_type);
    qvindex->graph_type = sdsnew(graph_type);
    qvindex->zero_based_numbering = 1;
    qvindex->dimension_of_subvector = dimension_of_subvector;
    qvindex->max_number_of_edges = max_number_of_edges;
    
    /* Create path for the index */
    qvindex->path = sdsnew(name);
    
    /* For QBG indices, we don't need to open the index here */
    /* The index will be opened when needed for operations */
    qvindex->index = NULL;
    
    return qvindex;
}

/* Free quantized vector index */
void freeQuantizedVectorIndex(quantizedVectorIndex *qvindex) {
    if (qvindex) {
        /* QBG indices are closed when operations are done */
        sdsfree(qvindex->distance_type);
        sdsfree(qvindex->object_type);
        sdsfree(qvindex->graph_type);
        sdsfree(qvindex->path);
        zfree(qvindex);
    }
}

/* VECTOR.QUANTIZE command - Quantize an existing vector index */
void vectorQuantizeCommand(client *c) {
    if (c->argc < 2) {
        addReplyError(c, "VECTOR.QUANTIZE requires index name and optional parameters");
        return;
    }
    
    char *index_name = c->argv[1]->ptr;
    float dimension_of_subvector = 0.0;
    size_t max_number_of_edges = 128;
    
    /* Parse optional parameters */
    if (c->argc > 2) {
        dimension_of_subvector = atof(c->argv[2]->ptr);
    }
    if (c->argc > 3) {
        max_number_of_edges = atoi(c->argv[3]->ptr);
    }
    
    /* Find the original index */
    dictEntry *de = dictFind(vector_indices, index_name);
    if (!de) {
        addReplyError(c, "Vector index not found");
        return;
    }
    
    vectorIndex *vindex = dictGetVal(de);
    
    /* Use the full path to the index files */
    char full_path[1024];
    snprintf(full_path, sizeof(full_path), "%s/%s", getcwd(NULL, 0), vindex->path);
    
    /* Create NGTQG quantization parameters */
    NGTQGQuantizationParameters qg_params;
    ngtqg_initialize_quantization_parameters(&qg_params);
    qg_params.dimension_of_subvector = dimension_of_subvector;
    qg_params.max_number_of_edges = max_number_of_edges;
    
    /* Create the quantized index using NGTQG API */
    NGTQGError error = ngt_create_error_object();
    
    /* Quantize the index */
    if (!ngtqg_quantize(full_path, qg_params, error)) {
        char error_msg[1024];
        snprintf(error_msg, sizeof(error_msg), "Failed to quantize index: %s", ngt_get_error_string(error));
        addReplyError(c, error_msg);
        ngt_destroy_error_object(error);
        return;
    }
    
    /* Initialize quantized indices storage if needed */
    initQuantizedVectorIndices();
    
    /* Create and register the quantized index */
    quantizedVectorIndex *qvindex = createQuantizedVectorIndex(c, index_name, vindex->dimension,
                                                              vindex->edge_size_for_creation, vindex->edge_size_for_search,
                                                              vindex->distance_type, vindex->object_type, vindex->graph_type,
                                                              dimension_of_subvector, max_number_of_edges);
    if (!qvindex) {
        ngt_destroy_error_object(error);
        return;
    }
    
    /* Store the quantized index */
    dictAdd(quantized_vector_indices, sdsnew(index_name), qvindex);
    
    ngt_destroy_error_object(error);
    addReply(c, shared.ok);
}

/* VECTOR.QUANTIZED.CREATE command - NOT SUPPORTED BY NGTQG API */
void vectorQuantizedCreateCommand(client *c) {
    addReplyError(c, "VECTOR.QUANTIZED.CREATE is not supported. Quantized indices are created by quantizing existing regular indices using VECTOR.QUANTIZE command.");
}

/* VECTOR.QUANTIZED.INSERT command - NOT SUPPORTED BY NGTQG API */
void vectorQuantizedInsertCommand(client *c) {
    addReplyError(c, "VECTOR.QUANTIZED.INSERT is not supported. Quantized indices are read-only search indices created from regular indices.");
}

/*
 * VECTOR.QUANTIZED.SEARCH <indexname> <k> <queryvector>
 *   [epsilon] [result_expansion] [edge_size] [probe] [blob_epsilon] [exploration_size]
 *
 * All advanced parameters are optional and have robust defaults.
 */
void vectorQuantizedSearchCommand(client *c) {
    if (c->argc < 4) {
        addReplyError(c, "VECTOR.QUANTIZED.SEARCH requires index name, k, and query vector");
        return;
    }
    char *index_name = c->argv[1]->ptr;
    int k = atoi(c->argv[2]->ptr);
    char *vector_data = c->argv[3]->ptr;
    // Robust NGTQG-like defaults
    float epsilon = 0.02f;
    float result_expansion = 3.0f;
    float radius = 0.0f;  // 0.0 means no radius limit
    int argi = 4;
    if (c->argc > argi) epsilon = atof(c->argv[argi++]->ptr);
    if (c->argc > argi) result_expansion = atof(c->argv[argi++]->ptr);
    if (c->argc > argi) radius = atof(c->argv[argi++]->ptr);
    // Find the quantized index
    if (!quantized_vector_indices) {
        addReplyError(c, "No quantized vector indices available");
        return;
    }
    dictEntry *de = dictFind(quantized_vector_indices, index_name);
    if (!de) {
        addReplyError(c, "Quantized vector index not found");
        return;
    }
    quantizedVectorIndex *qvindex = dictGetVal(de);
    // Parse vector data
    float *query_vector = zmalloc(sizeof(float) * qvindex->dimension);
    char *token = strtok(vector_data, ",");
    int i = 0;
    while (token != NULL && (size_t)i < qvindex->dimension) {
        query_vector[i] = atof(token);
        token = strtok(NULL, ",");
        i++;
    }
    if ((size_t)i != qvindex->dimension) {
        addReplyError(c, "Vector dimension mismatch");
        zfree(query_vector);
        return;
    }
    // Use the full path to the quantized index files
    char full_path[1024];
    snprintf(full_path, sizeof(full_path), "%s/%s", getcwd(NULL, 0), qvindex->path);
    // Open the quantized index
    NGTQGError error = ngt_create_error_object();
    NGTQGIndex qg_index = ngtqg_open_index(full_path, error);
    if (!qg_index) {
        char error_msg[2048];
        snprintf(error_msg, sizeof(error_msg), "Failed to open quantized index: %s", ngt_get_error_string(error));
        addReplyError(c, error_msg);
        ngt_destroy_error_object(error);
        zfree(query_vector);
        return;
    }
    // Create query
    NGTQGQuery query;
    ngtqg_initialize_query(&query);
    query.query = query_vector;
    query.size = k;
    query.epsilon = epsilon;
    query.result_expansion = result_expansion;
    query.radius = radius;
    // Create results array
    NGTObjectDistances results = ngt_create_empty_results(error);
    // Search the quantized index
    if (!ngtqg_search_index(qg_index, query, results, error)) {
        char error_msg[2048];
        snprintf(error_msg, sizeof(error_msg), "Failed to search quantized index: %s", ngt_get_error_string(error));
        addReplyError(c, error_msg);
        ngt_destroy_results(results);
        ngtqg_close_index(qg_index);
        ngt_destroy_error_object(error);
        zfree(query_vector);
        return;
    }
    // Get results
    uint32_t result_size = ngt_get_result_size(results, error);
    addReplyArrayLen(c, result_size);
    for (uint32_t i = 0; i < result_size; i++) {
        NGTObjectDistance distance = ngt_get_result(results, i, error);
        addReplyArrayLen(c, 2);
        addReplyLongLong(c, distance.id);
        addReplyDouble(c, distance.distance);
    }
    // Cleanup
    ngt_destroy_results(results);
    ngtqg_close_index(qg_index);
    ngt_destroy_error_object(error);
    zfree(query_vector);
}

/* VECTOR.QUANTIZED.BUILD command - NOT SUPPORTED BY NGTQG API */
void vectorQuantizedBuildCommand(client *c) {
    addReplyError(c, "VECTOR.QUANTIZED.BUILD is not supported. Quantized indices are automatically built during the quantization process.");
}

/* VECTOR.QUANTIZED.DROP command */
void vectorQuantizedDropCommand(client *c) {
    if (c->argc != 2) {
        addReplyError(c, "VECTOR.QUANTIZED.DROP requires index name");
        return;
    }
    
    char *index_name = c->argv[1]->ptr;
    
    /* Find and remove the quantized index */
    if (!quantized_vector_indices) {
        addReplyError(c, "No quantized vector indices available");
        return;
    }
    
    dictEntry *de = dictFind(quantized_vector_indices, index_name);
    if (!de) {
        addReplyError(c, "Quantized vector index not found");
        return;
    }
    
    quantizedVectorIndex *qvindex = dictGetVal(de);
    freeQuantizedVectorIndex(qvindex);
    dictDelete(quantized_vector_indices, index_name);
    
    addReply(c, shared.ok);
}

/* VECTOR.QUANTIZED.INFO command */
void vectorQuantizedInfoCommand(client *c) {
    if (c->argc != 2) {
        addReplyError(c, "VECTOR.QUANTIZED.INFO requires index name");
        return;
    }
    
    char *index_name = c->argv[1]->ptr;
    
    /* Find the quantized index */
    if (!quantized_vector_indices) {
        addReplyError(c, "No quantized vector indices available");
        return;
    }
    
    dictEntry *de = dictFind(quantized_vector_indices, index_name);
    if (!de) {
        addReplyError(c, "Quantized vector index not found");
        return;
    }
    
    quantizedVectorIndex *qvindex = dictGetVal(de);
    
    /* Get quantized index information */
    NGTQGError error = ngt_create_error_object();
    
    addReplyArrayLen(c, 10);
    addReplyBulkCString(c, "dimension");
    addReplyLongLong(c, qvindex->dimension);
    addReplyBulkCString(c, "edge_size_for_creation");
    addReplyLongLong(c, qvindex->edge_size_for_creation);
    addReplyBulkCString(c, "edge_size_for_search");
    addReplyLongLong(c, qvindex->edge_size_for_search);
    addReplyBulkCString(c, "distance_type");
    addReplyBulkCString(c, qvindex->distance_type);
    addReplyBulkCString(c, "object_type");
    addReplyBulkCString(c, qvindex->object_type);
    addReplyBulkCString(c, "graph_type");
    addReplyBulkCString(c, qvindex->graph_type);
    addReplyBulkCString(c, "dimension_of_subvector");
    addReplyDouble(c, qvindex->dimension_of_subvector);
    addReplyBulkCString(c, "max_number_of_edges");
    addReplyLongLong(c, qvindex->max_number_of_edges);
    addReplyBulkCString(c, "quantized");
    addReplyBulkCString(c, "true");
    
    ngt_destroy_error_object(error);
}

/* VECTOR.QUANTIZED.LIST command */
void vectorQuantizedListCommand(client *c) {
    if (c->argc != 1) {
        addReplyError(c, "VECTOR.QUANTIZED.LIST takes no arguments");
        return;
    }
    
    if (!quantized_vector_indices) {
        addReplyArrayLen(c, 0);
        return;
    }
    
    dictIterator *di = dictGetIterator(quantized_vector_indices);
    dictEntry *de;
    int count = 0;
    
    /* Count quantized indices */
    while ((de = dictNext(di)) != NULL) {
        count++;
    }
    dictReleaseIterator(di);
    
    addReplyArrayLen(c, count);
    
    /* Add quantized index names */
    di = dictGetIterator(quantized_vector_indices);
    while ((de = dictNext(di)) != NULL) {
        addReplyBulkCString(c, dictGetKey(de));
    }
    dictReleaseIterator(di);
} 

/* VECTOR.BATCH.INSERT command */
void vectorBatchInsertCommand(client *c) {
    if (c->argc < 3) {
        addReplyError(c, "VECTOR.BATCH.INSERT requires index name and at least one vector");
        return;
    }
    char *index_name = c->argv[1]->ptr;
    int num_vectors = c->argc - 2;
    
    dictEntry *de = dictFind(vector_indices, index_name);
    if (!de) {
        addReplyError(c, "Vector index not found");
        return;
    }
    vectorIndex *vindex = dictGetVal(de);
    int dim = vindex->dimension;
    int success_count = 0;
    
    for (int i = 0; i < num_vectors; ++i) {
        char *vector_data = c->argv[2 + i]->ptr;
        float *vector = zmalloc(dim * sizeof(float));
        char *token = strtok(vector_data, ",");
        int j = 0;
        while (token != NULL && j < dim) {
            vector[j] = atof(token);
            token = strtok(NULL, ",");
            j++;
        }
        if (j != dim) {
            zfree(vector);
            continue;
        }
        NGTError error = ngt_create_error_object();
        ObjectID id = ngt_insert_index_as_float(vindex->index, vector, dim, error);
        if (id != 0) success_count++;
        ngt_destroy_error_object(error);
        zfree(vector);
    }
    addReplyLongLong(c, success_count);
}

/* VECTOR.BATCH.SEARCH command */
void vectorBatchSearchCommand(client *c) {
    if (c->argc < 4) {
        addReplyError(c, "VECTOR.BATCH.SEARCH requires index name, k, and at least one query vector");
        return;
    }
    char *index_name = c->argv[1]->ptr;
    int k = atoi(c->argv[2]->ptr);
    int num_queries = c->argc - 3;
    
    dictEntry *de = dictFind(vector_indices, index_name);
    if (!de) {
        addReplyError(c, "Vector index not found");
        return;
    }
    vectorIndex *vindex = dictGetVal(de);
    int dim = vindex->dimension;
    
    addReplyArrayLen(c, num_queries);
    
    #pragma omp parallel for
    for (int i = 0; i < num_queries; ++i) {
        float *query_vector = zmalloc(dim * sizeof(float));
        char *vector_data = c->argv[3 + i]->ptr;
        char *token = strtok(vector_data, ",");
        int j = 0;
        while (token != NULL && j < dim) {
            query_vector[j] = atof(token);
            token = strtok(NULL, ",");
            j++;
        }
        if (j != dim) {
            #pragma omp critical
            addReplyNull(c);
            zfree(query_vector);
            continue;
        }
        NGTError error = ngt_create_error_object();
        NGTObjectDistances results = ngt_create_empty_results(error);
        if (!ngt_search_index_as_float(vindex->index, query_vector, dim, k, 0.1, FLT_MAX, results, error)) {
            #pragma omp critical
            addReplyNull(c);
            ngt_destroy_results(results);
            ngt_destroy_error_object(error);
            zfree(query_vector);
            continue;
        }
        uint32_t result_size = ngt_get_result_size(results, error);
        #pragma omp critical
        {
            addReplyArrayLen(c, result_size);
            for (uint32_t j = 0; j < result_size; j++) {
                NGTObjectDistance result = ngt_get_result(results, j, error);
                addReplyArrayLen(c, 2);
                addReplyLongLong(c, result.id);
                addReplyDouble(c, result.distance);
            }
        }
        ngt_destroy_results(results);
        ngt_destroy_error_object(error);
        zfree(query_vector);
    }
} 