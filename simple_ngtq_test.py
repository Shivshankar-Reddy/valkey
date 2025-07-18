#!/usr/bin/env python3
import redis
import numpy as np

def simple_test():
    """Simple test to debug NGTQ functionality"""
    
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    print("🔍 Simple NGTQ Test")
    print("=" * 30)
    
    try:
        # 1. Create index
        print("1. Creating index...")
        result = r.execute_command("vector_create", "simple_test", 32)
        print(f"   Result: {result}")
        
        # 2. Insert a few vectors
        print("\n2. Inserting vectors...")
        for i in range(5):
            vector = np.random.rand(32).astype(np.float32)
            vector_str = ",".join(map(str, vector))
            result = r.execute_command("vector_insert", "simple_test", i, vector_str)
            print(f"   Vector {i}: {result}")
        
        # 3. Build index
        print("\n3. Building index...")
        result = r.execute_command("vector_build", "simple_test")
        print(f"   Result: {result}")
        
        # 4. Try to quantize
        print("\n4. Quantizing index...")
        try:
            result = r.execute_command("vector_quantize", "simple_test")
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 5. Check if quantized index exists
        print("\n5. Checking quantized index info...")
        try:
            result = r.execute_command("vector_quantized_info", "simple_test")
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 6. Try to build quantized index
        print("\n6. Building quantized index...")
        try:
            result = r.execute_command("vector_quantized_build", "simple_test")
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 7. Test quantized search
        print("\n7. Testing quantized search...")
        try:
            query_vector = np.random.rand(32).astype(np.float32)
            query_str = ",".join(map(str, query_vector))
            result = r.execute_command("vector_quantized_search", "simple_test", query_str, 3)
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 8. Clean up
        print("\n8. Cleaning up...")
        try:
            r.execute_command("vector_quantized_drop", "simple_test")
            print("   Dropped quantized index")
        except:
            pass
        
        r.execute_command("vector_drop", "simple_test")
        print("   Dropped regular index")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = simple_test()
    if success:
        print("\n✅ Simple test completed!")
    else:
        print("\n❌ Simple test failed!") 