#!/usr/bin/env python3
import redis
import time
import random
import numpy as np
from datetime import datetime

class VectorBenchmark:
    def __init__(self, host='127.0.0.1', port=6379):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.results = {}
        
    def benchmark_vector_create(self, num_indices=10, dimensions=[64, 128, 256]):
        """Benchmark vector index creation"""
        print("=== VECTOR CREATE BENCHMARK ===")
        times = []
        
        for i in range(num_indices):
            for dim in dimensions:
                index_name = f"benchmark_index_{i}_{dim}"
                start_time = time.time()
                
                try:
                    # Create index with default parameters
                    self.redis_client.execute_command("vector_create", index_name, dim)
                    end_time = time.time()
                    times.append(end_time - start_time)
                    print(f"Created index {index_name} in {end_time - start_time:.4f}s")
                except Exception as e:
                    print(f"Error creating index {index_name}: {e}")
                    
        avg_time = np.mean(times) if times else 0
        self.results['vector_create'] = {
            'avg_time': avg_time,
            'total_operations': len(times),
            'throughput': len(times) / sum(times) if times else 0
        }
        print(f"Average creation time: {avg_time:.4f}s")
        print(f"Throughput: {self.results['vector_create']['throughput']:.2f} indices/second")
        
    def benchmark_vector_insert(self, num_vectors=1000, dimensions=[64, 128]):
        """Benchmark vector insertion"""
        print("\n=== VECTOR INSERT BENCHMARK ===")
        times = []
        
        for dim in dimensions:
            index_name = f"insert_benchmark_{dim}"
            
            # Create index
            try:
                self.redis_client.execute_command("vector_create", index_name, dim)
            except:
                pass  # Index might already exist
                
            # Generate random vectors
            vectors = []
            for i in range(num_vectors):
                vector = np.random.rand(dim).astype(np.float32)
                vector_str = ",".join([str(x) for x in vector])
                vectors.append(vector_str)
            
            # Benchmark insertion
            start_time = time.time()
            for i, vector_str in enumerate(vectors):
                try:
                    self.redis_client.execute_command("vector_insert", index_name, i+1, vector_str)
                except Exception as e:
                    print(f"Error inserting vector {i}: {e}")
                    break
            end_time = time.time()
            
            total_time = end_time - start_time
            times.append(total_time)
            print(f"Inserted {num_vectors} {dim}D vectors in {total_time:.4f}s")
            print(f"Throughput: {num_vectors/total_time:.2f} vectors/second")
            
        self.results['vector_insert'] = {
            'avg_time': np.mean(times) if times else 0,
            'total_vectors': num_vectors * len(dimensions),
            'throughput': (num_vectors * len(dimensions)) / sum(times) if times else 0
        }
        
    def benchmark_vector_build(self, dimensions=[64, 128]):
        """Benchmark vector index building"""
        print("\n=== VECTOR BUILD BENCHMARK ===")
        times = []
        
        for dim in dimensions:
            index_name = f"build_benchmark_{dim}"
            
            # Create and populate index
            try:
                self.redis_client.execute_command("vector_create", index_name, dim)
                
                # Insert some vectors
                for i in range(100):
                    vector = np.random.rand(dim).astype(np.float32)
                    vector_str = ",".join([str(x) for x in vector])
                    self.redis_client.execute_command("vector_insert", index_name, i+1, vector_str)
                
                # Benchmark build
                start_time = time.time()
                self.redis_client.execute_command("vector_build", index_name)
                end_time = time.time()
                
                build_time = end_time - start_time
                times.append(build_time)
                print(f"Built {dim}D index with 100 vectors in {build_time:.4f}s")
                
            except Exception as e:
                print(f"Error in build benchmark for {dim}D: {e}")
                
        self.results['vector_build'] = {
            'avg_time': np.mean(times) if times else 0,
            'total_operations': len(times),
            'throughput': len(times) / sum(times) if times else 0
        }
        
    def benchmark_vector_search(self, num_queries=100, k_values=[1, 5, 10], dimensions=[64, 128]):
        """Benchmark vector search"""
        print("\n=== VECTOR SEARCH BENCHMARK ===")
        times = {}
        
        for dim in dimensions:
            index_name = f"search_benchmark_{dim}"
            
            # Create and populate index
            try:
                self.redis_client.execute_command("vector_create", index_name, dim)
                
                # Insert vectors
                for i in range(1000):
                    vector = np.random.rand(dim).astype(np.float32)
                    vector_str = ",".join([str(x) for x in vector])
                    self.redis_client.execute_command("vector_insert", index_name, i+1, vector_str)
                
                # Build index
                self.redis_client.execute_command("vector_build", index_name)
                
                # Benchmark search for different k values
                for k in k_values:
                    query_times = []
                    
                    for _ in range(num_queries):
                        query_vector = np.random.rand(dim).astype(np.float32)
                        query_str = ",".join([str(x) for x in query_vector])
                        
                        start_time = time.time()
                        try:
                            results = self.redis_client.execute_command("vector_search", index_name, query_str, k)
                            end_time = time.time()
                            query_times.append(end_time - start_time)
                        except Exception as e:
                            print(f"Error in search: {e}")
                            continue
                    
                    if query_times:
                        avg_time = np.mean(query_times)
                        throughput = len(query_times) / sum(query_times)
                        key = f"{dim}D_k{k}"
                        times[key] = {
                            'avg_time': avg_time,
                            'throughput': throughput,
                            'queries': len(query_times)
                        }
                        print(f"{dim}D search with k={k}: {avg_time:.4f}s avg, {throughput:.2f} queries/sec")
                        
            except Exception as e:
                print(f"Error in search benchmark for {dim}D: {e}")
                
        self.results['vector_search'] = times
        
    def benchmark_mixed_operations(self, num_operations=1000):
        """Benchmark mixed vector operations"""
        print("\n=== MIXED OPERATIONS BENCHMARK ===")
        
        operations = []
        start_time = time.time()
        
        for i in range(num_operations):
            op_type = random.choice(['create', 'insert', 'search', 'info'])
            
            if op_type == 'create':
                dim = random.choice([64, 128, 256])
                index_name = f"mixed_{i}_{dim}"
                try:
                    self.redis_client.execute_command("vector_create", index_name, dim)
                    operations.append(('create', time.time()))
                except:
                    pass
                    
            elif op_type == 'insert':
                # Try to insert into existing index
                try:
                    index_name = f"mixed_{i//10}_64"
                    vector = np.random.rand(64).astype(np.float32)
                    vector_str = ",".join([str(x) for x in vector])
                    self.redis_client.execute_command("vector_insert", index_name, i, vector_str)
                    operations.append(('insert', time.time()))
                except:
                    pass
                    
            elif op_type == 'search':
                try:
                    index_name = f"mixed_{i//10}_64"
                    query_vector = np.random.rand(64).astype(np.float32)
                    query_str = ",".join([str(x) for x in query_vector])
                    self.redis_client.execute_command("vector_search", index_name, query_str, 5)
                    operations.append(('search', time.time()))
                except:
                    pass
                    
            elif op_type == 'info':
                try:
                    index_name = f"mixed_{i//10}_64"
                    self.redis_client.execute_command("vector_info", index_name)
                    operations.append(('info', time.time()))
                except:
                    pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        op_counts = {}
        for op, timestamp in operations:
            op_counts[op] = op_counts.get(op, 0) + 1
            
        self.results['mixed_operations'] = {
            'total_time': total_time,
            'total_operations': len(operations),
            'throughput': len(operations) / total_time,
            'operation_counts': op_counts
        }
        
        print(f"Completed {len(operations)} operations in {total_time:.4f}s")
        print(f"Overall throughput: {len(operations)/total_time:.2f} ops/sec")
        print("Operation breakdown:", op_counts)
        
    def run_all_benchmarks(self):
        """Run all benchmarks"""
        print("Starting Vector Search Benchmarks")
        print("=" * 50)
        print(f"Timestamp: {datetime.now()}")
        print("=" * 50)
        
        try:
            # Test connection
            self.redis_client.ping()
            print("✓ Connected to Valkey server")
        except Exception as e:
            print(f"✗ Failed to connect to Valkey: {e}")
            return
            
        # Run benchmarks
        self.benchmark_vector_create()
        self.benchmark_vector_insert()
        self.benchmark_vector_build()
        self.benchmark_vector_search()
        self.benchmark_mixed_operations()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "=" * 50)
        print("BENCHMARK SUMMARY")
        print("=" * 50)
        
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
                
        print("\n" + "=" * 50)

if __name__ == "__main__":
    benchmark = VectorBenchmark()
    benchmark.run_all_benchmarks() 