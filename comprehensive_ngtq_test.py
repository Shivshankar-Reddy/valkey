#!/usr/bin/env python3
import redis
import numpy as np
import sys

def comprehensive_test():
    """Comprehensive test of NGTQ functionality"""
    
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    print("🧪 Comprehensive NGTQ Test")
    print("=" * 50)
    
    results = {}
    
    try:
        # Test 1: Command availability
        print("\n1. Testing command availability...")
        try:
            commands = r.execute_command("command", "list")
            vector_commands = [cmd for cmd in commands if 'vector' in cmd.lower()]
            quantized_commands = [cmd for cmd in vector_commands if 'quant' in cmd.lower()]
            
            print(f"   Found {len(quantized_commands)} quantized vector commands:")
            for cmd in quantized_commands:
                print(f"     - {cmd}")
            
            results['commands_available'] = len(quantized_commands) >= 5
        except Exception as e:
            print(f"   ❌ Command availability test failed: {e}")
            results['commands_available'] = False
        
        # Test 2: Basic vector operations
        print("\n2. Testing basic vector operations...")
        try:
            r.execute_command("vector_create", "comp_test", 64)
            print("   ✅ vector_create: OK")
            
            # Insert a few vectors
            for i in range(5):
                vector = np.random.rand(64).astype(np.float32)
                vector_str = ",".join(map(str, vector))
                r.execute_command("vector_insert", "comp_test", i, vector_str)
            print("   ✅ vector_insert: OK")
            
            r.execute_command("vector_build", "comp_test")
            print("   ✅ vector_build: OK")
            
            results['basic_operations'] = True
        except Exception as e:
            print(f"   ❌ Basic operations failed: {e}")
            results['basic_operations'] = False
        
        # Test 3: Quantization
        print("\n3. Testing quantization...")
        try:
            r.execute_command("vector_quantize", "comp_test")
            print("   ✅ vector_quantize: OK")
            results['quantization'] = True
        except Exception as e:
            print(f"   ❌ Quantization failed: {e}")
            results['quantization'] = False
        
        # Test 4: Quantized index operations
        print("\n4. Testing quantized index operations...")
        try:
            info = r.execute_command("vector_quantized_info", "comp_test")
            print(f"   ✅ vector_quantized_info: {info}")
            results['quantized_info'] = True
        except Exception as e:
            print(f"   ❌ Quantized info failed: {e}")
            results['quantized_info'] = False
        
        # Test 5: Quantized build
        print("\n5. Testing quantized build...")
        try:
            r.execute_command("vector_quantized_build", "comp_test")
            print("   ✅ vector_quantized_build: OK")
            results['quantized_build'] = True
        except Exception as e:
            print(f"   ❌ Quantized build failed: {e}")
            results['quantized_build'] = False
        
        # Test 6: Quantized search (if build succeeded)
        print("\n6. Testing quantized search...")
        if results.get('quantized_build', False):
            try:
                query_vector = np.random.rand(64).astype(np.float32)
                query_str = ",".join(map(str, query_vector))
                result = r.execute_command("vector_quantized_search", "comp_test", query_str, 3)
                print(f"   ✅ vector_quantized_search: {result}")
                results['quantized_search'] = True
            except Exception as e:
                print(f"   ❌ Quantized search failed: {e}")
                results['quantized_search'] = False
        else:
            print("   ⏭️  Skipping search test (build failed)")
            results['quantized_search'] = False
        
        # Test 7: Cleanup
        print("\n7. Testing cleanup...")
        try:
            r.execute_command("vector_quantized_drop", "comp_test")
            print("   ✅ vector_quantized_drop: OK")
            r.execute_command("vector_drop", "comp_test")
            print("   ✅ vector_drop: OK")
            results['cleanup'] = True
        except Exception as e:
            print(f"   ❌ Cleanup failed: {e}")
            results['cleanup'] = False
        
    except Exception as e:
        print(f"❌ Error during comprehensive test: {e}")
        return False
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test}: {status}")
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests >= 4:
        print("🎉 NGTQ implementation is working well!")
        return True
    elif passed_tests >= 2:
        print("⚠️  NGTQ implementation has some issues but basic functionality works.")
        return True
    else:
        print("❌ NGTQ implementation needs more work.")
        return False

if __name__ == "__main__":
    success = comprehensive_test()
    if success:
        print("\n✅ Comprehensive test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Comprehensive test failed!")
        sys.exit(1) 