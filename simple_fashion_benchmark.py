#!/usr/bin/env python3
"""
Simplified Fashion MNIST Benchmark for Valkey+NGT Vector Search Integration
Tests reliability and performance with smaller vectors.
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

@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    operation: str
    dataset_size: int
    vector_dim: int
    duration: float
    throughput: float
    error_count: int = 0

class SimpleValkeyBenchmark:
    """Simplified benchmark class for Valkey+NGT vector search"""
    
    def __init__(self, host='localhost', port=6379, db=0):
        self.host = host
        self.port = port
        self.db = db
        self.redis_client = None
        self.results = []
    
    def connect(self):
        """Connect to Valkey server"""
        try:
            self.redis_client = redis.Redis(host=self.host, port=self.port, db=self.db)
            self.redis_client.ping()
            print(f"✓ Connected to Valkey at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Valkey: {e}")
            return False
    
    def load_synthetic_data(self, max_samples: int = 1000, vector_dim: int = 128) -> Tuple[np.ndarray, np.ndarray]:
        """Load synthetic data similar to Fashion MNIST but with smaller dimensions"""
        np.random.seed(42)
        n_samples = min(max_samples, 1000)
        
        # Generate synthetic data with smaller dimensions
        X = np.random.rand(n_samples, vector_dim).astype(np.float32)
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
                
                # Insert vector
                self.redis_client.execute_command('VECTOR_INSERT', index_name, vector_id, vector_str)
                
                if (i + 1) % 100 == 0:
                    print(f"  Inserted {i + 1}/{len(vectors)} vectors...")
                    
            except Exception as e:
                error_count += 1
                print(f"  Error inserting vector {i}: {e}")
                if error_count > 10:  # Stop after 10 errors
                    break
        
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
                dataset_size=0,
                vector_dim=0,
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
    
    def search_vectors(self, index_name: str, query_vectors: np.ndarray, k: int = 5) -> BenchmarkResult:
        """Search for similar vectors and measure performance"""
        start_time = time.time()
        error_count = 0
        results = []
        
        for i, query_vector in enumerate(query_vectors):
            try:
                # Convert query vector to comma-separated string
                query_str = ','.join(map(str, query_vector.tolist()))
                
                # Search for similar vectors
                search_result = self.redis_client.execute_command('VECTOR_SEARCH', index_name, query_str, k)
                
                # Parse results
                if isinstance(search_result, list) and len(search_result) > 0:
                    results.append(search_result)
                
                if (i + 1) % 50 == 0:
                    print(f"  Searched {i + 1}/{len(query_vectors)} queries...")
                    
            except Exception as e:
                error_count += 1
                print(f"  Error searching vector {i}: {e}")
                if error_count > 10:  # Stop after 10 errors
                    break
        
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
    
    def drop_index(self, index_name: str) -> bool:
        """Drop a vector index"""
        try:
            result = self.redis_client.execute_command('VECTOR_DROP', index_name)
            print(f"✓ Dropped vector index '{index_name}'")
            return True
        except Exception as e:
            print(f"✗ Failed to drop index: {e}")
            return False
    
    def run_benchmark(self, dataset_size: int = 500, vector_dim: int = 128, k: int = 5) -> List[BenchmarkResult]:
        """Run complete benchmark suite"""
        print(f"\n🚀 Starting Simplified Fashion MNIST Benchmark")
        print(f"Dataset: {dataset_size} samples, {vector_dim} dimensions, k={k}")
        print("=" * 60)
        
        # Load dataset
        X, y = self.load_synthetic_data(max_samples=dataset_size, vector_dim=vector_dim)
        
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
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        self.drop_index(index_name)
        
        return self.results
    
    def print_results(self):
        """Print benchmark results"""
        print(f"\n📊 Benchmark Results")
        print("=" * 40)
        
        for result in self.results:
            print(f"\n{result.operation.upper()}:")
            print(f"  Dataset size: {result.dataset_size}")
            print(f"  Vector dimension: {result.vector_dim}")
            print(f"  Duration: {result.duration:.2f}s")
            print(f"  Throughput: {result.throughput:.2f} ops/sec")
            print(f"  Errors: {result.error_count}")
    
    def save_results(self, filename: str = None):
        """Save benchmark results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fashion_mnist_benchmark_{timestamp}.json"
        
        results_data = []
        for result in self.results:
            results_data.append({
                'operation': result.operation,
                'dataset_size': result.dataset_size,
                'vector_dim': result.vector_dim,
                'duration': result.duration,
                'throughput': result.throughput,
                'error_count': result.error_count
            })
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"✓ Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Fashion MNIST Benchmark for Valkey+NGT')
    parser.add_argument('--dataset-size', type=int, default=500, help='Number of samples to use')
    parser.add_argument('--vector-dim', type=int, default=128, help='Vector dimension')
    parser.add_argument('--k', type=int, default=5, help='Number of nearest neighbors to search')
    parser.add_argument('--host', default='localhost', help='Valkey host')
    parser.add_argument('--port', type=int, default=6379, help='Valkey port')
    
    args = parser.parse_args()
    
    # Create benchmark instance
    benchmark = SimpleValkeyBenchmark(host=args.host, port=args.port)
    
    # Connect to server
    if not benchmark.connect():
        sys.exit(1)
    
    # Run benchmark
    results = benchmark.run_benchmark(
        dataset_size=args.dataset_size,
        vector_dim=args.vector_dim,
        k=args.k
    )
    
    # Print and save results
    benchmark.print_results()
    benchmark.save_results()
    
    print(f"\n✅ Benchmark completed successfully!")

if __name__ == "__main__":
    main() 