#!/usr/bin/env python3
"""
Comprehensive test script for all NGT and NGTQG vector commands in Valkey
Tests all the advanced commands we implemented: RECONSTRUCT_GRAPH, QBG.CREATE_QG, QBG.BUILD_QG
"""

import redis
import numpy as np
import time
import json
import sys
from typing import List, Dict, Any

class VectorCommandTester:
    def __init__(self, host='localhost', port=6380):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
    def test_basic_vector_operations(self):
        """Test basic vector operations first"""
        print("\n=== Testing Basic Vector Operations ===")
        
        try:
            # Test vector_create
            result = self.redis_client.execute_command('vector_create', 'test_index', 'DIM', '128', 'DISTANCE_METRIC', 'L2')
            self.log_test("vector_create", result == 'OK', f"Created index: {result}")
            
            # Test vector_insert
            vector = np.random.rand(128).astype(np.float32)
            result = self.redis_client.execute_command('vector_insert', 'test_index', 'vec1', *vector.tolist())
            self.log_test("vector_insert", result == 'OK', f"Inserted vector: {result}")
            
            # Test vector_search
            result = self.redis_client.execute_command('vector_search', 'test_index', *vector.tolist(), 'LIMIT', '5')
            self.log_test("vector_search", len(result) > 0, f"Search returned {len(result)} results")
            
            return True
        except Exception as e:
            self.log_test("Basic Vector Operations", False, str(e))
            return False
            
    def test_reconstruct_graph(self):
        """Test vector_reconstruct_graph command"""
        print("\n=== Testing vector_reconstruct_graph ===")
        
        try:
            # Create a test index with some vectors
            self.redis_client.execute_command('vector_create', 'reconstruct_test', 'DIM', '64', 'DISTANCE_METRIC', 'L2')
            
            # Insert some test vectors
            for i in range(10):
                vector = np.random.rand(64).astype(np.float32)
                self.redis_client.execute_command('vector_insert', 'reconstruct_test', f'vec_{i}', *vector.tolist())
            
            # Test RECONSTRUCT_GRAPH
            result = self.redis_client.execute_command('vector_reconstruct_graph', 'reconstruct_test')
            self.log_test("vector_reconstruct_graph", result == 'OK', f"Result: {result}")
            
            return True
        except Exception as e:
            self.log_test("vector_reconstruct_graph", False, str(e))
            return False
            
    def test_qbg_create_qg(self):
        """Test vector_qbg_create_qg command"""
        print("\n=== Testing vector_qbg_create_qg ===")
        
        try:
            # Create a test index
            self.redis_client.execute_command('vector_create', 'qbg_test', 'DIM', '64', 'DISTANCE_METRIC', 'L2')
            
            # Insert some test vectors
            for i in range(20):
                vector = np.random.rand(64).astype(np.float32)
                self.redis_client.execute_command('vector_insert', 'qbg_test', f'vec_{i}', *vector.tolist())
            
            # Test QBG.CREATE_QG with different parameters
            test_cases = [
                {'params': ['qbg_test', 'qg1'], 'desc': 'Basic QG creation'},
                {'params': ['qbg_test', 'qg2', 'BITS', '8'], 'desc': 'With BITS parameter'},
                {'params': ['qbg_test', 'qg3', 'BITS', '4', 'THRESHOLD', '0.1'], 'desc': 'With BITS and THRESHOLD'},
            ]
            
            for i, test_case in enumerate(test_cases):
                try:
                    result = self.redis_client.execute_command('vector_qbg_create_qg', *test_case['params'])
                    self.log_test(f"vector_qbg_create_qg {i+1}", result == 'OK', 
                                f"{test_case['desc']}: {result}")
                except Exception as e:
                    self.log_test(f"vector_qbg_create_qg {i+1}", False, 
                                f"{test_case['desc']}: {str(e)}")
            
            return True
        except Exception as e:
            self.log_test("vector_qbg_create_qg", False, str(e))
            return False
            
    def test_qbg_build_qg(self):
        """Test vector_qbg_build_qg command"""
        print("\n=== Testing vector_qbg_build_qg ===")
        
        try:
            # Create a test index
            self.redis_client.execute_command('vector_create', 'build_qg_test', 'DIM', '64', 'DISTANCE_METRIC', 'L2')
            
            # Insert some test vectors
            for i in range(30):
                vector = np.random.rand(64).astype(np.float32)
                self.redis_client.execute_command('vector_insert', 'build_qg_test', f'vec_{i}', *vector.tolist())
            
            # Create a QG first
            self.redis_client.execute_command('vector_qbg_create_qg', 'build_qg_test', 'test_qg')
            
            # Test QBG.BUILD_QG with different parameters
            test_cases = [
                {'params': ['build_qg_test', 'test_qg'], 'desc': 'Basic QG build'},
                {'params': ['build_qg_test', 'test_qg', 'EPSILON', '0.1'], 'desc': 'With EPSILON parameter'},
                {'params': ['build_qg_test', 'test_qg', 'EPSILON', '0.05', 'THRESHOLD', '0.1'], 'desc': 'With EPSILON and THRESHOLD'},
            ]
            
            for i, test_case in enumerate(test_cases):
                try:
                    result = self.redis_client.execute_command('vector_qbg_build_qg', *test_case['params'])
                    self.log_test(f"vector_qbg_build_qg {i+1}", result == 'OK', 
                                f"{test_case['desc']}: {result}")
                except Exception as e:
                    self.log_test(f"vector_qbg_build_qg {i+1}", False, 
                                f"{test_case['desc']}: {str(e)}")
            
            return True
        except Exception as e:
            self.log_test("vector_qbg_build_qg", False, str(e))
            return False
            
    def test_error_handling(self):
        """Test error handling for invalid parameters"""
        print("\n=== Testing Error Handling ===")
        
        try:
            # Test with non-existent index
            try:
                result = self.redis_client.execute_command('vector_reconstruct_graph', 'non_existent_index')
                self.log_test("Error handling - non-existent index", False, "Should have failed")
            except Exception as e:
                self.log_test("Error handling - non-existent index", True, f"Correctly failed: {str(e)}")
            
            # Test with invalid parameters
            try:
                result = self.redis_client.execute_command('vector_qbg_create_qg', 'invalid_params')
                self.log_test("Error handling - invalid parameters", False, "Should have failed")
            except Exception as e:
                self.log_test("Error handling - invalid parameters", True, f"Correctly failed: {str(e)}")
                
            return True
        except Exception as e:
            self.log_test("Error Handling", False, str(e))
            return False
            
    def test_command_listing(self):
        """Test that all commands are properly registered"""
        print("\n=== Testing Command Registration ===")
        
        try:
            # Get all commands
            commands = self.redis_client.execute_command('COMMAND')
            
            # Check for our new commands
            command_names = [cmd[0] for cmd in commands]
            
            expected_commands = [
                'vector_reconstruct_graph',
                'vector_qbg_create_qg', 
                'vector_qbg_build_qg'
            ]
            
            for cmd in expected_commands:
                found = cmd in command_names
                self.log_test(f"Command registered: {cmd}", found, 
                            f"Command {'found' if found else 'not found'} in command list")
            
            return True
        except Exception as e:
            self.log_test("Command Registration", False, str(e))
            return False
            
    def cleanup(self):
        """Clean up test data"""
        print("\n=== Cleaning Up ===")
        
        try:
            # Delete test indices
            test_indices = ['test_index', 'reconstruct_test', 'qbg_test', 'build_qg_test']
            for index in test_indices:
                try:
                    self.redis_client.execute_command('vector_drop', index)
                    print(f"✅ Deleted index: {index}")
                except:
                    pass  # Index might not exist
                    
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
            
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting comprehensive vector command tests...")
        print(f"Testing against Redis server at localhost:6380")
        
        # Test basic connectivity
        try:
            self.redis_client.ping()
            print("✅ Connected to Redis server")
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            return
            
        # Run all test suites
        test_suites = [
            self.test_command_listing,
            self.test_basic_vector_operations,
            self.test_reconstruct_graph,
            self.test_qbg_create_qg,
            self.test_qbg_build_qg,
            self.test_error_handling
        ]
        
        for test_suite in test_suites:
            test_suite()
            
        # Print summary
        self.print_summary()
        
        # Cleanup
        self.cleanup()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print("📊 TEST SUMMARY")
        print("="*50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("="*50)

if __name__ == "__main__":
    tester = VectorCommandTester()
    tester.run_all_tests() 