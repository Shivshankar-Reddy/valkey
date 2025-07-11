#include "server.h"
#include "sds.h"
#include <string.h>
#include <stdlib.h>
#include <math.h>

/* NGT C API includes */
#include "../deps/NGT/lib/NGT/Capi.h"

/* Vector index structure */
typedef struct vectorIndex {
    NGTIndex index;
    char *path;
    size_t dimension;
    int edge_size_for_creation;
    int edge_size_for_search;
    char *distance_type;
    char *object_type;
    char *graph_type;
    int zero_based_numbering;
} vectorIndex;

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
    
    if (!ngt_search_index_as_float(vindex->index, query_vector, vindex->dimension, k, 0.0, 0.0, results, error)) {
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