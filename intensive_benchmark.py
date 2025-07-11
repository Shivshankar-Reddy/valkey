#!/usr/bin/env python3
import redis
import time
import numpy as np
from datetime import datetime

class IntensiveVectorBenchmark:
    def __init__(self, host='127.0.0.1', port=6379):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.results = {}
        
    def benchmark_large_scale_insertion(self, num_vectors=10000, dimensions=[64, 128, 256]):
        """Benchmark large-scale vector insertion"""
        print("=== LARGE SCALE INSERTION BENCHMARK ===")
        
        for dim in dimensions:
            index_name = f"large_scale_{dim}"
            
            # Create index
            try:
                self.redis_client.execute_command("vector_create", index_name, dim)
                print(f"Created index for {dim}D vectors")
            except:
                pass
                
            # Generate vectors in batches
            batch_size = 1000
            total_time = 0
            vectors_inserted = 0
            
            for batch_start in range(0, num_vectors, batch_size):
                batch_end = min(batch_start + batch_size, num_vectors)
                batch_size_actual = batch_end - batch_start
                
                # Generate batch of vectors
                vectors = []
                for i in range(batch_size_actual):
                    vector = np.random.rand(dim).astype(np.float32)
                    vector_str = ",".join([str(x) for x in vector])
                    vectors.append(vector_str)
                
                # Insert batch
                start_time = time.time()
                for i, vector_str in enumerate(vectors):
                    try:
                        self.redis_client.execute_command("vector_insert", index_name, batch_start + i + 1, vector_str)
                        vectors_inserted += 1
                    except Exception as e:
                        print(f"Error inserting vector {batch_start + i}: {e}")
                        break
                end_time = time.time()
                
                batch_time = end_time - start_time
                total_time += batch_time
                
                print(f"Inserted batch {batch_start//batch_size + 1}/{(num_vectors + batch_size - 1)//batch_size} "
                      f"({batch_size_actual} vectors) in {batch_time:.4f}s")
                
                if vectors_inserted % 5000 == 0:
                    print(f"Progress: {vectors_inserted}/{num_vectors} vectors inserted")
            
            throughput = vectors_inserted / total_time if total_time > 0 else 0
            print(f"\n{dim}D Results:")
            print(f"  Total vectors inserted: {vectors_inserted}")
            print(f"  Total time: {total_time:.4f}s")
            print(f"  Throughput: {throughput:.2f} vectors/second")
            print(f"  Average time per vector: {total_time/vectors_inserted:.6f}s")
            
            self.results[f'large_scale_insertion_{dim}D'] = {
                'vectors_inserted': vectors_inserted,
                'total_time': total_time,
                'throughput': throughput,
                'avg_time_per_vector': total_time/vectors_inserted if vectors_inserted > 0 else 0
            }
            
    def benchmark_large_scale_search(self, num_queries=1000, k_values=[1, 5, 10, 50], dimensions=[64, 128]):
        """Benchmark large-scale vector search"""
        print("\n=== LARGE SCALE SEARCH BENCHMARK ===")
        
        for dim in dimensions:
            index_name = f"large_scale_{dim}"
            
            # Build the index if it exists
            try:
                self.redis_client.execute_command("vector_build", index_name)
                print(f"Built index for {dim}D search")
            except Exception as e:
                print(f"Error building index for {dim}D: {e}")
                continue
                
            for k in k_values:
                query_times = []
                
                print(f"Testing {dim}D search with k={k}...")
                
                for i in range(num_queries):
                    query_vector = np.random.rand(dim).astype(np.float32)
                    query_str = ",".join([str(x) for x in query_vector])
                    
                    start_time = time.time()
                    try:
                        results = self.redis_client.execute_command("vector_search", index_name, query_str, k)
                        end_time = time.time()
                        query_times.append(end_time - start_time)
                    except Exception as e:
                        print(f"Error in search query {i}: {e}")
                        continue
                    
                    if (i + 1) % 100 == 0:
                        print(f"  Completed {i + 1}/{num_queries} queries")
                
                if query_times:
                    avg_time = np.mean(query_times)
                    throughput = len(query_times) / sum(query_times)
                    p95_time = np.percentile(query_times, 95)
                    p99_time = np.percentile(query_times, 99)
                    
                    print(f"  {dim}D search with k={k}:")
                    print(f"    Average time: {avg_time:.6f}s")
                    print(f"    P95 time: {p95_time:.6f}s")
                    print(f"    P99 time: {p99_time:.6f}s")
                    print(f"    Throughput: {throughput:.2f} queries/sec")
                    print(f"    Successful queries: {len(query_times)}/{num_queries}")
                    
                    self.results[f'large_scale_search_{dim}D_k{k}'] = {
                        'avg_time': avg_time,
                        'p95_time': p95_time,
                        'p99_time': p99_time,
                        'throughput': throughput,
                        'successful_queries': len(query_times),
                        'total_queries': num_queries
                    }
                    
    def benchmark_concurrent_operations(self, num_threads=4, operations_per_thread=1000):
        """Benchmark concurrent operations"""
        print("\n=== CONCURRENT OPERATIONS BENCHMARK ===")
        
        import threading
        
        results = []
        lock = threading.Lock()
        
        def worker(thread_id):
            thread_results = []
            
            for i in range(operations_per_thread):
                op_type = np.random.choice(['create', 'insert', 'search', 'info'], p=[0.1, 0.3, 0.5, 0.1])
                
                start_time = time.time()
                success = False
                
                try:
                    if op_type == 'create':
                        dim = np.random.choice([64, 128, 256])
                        index_name = f"concurrent_{thread_id}_{i}_{dim}"
                        self.redis_client.execute_command("vector_create", index_name, dim)
                        success = True
                        
                    elif op_type == 'insert':
                        index_name = f"concurrent_{thread_id//2}_64"
                        vector = np.random.rand(64).astype(np.float32)
                        vector_str = ",".join([str(x) for x in vector])
                        self.redis_client.execute_command("vector_insert", index_name, i, vector_str)
                        success = True
                        
                    elif op_type == 'search':
                        index_name = f"concurrent_{thread_id//2}_64"
                        query_vector = np.random.rand(64).astype(np.float32)
                        query_str = ",".join([str(x) for x in query_vector])
                        self.redis_client.execute_command("vector_search", index_name, query_str, 5)
                        success = True
                        
                    elif op_type == 'info':
                        index_name = f"concurrent_{thread_id//2}_64"
                        self.redis_client.execute_command("vector_info", index_name)
                        success = True
                        
                except Exception as e:
                    pass  # Ignore errors for concurrent benchmark
                    
                end_time = time.time()
                
                if success:
                    thread_results.append((op_type, end_time - start_time))
                    
            with lock:
                results.extend(thread_results)
        
        # Create some initial indices for concurrent operations
        for i in range(num_threads // 2):
            try:
                self.redis_client.execute_command("vector_create", f"concurrent_{i}_64", 64)
                for j in range(100):
                    vector = np.random.rand(64).astype(np.float32)
                    vector_str = ",".join([str(x) for x in vector])
                    self.redis_client.execute_command("vector_insert", f"concurrent_{i}_64", j+1, vector_str)
                self.redis_client.execute_command("vector_build", f"concurrent_{i}_64")
            except:
                pass
        
        # Start threads
        threads = []
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        op_counts = {}
        op_times = {}
        
        for op_type, op_time in results:
            op_counts[op_type] = op_counts.get(op_type, 0) + 1
            if op_type not in op_times:
                op_times[op_type] = []
            op_times[op_type].append(op_time)
        
        print(f"Concurrent benchmark results:")
        print(f"  Total operations: {len(results)}")
        print(f"  Total time: {total_time:.4f}s")
        print(f"  Overall throughput: {len(results)/total_time:.2f} ops/sec")
        print(f"  Threads: {num_threads}")
        print(f"  Operations per thread: {operations_per_thread}")
        
        for op_type in op_counts:
            if op_times[op_type]:
                avg_time = np.mean(op_times[op_type])
                throughput = len(op_times[op_type]) / sum(op_times[op_type])
                print(f"  {op_type}: {op_counts[op_type]} ops, {avg_time:.6f}s avg, {throughput:.2f} ops/sec")
        
        self.results['concurrent_operations'] = {
            'total_operations': len(results),
            'total_time': total_time,
            'overall_throughput': len(results) / total_time,
            'threads': num_threads,
            'operations_per_thread': operations_per_thread,
            'operation_counts': op_counts,
            'operation_times': {op: np.mean(times) for op, times in op_times.items()}
        }
        
    def benchmark_memory_usage(self, dimensions=[64, 128, 256]):
        """Benchmark memory usage with different vector dimensions"""
        print("\n=== MEMORY USAGE BENCHMARK ===")
        
        for dim in dimensions:
            index_name = f"memory_test_{dim}"
            
            # Get initial memory info
            try:
                info = self.redis_client.info('memory')
                initial_memory = info.get('used_memory', 0)
                print(f"Initial memory usage: {initial_memory / 1024 / 1024:.2f} MB")
            except:
                initial_memory = 0
            
            # Create index
            try:
                self.redis_client.execute_command("vector_create", index_name, dim)
                
                # Insert vectors in batches and monitor memory
                batch_size = 1000
                total_vectors = 0
                
                for batch in range(10):  # 10 batches of 1000 vectors each
                    for i in range(batch_size):
                        vector = np.random.rand(dim).astype(np.float32)
                        vector_str = ",".join([str(x) for x in vector])
                        self.redis_client.execute_command("vector_insert", index_name, total_vectors + i + 1, vector_str)
                    
                    total_vectors += batch_size
                    
                    # Check memory usage
                    try:
                        info = self.redis_client.info('memory')
                        current_memory = info.get('used_memory', 0)
                        memory_increase = current_memory - initial_memory
                        memory_per_vector = memory_increase / total_vectors if total_vectors > 0 else 0
                        
                        print(f"  After {total_vectors} vectors: {current_memory / 1024 / 1024:.2f} MB "
                              f"(+{memory_increase / 1024 / 1024:.2f} MB, {memory_per_vector / 1024:.2f} KB/vector)")
                    except:
                        pass
                
                # Build index
                self.redis_client.execute_command("vector_build", index_name)
                
                # Final memory check
                try:
                    info = self.redis_client.info('memory')
                    final_memory = info.get('used_memory', 0)
                    total_increase = final_memory - initial_memory
                    
                    print(f"  Final memory usage: {final_memory / 1024 / 1024:.2f} MB")
                    print(f"  Total memory increase: {total_increase / 1024 / 1024:.2f} MB")
                    print(f"  Memory per vector: {total_increase / total_vectors / 1024:.2f} KB")
                    
                    self.results[f'memory_usage_{dim}D'] = {
                        'total_vectors': total_vectors,
                        'initial_memory_mb': initial_memory / 1024 / 1024,
                        'final_memory_mb': final_memory / 1024 / 1024,
                        'memory_increase_mb': total_increase / 1024 / 1024,
                        'memory_per_vector_kb': total_increase / total_vectors / 1024
                    }
                    
                except Exception as e:
                    print(f"  Error getting final memory info: {e}")
                    
            except Exception as e:
                print(f"Error in memory benchmark for {dim}D: {e}")
                
    def run_intensive_benchmarks(self):
        """Run all intensive benchmarks"""
        print("Starting Intensive Vector Search Benchmarks")
        print("=" * 60)
        print(f"Timestamp: {datetime.now()}")
        print("=" * 60)
        
        try:
            self.redis_client.ping()
            print("✓ Connected to Valkey server")
        except Exception as e:
            print(f"✗ Failed to connect to Valkey: {e}")
            return
            
        # Run intensive benchmarks
        self.benchmark_large_scale_insertion()
        self.benchmark_large_scale_search()
        self.benchmark_concurrent_operations()
        self.benchmark_memory_usage()
        
        # Print summary
        self.print_intensive_summary()
        
    def print_intensive_summary(self):
        """Print intensive benchmark summary"""
        print("\n" + "=" * 60)
        print("INTENSIVE BENCHMARK SUMMARY")
        print("=" * 60)
        
        for benchmark_name, results in self.results.items():
            print(f"\n{benchmark_name.upper()}:")
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, float):
                        print(f"  {key}: {value:.4f}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print(f"  {results}")
                
        print("\n" + "=" * 60)

if __name__ == "__main__":
    benchmark = IntensiveVectorBenchmark()
    benchmark.run_intensive_benchmarks() 