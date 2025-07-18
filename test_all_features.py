#!/usr/bin/env python3
import redis
import numpy as np
import time
import sys

def test_all_features():
    """Test all advanced features and parameters with various configurations"""
    
    # Connect to Valkey
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✓ Connected to Valkey server")
    except Exception as e:
        print(f"✗ Failed to connect to Valkey: {e}")
        return False
    
    # Test 1: Basic vector operations with different dimensions
    print("\n=== Test 1: Basic vector operations ===")
    dimensions = [64, 128, 256]
    for dim in dimensions:
        print(f"Testing dimension {dim}...")
        
        # Create index
        result = r.execute_command('vector_create', f'test_dim_{dim}', dim)
        print(f"  ✓ Created index: {result}")
        
        # Insert vectors
        vector_data = ','.join([str(i * 0.1) for i in range(dim)])
        result = r.execute_command('vector_insert', f'test_dim_{dim}', f'vec1_{dim}', vector_data)
        print(f"  ✓ Inserted vector: {result}")
        
        # Build index
        result = r.execute_command('vector_build', f'test_dim_{dim}')
        print(f"  ✓ Built index: {result}")
        
        # Search
        result = r.execute_command('vector_search', f'test_dim_{dim}', vector_data, 5)
        print(f"  ✓ Search result: {len(result) if result else 0} matches")
        
        # Info
        info = r.execute_command('vector_info', f'test_dim_{dim}')
        print(f"  ✓ Index info: dimension={info[1]}, distance={info[7]}")
    
    # Test 2: Batch operations
    print("\n=== Test 2: Batch operations ===")
    
    # Create index for batch testing
    r.execute_command('vector_create', 'test_batch', 64)
    
    # Batch insert multiple vectors
    batch_vectors = []
    for i in range(10):
        vector_data = ','.join([str(j * 0.1 + i * 0.01) for j in range(64)])
        batch_vectors.append(f'vec{i}:{vector_data}')
    
    batch_data = ' '.join(batch_vectors)
    result = r.execute_command('vector_batch_insert', 'test_batch', batch_data)
    print(f"✓ Batch inserted {result} vectors")
    
    # Build index
    r.execute_command('vector_build', 'test_batch')
    
    # Batch search
    query_vector = ','.join([str(i * 0.1) for i in range(64)])
    result = r.execute_command('vector_batch_search', 'test_batch', query_vector, 5)
    print(f"✓ Batch search found {len(result) if result else 0} results")
    
    # Test 3: Quantized operations
    print("\n=== Test 3: Quantized operations ===")
    
    # Create regular index
    r.execute_command('vector_create', 'test_quantize', 64)
    
    # Insert many vectors for quantization
    for i in range(100):
        vector_data = ','.join([str(j * 0.1 + i * 0.01) for j in range(64)])
        r.execute_command('vector_insert', 'test_quantize', f'vec{i}', vector_data)
    
    # Build index
    r.execute_command('vector_build', 'test_quantize')
    
    # Quantize the index
    result = r.execute_command('vector_quantize', 'test_quantize', 8)
    print(f"✓ Quantized index: {result}")
    
    # Test quantized search (if quantized index was created successfully)
    try:
        query_vector = ','.join([str(i * 0.1) for i in range(64)])
        result = r.execute_command('vector_quantized_search', 'test_quantize', query_vector, 5)
        print(f"✓ Quantized search found {len(result) if result else 0} results")
    except Exception as e:
        print(f"⚠ Quantized search not available: {e}")
    
    # Test 4: Advanced parameters
    print("\n=== Test 4: Advanced parameters ===")
    
    # Create index with custom parameters
    result = r.execute_command('vector_create', 'test_advanced', 128, 20, 50, 'L2', 'Float', 'ANNG')
    print(f"✓ Created advanced index: {result}")
    
    # Insert vectors
    for i in range(20):
        vector_data = ','.join([str(j * 0.1 + i * 0.01) for j in range(128)])
        r.execute_command('vector_insert', 'test_advanced', f'vec{i}', vector_data)
    
    # Build with refine
    r.execute_command('vector_build', 'test_advanced')
    result = r.execute_command('vector_refine', 'test_advanced')
    print(f"✓ Refined index: {result}")
    
    # Search with different parameters
    query_vector = ','.join([str(i * 0.1) for i in range(128)])
    result = r.execute_command('vector_search', 'test_advanced', query_vector, 10)
    print(f"✓ Advanced search found {len(result) if result else 0} results")
    
    # Test 5: List and info commands
    print("\n=== Test 5: List and info commands ===")
    
    # List all indices
    indices = r.execute_command('vector_list')
    print(f"✓ Regular indices: {indices}")
    
    # List quantized indices
    try:
        quantized_indices = r.execute_command('vector_quantized_list')
        print(f"✓ Quantized indices: {quantized_indices}")
    except Exception as e:
        print(f"⚠ Quantized list not available: {e}")
        quantized_indices = []
    
    # Get info for each index
    for idx in indices[:3]:  # Test first 3 indices
        info = r.execute_command('vector_info', idx)
        print(f"✓ Info for {idx}: dimension={info[1]}, distance={info[7]}")
    
    # Test 6: Cleanup
    print("\n=== Test 6: Cleanup ===")
    
    # Drop indices
    for idx in indices:
        result = r.execute_command('vector_drop', idx)
        print(f"✓ Dropped {idx}: {result}")
    
    for idx in quantized_indices:
        try:
            result = r.execute_command('vector_quantized_drop', idx)
            print(f"✓ Dropped quantized {idx}: {result}")
        except Exception as e:
            print(f"⚠ Could not drop quantized {idx}: {e}")
    
    print("\n=== All tests completed successfully! ===")
    return True

if __name__ == "__main__":
    success = test_all_features()
    sys.exit(0 if success else 1) 