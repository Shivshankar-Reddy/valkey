#!/usr/bin/env python3
"""
Fashion MNIST Benchmark for Valkey+NGT Vector Search Integration
Tests reliability and performance of vector search commands.
"""

import redis
import numpy as np
import time
import json
import os
import sys
from typing import List, Dict, Tuple, Optional
import argparse
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    operation: str
    dataset_size: int
    vector_dim: int
    duration: float
    throughput: float
    memory_usage: Optional[float] = None
    accuracy: Optional[float] = None
    error_count: int = 0

class ValkeyVectorBenchmark:
    """Benchmark class for Valkey+NGT vector search"""
    
    def __init__(self, host='localhost', port=6379, db=0):
        self.host = host
        self.port = port
        self.db = db
        self.redis_client = None
        self.results = []
        
    def connect(self):
        """Connect to Valkey server"""
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            print(f"✓ Connected to Valkey at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Valkey: {e}")
            return False
    
    def load_fashion_mnist(self, max_samples: int = 10000) -> Tuple[np.ndarray, np.ndarray]:
        """Load Fashion MNIST dataset"""
        try:
            from sklearn.datasets import fetch_openml
            print("Loading Fashion MNIST dataset...")
            
            # Load Fashion MNIST
            fashion_mnist = fetch_openml('Fashion-MNIST', version=1, as_frame=False)
            X = fashion_mnist.data.astype(np.float32)
            y = fashion_mnist.target.astype(int)
            
            # Normalize to [0, 1]
            X = X / 255.0
            
            # Limit samples if requested
            if max_samples and len(X) > max_samples:
                indices = np.random.choice(len(X), max_samples, replace=False)
                X = X[indices]
                y = y[indices]
            
            print(f"✓ Loaded {len(X)} samples with {X.shape[1]} dimensions")
            return X, y
            
        except ImportError:
            print("scikit-learn not available, generating synthetic data...")
            # Generate synthetic data similar to Fashion MNIST
            np.random.seed(42)
            n_samples = min(max_samples, 10000)
            n_features = 784  # Same as Fashion MNIST
            
            X = np.random.rand(n_samples, n_features).astype(np.float32)
            y = np.random.randint(0, 10, n_samples)
            
            print(f"✓ Generated {len(X)} synthetic samples with {X.shape[1]} dimensions")
            return X, y
    
    def create_vector_index(self, index_name: str, dimension: int) -> bool:
        """Create a vector index"""
        try:
            result = self.redis_client.execute_command('VECTOR_CREATE', index_name, dimension)
            print(f"✓ Created vector index '{index_name}' with dimension {dimension}")
            return True
        except Exception as e:
            print(f"✗ Failed to create vector index: {e}")
            return False
    
    def insert_vectors(self, index_name: str, vectors: np.ndarray, labels: np.ndarray) -> BenchmarkResult:
        """Insert vectors into the index and measure performance"""
        start_time = time.time()
        error_count = 0
        
        for i, (vector, label) in enumerate(zip(vectors, labels)):
            try:
                # Convert vector to comma-separated string
                vector_str = ','.join(map(str, vector.tolist()))
                vector_id = str(i)
                
                # Insert vector using correct format: VECTOR.INSERT index_name vector_id vector_data
                self.redis_client.execute_command('VECTOR.INSERT', index_name, vector_id, vector_str)
                
                if (i + 1) % 1000 == 0:
                    print(f"  Inserted {i + 1}/{len(vectors)} vectors...")
                    
            except Exception as e:
                error_count += 1
                print(f"  Error inserting vector {i}: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = len(vectors) / duration if duration > 0 else 0
        
        return BenchmarkResult(
            operation="insert",
            dataset_size=len(vectors),
            vector_dim=vectors.shape[1],
            duration=duration,
            throughput=throughput,
            error_count=error_count
        )
    
    def build_index(self, index_name: str) -> BenchmarkResult:
        """Build the vector index and measure performance"""
        start_time = time.time()
        
        try:
            result = self.redis_client.execute_command('VECTOR_BUILD', index_name)
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✓ Built vector index '{index_name}' in {duration:.2f}s")
            
            return BenchmarkResult(
                operation="build",
                dataset_size=0,  # Will be updated
                vector_dim=0,    # Will be updated
                duration=duration,
                throughput=0
            )
            
        except Exception as e:
            print(f"✗ Failed to build index: {e}")
            return BenchmarkResult(
                operation="build",
                dataset_size=0,
                vector_dim=0,
                duration=0,
                throughput=0,
                error_count=1
            )
    
    def search_vectors(self, index_name: str, query_vectors: np.ndarray, k: int = 10) -> BenchmarkResult:
        """Search for similar vectors and measure performance"""
        start_time = time.time()
        error_count = 0
        results = []
        
        for i, query_vector in enumerate(query_vectors):
            try:
                # Convert query vector to comma-separated string
                query_str = ','.join(map(str, query_vector.tolist()))
                
                # Search for similar vectors using correct format: VECTOR.SEARCH index_name query_vector k
                search_result = self.redis_client.execute_command('VECTOR.SEARCH', index_name, query_str, k)
                
                # Parse results (format: [[id, distance], [id, distance], ...])
                if isinstance(search_result, list) and len(search_result) > 0:
                    results.append(search_result)
                
                if (i + 1) % 100 == 0:
                    print(f"  Searched {i + 1}/{len(query_vectors)} queries...")
                    
            except Exception as e:
                error_count += 1
                print(f"  Error searching vector {i}: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = len(query_vectors) / duration if duration > 0 else 0
        
        return BenchmarkResult(
            operation="search",
            dataset_size=len(query_vectors),
            vector_dim=query_vectors.shape[1],
            duration=duration,
            throughput=throughput,
            error_count=error_count
        )
    
    def get_index_info(self, index_name: str) -> Dict:
        """Get information about the vector index"""
        try:
            info = self.redis_client.execute_command('VECTOR_INFO', index_name)
            return info
        except Exception as e:
            print(f"✗ Failed to get index info: {e}")
            return {}
    
    def list_indices(self) -> List[str]:
        """List all vector indices"""
        try:
            indices = self.redis_client.execute_command('VECTOR_LIST')
            return indices
        except Exception as e:
            print(f"✗ Failed to list indices: {e}")
            return []
    
    def drop_index(self, index_name: str) -> bool:
        """Drop a vector index"""
        try:
            result = self.redis_client.execute_command('VECTOR_DROP', index_name)
            print(f"✓ Dropped vector index '{index_name}'")
            return True
        except Exception as e:
            print(f"✗ Failed to drop index: {e}")
            return False
    
    def run_benchmark(self, dataset_size: int = 5000, k: int = 10) -> List[BenchmarkResult]:
        """Run complete benchmark suite"""
        print(f"\n🚀 Starting Fashion MNIST Benchmark (Dataset: {dataset_size} samples)")
        print("=" * 60)
        
        # Load dataset
        X, y = self.load_fashion_mnist(max_samples=dataset_size)
        
        # Split into train and test
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Create index
        index_name = f"fashion_mnist_{int(time.time())}"
        if not self.create_vector_index(index_name, X_train.shape[1]):
            return []
        
        # Insert vectors
        print(f"\n📥 Inserting {len(X_train)} vectors...")
        insert_result = self.insert_vectors(index_name, X_train, y_train)
        self.results.append(insert_result)
        
        # Build index
        print(f"\n🔨 Building index...")
        build_result = self.build_index(index_name)
        self.results.append(build_result)
        
        # Search vectors
        print(f"\n🔍 Searching {len(X_test)} queries (k={k})...")
        search_result = self.search_vectors(index_name, X_test, k)
        self.results.append(search_result)
        
        # Get index info
        print(f"\n📊 Getting index information...")
        info = self.get_index_info(index_name)
        if info:
            print(f"Index info: {json.dumps(info, indent=2)}")
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        self.drop_index(index_name)
        
        return self.results
    
    def print_results(self):
        """Print benchmark results in a formatted way"""
        print("\n" + "=" * 80)
        print("📊 BENCHMARK RESULTS")
        print("=" * 80)
        
        for result in self.results:
            print(f"\n🔹 {result.operation.upper()}")
            print(f"   Dataset Size: {result.dataset_size:,}")
            print(f"   Vector Dimension: {result.vector_dim}")
            print(f"   Duration: {result.duration:.2f}s")
            print(f"   Throughput: {result.throughput:.2f} ops/sec")
            if result.error_count > 0:
                print(f"   Errors: {result.error_count}")
        
        # Calculate overall statistics
        total_operations = sum(r.dataset_size for r in self.results if r.dataset_size > 0)
        total_duration = sum(r.duration for r in self.results)
        total_errors = sum(r.error_count for r in self.results)
        
        print(f"\n📈 OVERALL STATISTICS")
        print(f"   Total Operations: {total_operations:,}")
        print(f"   Total Duration: {total_duration:.2f}s")
        print(f"   Total Errors: {total_errors}")
        print(f"   Overall Throughput: {total_operations/total_duration:.2f} ops/sec" if total_duration > 0 else "   Overall Throughput: N/A")
        
        # Reliability score
        reliability = ((total_operations - total_errors) / total_operations * 100) if total_operations > 0 else 0
        print(f"   Reliability: {reliability:.2f}%")
    
    def save_results(self, filename: str = None):
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fashion_mnist_benchmark_{timestamp}.json"
        
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'benchmark_type': 'fashion_mnist',
            'results': [
                {
                    'operation': r.operation,
                    'dataset_size': r.dataset_size,
                    'vector_dim': r.vector_dim,
                    'duration': r.duration,
                    'throughput': r.throughput,
                    'error_count': r.error_count
                }
                for r in self.results
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")

def main():
    parser = argparse.ArgumentParser(description='Fashion MNIST Benchmark for Valkey+NGT')
    parser.add_argument('--host', default='localhost', help='Valkey host')
    parser.add_argument('--port', type=int, default=6379, help='Valkey port')
    parser.add_argument('--db', type=int, default=0, help='Valkey database')
    parser.add_argument('--dataset-size', type=int, default=5000, help='Number of samples to use')
    parser.add_argument('--k', type=int, default=10, help='Number of nearest neighbors to search')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    # Create benchmark instance
    benchmark = ValkeyVectorBenchmark(host=args.host, port=args.port, db=args.db)
    
    # Connect to Valkey
    if not benchmark.connect():
        print("❌ Failed to connect to Valkey. Make sure the server is running.")
        sys.exit(1)
    
    # Run benchmark
    results = benchmark.run_benchmark(dataset_size=args.dataset_size, k=args.k)
    
    if results:
        # Print results
        benchmark.print_results()
        
        # Save results
        benchmark.save_results(args.output)
        
        print("\n✅ Benchmark completed successfully!")
    else:
        print("\n❌ Benchmark failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 