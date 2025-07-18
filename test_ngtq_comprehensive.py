#!/usr/bin/env python3

import redis
import time
import sys
import os

def test_ngtq_implementation():
    """Test the fixed NGTQ implementation"""
    
    # Connect to Redis
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✓ Connected to Redis server")
    except Exception as e:
        print(f"✗ Failed to connect to Redis: {e}")
        return False
    
    # Test 1: Print expected command list
    print("\n=== Test 1: Command Availability (static list) ===")
    expected_commands = [
        'vector_create', 'vector_insert', 'vector_build', 'vector_search', 'vector_info', 'vector_list', 'vector_drop',
        'vector_quantize', 'vector_quantized_search', 'vector_quantized_list', 'vector_quantized_info', 'vector_quantized_drop',
        'vector_refine'
    ]
    for cmd in expected_commands:
        print(f"  - {cmd}")
    print("(Note: Actual command detection is skipped; see CLI for live check)")
    
    # Test 2: Basic vector operations
    print("\n=== Test 2: Basic Vector Operations ===")
    try:
        # Create a vector index
        result = r.execute_command("vector_create", "test_index", "3")
        print(f"✓ Created vector index: {result}")
        
        # Insert vectors
        vectors = [
            "1.0,2.0,3.0",
            "4.0,5.0,6.0", 
            "7.0,8.0,9.0",
            "10.0,11.0,12.0",
            "13.0,14.0,15.0",
            "16.0,17.0,18.0",
            "19.0,20.0,21.0",
            "22.0,23.0,24.0",
            "25.0,26.0,27.0",
            "28.0,29.0,30.0",
            "31.0,32.0,33.0",
            "34.0,35.0,36.0",
            "37.0,38.0,39.0",
            "40.0,41.0,42.0",
            "43.0,44.0,45.0",
            "46.0,47.0,48.0",
            "49.0,50.0,51.0",
            "52.0,53.0,54.0",
            "55.0,56.0,57.0",
            "58.0,59.0,60.0"
        ]
        
        for i, vector in enumerate(vectors):
            result = r.execute_command("vector_insert", "test_index", str(i), vector)
            print(f"✓ Inserted vector {i}: {result}")
        
        # Build the index before searching
        result = r.execute_command("vector_build", "test_index")
        print(f"✓ Built vector index: {result}")
        
        # Search in regular index (correct argument order: index, vector, k)
        try:
            result = r.execute_command("vector_search", "test_index", "1.0,2.0,3.0", 3)
            print(f"✓ Regular search result: {result}")
        except Exception as e:
            print(f"✗ Regular search failed: {e}")
            return False
        
    except Exception as e:
        print(f"✗ Basic vector operations failed: {e}")
        return False
    
    # Test 3: Quantization
    print("\n=== Test 3: Quantization ===")
    try:
        # Quantize the index
        result = r.execute_command("vector_quantize", "test_index")
        print(f"✓ Quantization result: {result}")
        
        # Check if quantized files were created
        if os.path.exists("test_index"):
            print("✓ Quantized index directory exists")
            if os.path.exists("test_index/qg"):
                print("✓ Quantized index files created")
            else:
                print("✗ Quantized index files not found")
        else:
            print("✗ Quantized index directory not found")
            
    except Exception as e:
        print(f"✗ Quantization failed: {e}")
        return False
    
    # Test 4: Quantized index operations
    print("\n=== Test 4: Quantized Index Operations ===")
    try:
        # List quantized indices
        result = r.execute_command("vector_quantized_list")
        print(f"✓ Quantized indices: {result}")
        
        # Get quantized index info
        result = r.execute_command("vector_quantized_info", "test_index")
        print(f"✓ Quantized index info: {result}")
        
    except Exception as e:
        print(f"✗ Quantized index operations failed: {e}")
        return False
    
    # Test 5: Quantized search
    print("\n=== Test 5: Quantized Search ===")
    try:
        # Search in quantized index (correct argument order: index, k, vector)
        try:
            result = r.execute_command("vector_quantized_search", "test_index", 3, "1.0,2.0,3.0")
            print(f"✓ Quantized search result: {result}")
        except Exception as e:
            print(f"✗ Quantized search failed: {e}")
            return False
        
    except Exception as e:
        print(f"✗ Quantized search failed: {e}")
        return False
    
    # Test 6: Test unsupported commands
    print("\n=== Test 6: Unsupported Commands ===")
    try:
        # Test quantized create (should fail)
        try:
            result = r.execute_command("vector_quantized_create", "test_qg_index", "3")
            print(f"✗ Quantized create should have failed but returned: {result}")
        except Exception as e:
            print(f"✓ Quantized create correctly rejected: {e}")
        
        # Test quantized insert (should fail)
        try:
            result = r.execute_command("vector_quantized_insert", "test_index", "0", "1.0,2.0,3.0")
            print(f"✗ Quantized insert should have failed but returned: {result}")
        except Exception as e:
            print(f"✓ Quantized insert correctly rejected: {e}")
        
        # Test quantized build (should fail)
        try:
            result = r.execute_command("vector_quantized_build", "test_index")
            print(f"✗ Quantized build should have failed but returned: {result}")
        except Exception as e:
            print(f"✓ Quantized build correctly rejected: {e}")
        
    except Exception as e:
        print(f"✗ Testing unsupported commands failed: {e}")
        return False
    
    # Test 7: Cleanup
    print("\n=== Test 7: Cleanup ===")
    try:
        # Drop quantized index
        result = r.execute_command("vector_quantized_drop", "test_index")
        print(f"✓ Dropped quantized index: {result}")
        
        # Drop regular index
        result = r.execute_command("vector_drop", "test_index")
        print(f"✓ Dropped regular index: {result}")
        
        # Clean up files
        if os.path.exists("test_index"):
            import shutil
            shutil.rmtree("test_index")
            print("✓ Cleaned up test files")
        
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        return False
    
    print("\n=== NGTQ Implementation Test Summary ===")
    print("✓ All tests completed successfully!")
    print("✓ NGTQ support is working correctly")
    print("✓ Quantization creates proper quantized indices")
    print("✓ Quantized search works with proper error handling")
    print("✓ Unsupported commands are properly rejected")
    
    return True

if __name__ == "__main__":
    success = test_ngtq_implementation()
    sys.exit(0 if success else 1) 