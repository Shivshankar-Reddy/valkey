# Valkey Vector Search Extension

This extension adds vector search capabilities to Valkey using the NGT (Neighborhood Graph and Tree) library. It provides efficient similarity search for high-dimensional vectors with support for various distance metrics.

## Features

- **Vector Index Creation**: Create vector indices with configurable dimensions and parameters
- **Vector Insertion**: Insert vectors into indices for similarity search
- **Vector Search**: Perform k-nearest neighbor search with various distance metrics
- **Index Management**: Build, refine, and manage vector indices
- **Multiple Distance Metrics**: Support for L1, L2, Normalized L2, Hamming, Jaccard, Cosine, and Inner Product distances
- **Multiple Object Types**: Support for Float and Byte vector types

## Build Instructions

### Prerequisites

1. **OpenBLAS**: Required for NGT matrix operations
   ```bash
   sudo apt-get update
   sudo apt-get install libopenblas-dev
   ```

2. **CMake**: Required for building NGT
   ```bash
   sudo apt-get install cmake
   ```

### Building

1. **Clone and build the project**:
   ```bash
   git clone <repository-url>
   cd valkey
   make clean && make
   ```

2. **Start the server**:
   ```bash
   ./src/valkey-server --port 6379
   ```

3. **Test the installation**:
   ```bash
   ./src/valkey-cli ping
   # Should return: PONG
   ```

## Vector Commands

### 1. VECTOR.CREATE - Create a Vector Index

Creates a new vector index with specified parameters.

**Syntax**:
```
VECTOR.CREATE index_name dimension [EDGE_SIZE_FOR_CREATION value] [EDGE_SIZE_FOR_SEARCH value] [DISTANCE_TYPE type] [OBJECT_TYPE type] [GRAPH_TYPE type]
```

**Parameters**:
- `index_name`: Name of the vector index
- `dimension`: Dimension of the vectors (positive integer)
- `EDGE_SIZE_FOR_CREATION`: Number of edges for graph creation (default: 10)
- `EDGE_SIZE_FOR_SEARCH`: Number of edges for search (default: 40)
- `DISTANCE_TYPE`: Distance metric (L1, L2, Normalized L2, Hamming, Jaccard, Cosine, Inner Product) (default: L2)
- `OBJECT_TYPE`: Vector data type (Float, Byte) (default: Float)
- `GRAPH_TYPE`: Graph type (ANNG) (default: ANNG)

**Example**:
```bash
# Create a 2D vector index with default parameters
./src/valkey-cli vector_create my_index 2

# Create a 128D vector index with custom parameters
./src/valkey-cli vector_create my_index 128 EDGE_SIZE_FOR_CREATION 20 EDGE_SIZE_FOR_SEARCH 50 DISTANCE_TYPE Cosine OBJECT_TYPE Float
```

### 2. VECTOR.INSERT - Insert Vectors

Inserts a vector into the specified index.

**Syntax**:
```
VECTOR.INSERT index_name vector_id vector_data
```

**Parameters**:
- `index_name`: Name of the vector index
- `vector_id`: Unique identifier for the vector
- `vector_data`: Comma-separated vector values

**Example**:
```bash
# Insert a 2D vector
./src/valkey-cli vector_insert my_index 1 "1.0,2.0"

# Insert a 3D vector
./src/valkey-cli vector_insert my_index 2 "3.0,4.0,5.0"
```

### 3. VECTOR.BUILD - Build the Index

Builds the vector index for efficient searching.

**Syntax**:
```
VECTOR.BUILD index_name
```

**Example**:
```bash
./src/valkey-cli vector_build my_index
```

### 4. VECTOR.SEARCH - Search for Similar Vectors

Performs k-nearest neighbor search.

**Syntax**:
```
VECTOR.SEARCH index_name query_vector k
```

**Parameters**:
- `index_name`: Name of the vector index
- `query_vector`: Comma-separated query vector values
- `k`: Number of nearest neighbors to return

**Example**:
```bash
# Search for 5 nearest neighbors
./src/valkey-cli vector_search my_index "1.0,2.0" 5
```

**Response Format**:
```
1) 1) (integer) vector_id
   2) "distance"
2) 1) (integer) vector_id
   2) "distance"
...
```

### 5. VECTOR.INFO - Get Index Information

Returns information about a vector index.

**Syntax**:
```
VECTOR.INFO index_name
```

**Example**:
```bash
./src/valkey-cli vector_info my_index
```

**Response Format**:
```
1) "dimension"
2) (integer) dimension_value
3) "edge_size_for_creation"
4) (integer) creation_edge_size
5) "edge_size_for_search"
6) (integer) search_edge_size
7) "distance_type"
8) "distance_type_name"
```

### 6. VECTOR.LIST - List All Indices

Lists all vector indices.

**Syntax**:
```
VECTOR.LIST
```

**Example**:
```bash
./src/valkey-cli vector_list
```

**Response Format**:
```
1) "index_name_1"
2) "index_name_2"
...
```

### 7. VECTOR.DROP - Drop an Index

Removes a vector index.

**Syntax**:
```
VECTOR.DROP index_name
```

**Example**:
```bash
./src/valkey-cli vector_drop my_index
```

### 8. VECTOR.REFINE - Refine the Index

Refines the vector index for better search performance.

**Syntax**:
```
VECTOR.REFINE index_name
```

**Example**:
```bash
./src/valkey-cli vector_refine my_index
```

## Complete Example

Here's a complete example demonstrating vector search functionality:

```bash
# 1. Start the server
./src/valkey-server --port 6379 --daemonize yes

# 2. Create a vector index
./src/valkey-cli vector_create test_index 2

# 3. Insert some vectors
./src/valkey-cli vector_insert test_index 1 "1.0,2.0"
./src/valkey-cli vector_insert test_index 2 "3.0,4.0"
./src/valkey-cli vector_insert test_index 3 "5.0,6.0"

# 4. Build the index
./src/valkey-cli vector_build test_index

# 5. Search for similar vectors
./src/valkey-cli vector_search test_index "1.0,2.0" 3

# 6. Get index information
./src/valkey-cli vector_info test_index

# 7. List all indices
./src/valkey-cli vector_list
```

## Distance Metrics

The extension supports the following distance metrics:

- **L1 (Manhattan)**: Sum of absolute differences
- **L2 (Euclidean)**: Square root of sum of squared differences
- **Normalized L2**: Normalized Euclidean distance
- **Hamming**: Number of positions at which corresponding symbols are different
- **Jaccard**: 1 minus the Jaccard similarity coefficient
- **Cosine**: 1 minus the cosine similarity
- **Inner Product**: Negative dot product

## Performance Considerations

1. **Index Building**: Always call `VECTOR.BUILD` after inserting vectors for efficient search
2. **Edge Sizes**: Adjust `EDGE_SIZE_FOR_CREATION` and `EDGE_SIZE_FOR_SEARCH` based on your data characteristics
3. **Distance Metrics**: Choose the appropriate distance metric for your use case
4. **Vector Dimensions**: Higher dimensions require more memory and computation time

## Error Handling

The extension provides detailed error messages for common issues:

- Invalid vector dimensions
- Missing indices
- Incorrect parameter values
- Memory allocation failures
- NGT library errors

## Dependencies

- **NGT Library**: Neighborhood Graph and Tree for efficient similarity search
- **OpenBLAS**: Optimized BLAS/LAPACK implementation for matrix operations
- **OpenMP**: Parallel processing support

## Troubleshooting

1. **Build Errors**: Ensure OpenBLAS is installed
2. **Runtime Errors**: Check that indices are built before searching
3. **Memory Issues**: Monitor memory usage with large indices
4. **Performance Issues**: Consider refining indices for better search quality

## License

This extension is part of the Valkey project and follows the same licensing terms. 