#!/usr/bin/env python3
import redis
import numpy as np

def debug_search():
    """Debug the quantized search dimension issue"""
    
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    print("🔍 Debug Quantized Search")
    print("=" * 30)
    
    try:
        # 1. Create and prepare index
        print("1. Creating index...")
        r.execute_command("vector_create", "debug_test", 32)
        
        # 2. Insert vectors
        print("2. Inserting vectors...")
        for i in range(3):
            vector = np.random.rand(32).astype(np.float32)
            vector_str = ",".join(map(str, vector))
            r.execute_command("vector_insert", "debug_test", i, vector_str)
        
        # 3. Build and quantize
        print("3. Building and quantizing...")
        r.execute_command("vector_build", "debug_test")
        r.execute_command("vector_quantize", "debug_test")
        
        # 4. Get quantized info
        print("4. Getting quantized info...")
        info = r.execute_command("vector_quantized_info", "debug_test")
        print(f"   Info: {info}")
        
        # 5. Test search with different dimensions
        print("5. Testing search...")
        
        # Try with 32 dimensions (original)
        query_32 = np.random.rand(32).astype(np.float32)
        query_str_32 = ",".join(map(str, query_32))
        print(f"   Trying with 32 dimensions...")
        try:
            result = r.execute_command("vector_quantized_search", "debug_test", query_str_32, 3)
            print(f"   Success: {result}")
        except Exception as e:
            print(f"   Failed: {e}")
        
        # Try with 16 dimensions (half)
        query_16 = np.random.rand(16).astype(np.float32)
        query_str_16 = ",".join(map(str, query_16))
        print(f"   Trying with 16 dimensions...")
        try:
            result = r.execute_command("vector_quantized_search", "debug_test", query_str_16, 3)
            print(f"   Success: {result}")
        except Exception as e:
            print(f"   Failed: {e}")
        
        # Try with 64 dimensions (double)
        query_64 = np.random.rand(64).astype(np.float32)
        query_str_64 = ",".join(map(str, query_64))
        print(f"   Trying with 64 dimensions...")
        try:
            result = r.execute_command("vector_quantized_search", "debug_test", query_str_64, 3)
            print(f"   Success: {result}")
        except Exception as e:
            print(f"   Failed: {e}")
        
        # 6. Clean up
        print("6. Cleaning up...")
        r.execute_command("vector_quantized_drop", "debug_test")
        r.execute_command("vector_drop", "debug_test")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = debug_search()
    if success:
        print("\n✅ Debug completed!")
    else:
        print("\n❌ Debug failed!") 