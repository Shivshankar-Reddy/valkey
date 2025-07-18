import redis
import time
import numpy as np

# Configuration
VALKEY_HOST = 'localhost'
VALKEY_PORT = 6379
INDEX_NAME = 'benchidx'
QBG_INDEX = 'qbgidx'
NUM_VECTORS = 10000
DIM = 128
TOPK = 10
NUM_SUBVECTORS = 8
NUM_BLOBS = 1

# Connect to Valkey
r = redis.Redis(host=VALKEY_HOST, port=VALKEY_PORT)

# Generate random data
X = np.random.rand(NUM_VECTORS, DIM).astype(np.float32)

# 1. Create QBG index
print(f"Creating QBG index '{QBG_INDEX}' with dim={DIM}, num_subvectors={NUM_SUBVECTORS}, num_blobs={NUM_BLOBS}...")
start = time.time()
r.execute_command('VECTOR.QBG.CREATE_QG', QBG_INDEX, DIM, NUM_SUBVECTORS, NUM_BLOBS)
print("QBG index creation time: {:.3f} sec".format(time.time() - start))

# 2. Insert vectors into QBG index
print(f"Inserting {NUM_VECTORS} vectors into QBG index...")
start = time.time()
for i, vec in enumerate(X):
    vec_str = ','.join(map(str, vec.tolist()))
    r.execute_command('VECTOR.QBG.INSERT', QBG_INDEX, vec_str)
    if (i+1) % 1000 == 0:
        print(f"  Inserted {i+1}/{NUM_VECTORS}")
print("QBG batch insert time: {:.3f} sec".format(time.time() - start))

# 3. Build/optimize QBG index
print("Building/optimizing QBG index...")
start = time.time()
r.execute_command('VECTOR.QBG.BUILD_QG', QBG_INDEX, NUM_VECTORS, NUM_SUBVECTORS)
print("QBG build time: {:.3f} sec".format(time.time() - start))

# 4. Quantized search (if supported)
q = X[0]
q_str = ','.join(map(str, q.tolist()))
print(f"Quantized search for top {TOPK} nearest neighbors...")
start = time.time()
try:
    result = r.execute_command('VECTOR.QUANTIZED.SEARCH', QBG_INDEX, q_str, TOPK)
    print("Quantized search time: {:.3f} sec".format(time.time() - start))
    print("Quantized search result:", result)
except Exception as e:
    print("Quantized search failed:", e) 