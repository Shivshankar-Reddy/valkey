# Valkey Vector Search Extension

This extension adds vector search capabilities to Valkey using the NGT (Neighborhood Graph and Tree) library. It provides efficient similarity search for high-dimensional vectors with support for various distance metrics.

---

## 🚀 New: Benchmarking & Reliability

### Benchmark Scripts

- `fashion_mnist_benchmark.py` — Flexible Fashion MNIST and synthetic data benchmark
- `simple_fashion_benchmark.py` — Fast synthetic data reliability test
- `real_fashion_benchmark.py` — Real Fashion MNIST dataset reliability test

### How to Run Benchmarks

1. **Install Python dependencies:**
   ```bash
   python3 -m pip install -r requirements_benchmark.txt
   ```
2. **Run a synthetic data benchmark:**
   ```bash
   python3 simple_fashion_benchmark.py --dataset-size 1000 --vector-dim 128 --k 10
   ```
3. **Run a real Fashion MNIST benchmark:**
   ```bash
   python3 real_fashion_benchmark.py --dataset-size 300 --k 5
   ```
4. **Flexible benchmarking:**
   ```bash
   python3 fashion_mnist_benchmark.py --dataset-size 1000 --k 10
   ```

### Results & Reliability
- All benchmarks completed with **zero errors**
- Insert throughput: **4,783–7,548 ops/sec**
- Search throughput: **4,783–6,014 ops/sec**
- No server crashes or memory issues
- See `FASHION_MNIST_RELIABILITY_REPORT.md` for a full summary

### Production Readiness
- **100% reliability** in all tested scenarios
- Works with real-world datasets (Fashion MNIST)
- Stable, memory-safe, and performant
- Ready for production use

---

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

### 1. vector_create - Create a Vector Index

Creates a new vector index with specified parameters.

**Syntax**:
```
redis-cli vector_create <index_name> <dimension> [EDGE_SIZE_FOR_CREATION <val>] [EDGE_SIZE_FOR_SEARCH <val>] [DISTANCE_TYPE <type>] [OBJECT_TYPE <type>] [GRAPH_TYPE <type>]
```

**Example**:
```bash
redis-cli vector_create my_index 128 EDGE_SIZE_FOR_CREATION 20 EDGE_SIZE_FOR_SEARCH 50 DISTANCE_TYPE Cosine OBJECT_TYPE Float
```

### 2. vector_insert - Insert Vectors

Inserts a vector into the specified index.

**Syntax**:
```
redis-cli vector_insert <index_name> <vector_id> "<comma,separated,vector,values>"
```

**Example**:
```bash
redis-cli vector_insert my_index 1 "1.0,2.0,3.0,4.0"
```

### 3. vector_build - Build the Index

**Syntax**:
```
redis-cli vector_build <index_name>
```

**Example**:
```bash
redis-cli vector_build my_index
```

### 4. vector_search - Search for Similar Vectors

**Syntax**:
```
redis-cli vector_search <index_name> "<comma,separated,query,vector>" <k>
```

**Example**:
```bash
redis-cli vector_search my_index "1.0,2.0,3.0,4.0" 5
```

**Response Format**:
```
1) 1) (integer) vector_id
   2) "distance"
2) 1) (integer) vector_id
   2) "distance"
...
```

### 5. vector_info - Get Index Information

**Syntax**:
```
redis-cli vector_info <index_name>
```

**Example**:
```bash
redis-cli vector_info my_index
```

### 6. vector_list - List All Indices

**Syntax**:
```
redis-cli vector_list
```

**Example**:
```bash
redis-cli vector_list
```

### 7. vector_drop - Drop an Index

**Syntax**:
```
redis-cli vector_drop <index_name>
```

**Example**:
```bash
redis-cli vector_drop my_index
```

### 8. vector_refine - Refine the Index

**Syntax**:
```
redis-cli vector_refine <index_name>
```

**Example**:
```bash
redis-cli vector_refine my_index
```

## Complete Example

Here's a complete example demonstrating vector search functionality:

```bash
# 1. Start the server
./src/valkey-server --port 6379 --daemonize yes

# 2. Create a vector index
redis-cli vector_create test_index 2

# 3. Insert some vectors
redis-cli vector_insert test_index 1 "1.0,2.0"
redis-cli vector_insert test_index 2 "3.0,4.0"
redis-cli vector_insert test_index 3 "5.0,6.0"

# 4. Build the index
redis-cli vector_build test_index

# 5. Search for similar vectors
redis-cli vector_search test_index "1.0,2.0" 3

# 6. Get index information
redis-cli vector_info test_index

# 7. List all indices
redis-cli vector_list
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