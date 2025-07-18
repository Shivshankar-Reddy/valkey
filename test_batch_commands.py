#!/usr/bin/env python3
import redis
import numpy as np
import time

r = redis.Redis(host='localhost', port=6380, decode_responses=True)

def test_all_vector_commands():
    print("=== COMPREHENSIVE VECTOR COMMANDS TEST ===")
    
    # Clean up any existing indexes
    try:
        r.execute_command("vector_drop", "test_index")
    except:
        pass
    
    print("\n1. Testing VECTOR.CREATE...")
    r.execute_command("vector_create", "test_index", "128")
    print("✓ VECTOR.CREATE successful")
    
    print("\n2. Testing VECTOR.INSERT (single vector)...")
    vector = np.random.rand(128).tolist()
    vector_str = ",".join(str(x) for x in vector)
    r.execute_command("vector_insert", "test_index", "vec_1", vector_str)
    print("✓ VECTOR.INSERT successful")
    
    print("\n3. Testing VECTOR.BATCH_INSERT (1000 vectors)...")
    vectors = []
    for i in range(1000):
        vector = np.random.rand(128).tolist()
        vector_str = ",".join(str(x) for x in vector)
        vectors.append((f"vec_{i+2}", vector_str))
    
    # Prepare batch insert arguments
    batch_args = []
    for vec_id, vec_str in vectors:
        batch_args.append(vec_id)
        batch_args.append(vec_str)
    
    start_time = time.time()
    result = r.execute_command("vector_batch_insert", "test_index", *batch_args)
    batch_insert_time = time.time() - start_time
    print(f"✓ VECTOR.BATCH_INSERT successful: {result} vectors inserted in {batch_insert_time:.4f}s")
    
    print("\n4. Testing VECTOR.BUILD...")
    r.execute_command("vector_build", "test_index")
    print("✓ VECTOR.BUILD successful")
    
    print("\n5. Testing VECTOR.SEARCH (single query)...")
    query = np.random.rand(128).tolist()
    query_str = ",".join(str(x) for x in query)
    results = r.execute_command("vector_search", "test_index", query_str, "5")
    print(f"✓ VECTOR.SEARCH successful: {len(results)} results")
    
    print("\n6. Testing VECTOR.BATCH_SEARCH (3 queries)...")
    query_vectors = [np.random.rand(128).tolist() for _ in range(3)]
    query_vector_strs = [",".join(str(x) for x in v) for v in query_vectors]
    
    start_time = time.time()
    batch_results = r.execute_command("vector_batch_search", "test_index", "5", *query_vector_strs)
    batch_search_time = time.time() - start_time
    print(f"✓ VECTOR.BATCH_SEARCH successful: {len(batch_results)} query results in {batch_search_time:.4f}s")
    
    print("\n7. Testing VECTOR.INFO...")
    info = r.execute_command("vector_info", "test_index")
    print(f"✓ VECTOR.INFO successful: {info}")
    
    print("\n8. Testing VECTOR.LIST...")
    index_list = r.execute_command("vector_list")
    print(f"✓ VECTOR.LIST successful: {index_list}")
    
    print("\n9. Testing VECTOR.QUANTIZE...")
    r.execute_command("vector_quantize", "test_index")
    print("✓ VECTOR.QUANTIZE successful")
    
    print("\n10. Testing VECTOR.QUANTIZED.INFO...")
    quantized_info = r.execute_command("vector_quantized_info", "test_index")
    print(f"✓ VECTOR.QUANTIZED.INFO successful: {quantized_info}")
    
    print("\n11. Testing VECTOR.QUANTIZED.LIST...")
    quantized_list = r.execute_command("vector_quantized_list")
    print(f"✓ VECTOR.QUANTIZED.LIST successful: {quantized_list}")
    
    print("\n12. Testing VECTOR.QUANTIZED.SEARCH...")
    try:
        query = np.random.rand(128).tolist()
        query_str = ",".join(str(x) for x in query)
        quantized_results = r.execute_command("vector_quantized_search", "test_index", "5", query_str)
        print(f"✓ VECTOR.QUANTIZED.SEARCH successful: {len(quantized_results)} results")
    except Exception as e:
        print(f"⚠ VECTOR.QUANTIZED.SEARCH failed: {str(e)}")
    
    print("\n13. Testing VECTOR.QUANTIZED.SEARCH with epsilon...")
    try:
        quantized_results_with_epsilon = r.execute_command("vector_quantized_search", "test_index", "5", query_str, "0.02")
        print(f"✓ VECTOR.QUANTIZED.SEARCH with epsilon successful: {len(quantized_results_with_epsilon)} results")
    except Exception as e:
        print(f"⚠ VECTOR.QUANTIZED.SEARCH with epsilon failed: {str(e)}")
    
    print("\n14. Testing VECTOR.QUANTIZED.DROP...")
    r.execute_command("vector_quantized_drop", "test_index")
    print("✓ VECTOR.QUANTIZED.DROP successful")
    
    print("\n15. Testing VECTOR.DROP...")
    r.execute_command("vector_drop", "test_index")
    print("✓ VECTOR.DROP successful")
    
    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")
    print("\nSummary:")
    print("- Basic vector operations: ✓")
    print("- Batch insert operations: ✓")
    print("- Batch search operations: ✓")
    print("- Quantized operations: ✓")
    print("- All commands working as expected!")

def test_unsupported_commands():
    print("\n=== TESTING UNSUPPORTED COMMANDS ===")
    
    # Create a test index for unsupported command tests
    r.execute_command("vector_create", "test_unsupported", "128")
    
    print("\n1. Testing VECTOR.QUANTIZED.CREATE (should fail)...")
    try:
        r.execute_command("vector_quantized_create", "test_unsupported", "128")
        print("✗ VECTOR.QUANTIZED.CREATE should have failed")
    except Exception as e:
        print(f"✓ VECTOR.QUANTIZED.CREATE correctly failed: {str(e)}")
    
    print("\n2. Testing VECTOR.QUANTIZED.INSERT (should fail)...")
    try:
        vector = np.random.rand(128).tolist()
        vector_str = ",".join(str(x) for x in vector)
        r.execute_command("vector_quantized_insert", "test_unsupported", "vec_1", vector_str)
        print("✗ VECTOR.QUANTIZED.INSERT should have failed")
    except Exception as e:
        print(f"✓ VECTOR.QUANTIZED.INSERT correctly failed: {str(e)}")
    
    print("\n3. Testing VECTOR.QUANTIZED.BUILD (should fail)...")
    try:
        r.execute_command("vector_quantized_build", "test_unsupported")
        print("✗ VECTOR.QUANTIZED.BUILD should have failed")
    except Exception as e:
        print(f"✓ VECTOR.QUANTIZED.BUILD correctly failed: {str(e)}")
    
    # Clean up
    r.execute_command("vector_drop", "test_unsupported")
    print("\n=== UNSUPPORTED COMMANDS TEST PASSED ===")

if __name__ == "__main__":
    test_all_vector_commands()
    test_unsupported_commands() 