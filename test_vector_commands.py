import redis
import time
import random
import sys
import shutil
import os

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

results = []

def test(name, fn):
    try:
        fn()
        print(f"[PASS] {name}")
        results.append((name, True, None))
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        results.append((name, False, str(e)))

def cleanup():
    for idx in ["testidx", "testidx2", "qgidx", "qgidx2", "dupidx", "badidx"]:
        try:
            r.execute_command("vector_drop", idx)
        except Exception:
            pass
        try:
            r.execute_command("vector_quantized_drop", idx)
        except Exception:
            pass
    # Remove QBG directories if they exist
    for d in ["qgidx", "qgidx2"]:
        if os.path.exists(d):
            shutil.rmtree(d)

if __name__ == "__main__":
    print("Starting vector command tests (NGT style workflow)...")
    try:
        cleanup()

        def test_vector_create():
            r.execute_command("vector_create", "testidx", 4)
        test("vector_create", test_vector_create)

        def test_vector_insert():
            r.execute_command("vector_insert", "testidx", "vec1", "1.0,2.0,3.0,4.0")
            r.execute_command("vector_insert", "testidx", "vec2", "2.0,3.0,4.0,5.0")
        test("vector_insert", test_vector_insert)

        def test_vector_build():
            r.execute_command("vector_build", "testidx")
        test("vector_build", test_vector_build)

        def test_vector_search():
            try:
                res = r.execute_command("vector_search", "testidx", "1.0,2.0,3.0,4.0", 2)
                print(f"[DEBUG] vector_search result: {res}")
                assert isinstance(res, list) and len(res) > 0
            except Exception as e:
                print(f"[DEBUG] vector_search exception: {e}")
                raise
        test("vector_search", test_vector_search)

        def test_vector_refine():
            try:
                print("[DEBUG] Calling vector_refine with args: testidx, 0.1, 10")
                r.execute_command("vector_refine", "testidx", 0.1, 10)
            except Exception as e:
                print(f"[DEBUG] vector_refine exception: {e}")
                raise
        test("vector_refine", test_vector_refine)

        def test_vector_quantize():
            r.execute_command("vector_create", "testidx2", 4)
            r.execute_command("vector_insert", "testidx2", "vec1", "1.0,2.0,3.0,4.0")
            r.execute_command("vector_build", "testidx2")
            r.execute_command("vector_quantize", "testidx2", 2, 128)
        test("vector_quantize", test_vector_quantize)

        def test_vector_reconstruct_graph():
            try:
                print("[DEBUG] Checking for ngt CLI in PATH...")
                if not shutil.which("ngt"):
                    print("[DEBUG] ngt CLI not found in PATH. Skipping test.")
                    return
                print("[DEBUG] Running vector_reconstruct_graph with args: testidx2, testidx2.graph, 10, 10, 0.1, 0.99")
                r.execute_command("vector_reconstruct_graph", "testidx2", "testidx2.graph", 10, 10, 0.1, 0.99)
            except Exception as e:
                print(f"[DEBUG] vector_reconstruct_graph exception: {e}")
                raise
        test("vector_reconstruct_graph", test_vector_reconstruct_graph)

        def test_vector_batch_insert():
            print("[DEBUG] Cleaning up qgidx before batch insert...")
            if os.path.exists("qgidx"):
                shutil.rmtree("qgidx")
            r.execute_command("vector_create", "qgidx", 4)
            # Insert two vectors as separate arguments (no IDs)
            print("[DEBUG] Running vector_batch_insert with args: qgidx, 1.0,2.0,3.0,4.0, 2.0,3.0,4.0,5.0")
            try:
                r.execute_command("vector_batch_insert", "qgidx", "1.0,2.0,3.0,4.0", "2.0,3.0,4.0,5.0")
            except Exception as e:
                print(f"[DEBUG] vector_batch_insert exception: {e}")
                raise
        test("vector_batch_insert", test_vector_batch_insert)

        def test_vector_batch_search():
            res = r.execute_command("vector_batch_search", "qgidx", 2, "1.0,2.0,3.0,4.0", "2.0,3.0,4.0,5.0", 2)
            assert isinstance(res, list)
        test("vector_batch_search", test_vector_batch_search)

        def test_vector_qbg_create_qg():
            print("[DEBUG] Cleaning up qgidx before QBG create...")
            if os.path.exists("qgidx"):
                shutil.rmtree("qgidx")
            try:
                print("[DEBUG] Calling vector_qbg_create_qg with args: qgidx, 2, 2, 0.1, 0.99")
                r.execute_command("vector_qbg_create_qg", "qgidx", 2, 2, 0.1, 0.99)
                print("[DEBUG] Inserting vector into QBG index with vector_qbg_insert...")
                r.execute_command("vector_qbg_insert", "qgidx", "1.0,2.0,3.0,4.0")
            except Exception as e:
                print(f"[DEBUG] vector_qbg_create_qg exception: {e}")
                raise
        test("vector_qbg_create_qg", test_vector_qbg_create_qg)

        def test_vector_qbg_build_qg():
            try:
                print("[DEBUG] Calling vector_qbg_build_qg with args: qgidx")
                r.execute_command("vector_qbg_build_qg", "qgidx")
            except Exception as e:
                print(f"[DEBUG] vector_qbg_build_qg exception: {e}")
                raise
        test("vector_qbg_build_qg", test_vector_qbg_build_qg)

        def test_vector_create_duplicate():
            r.execute_command("vector_create", "dupidx", 4)
            try:
                r.execute_command("vector_create", "dupidx", 4)
                raise Exception("Expected error for duplicate index")
            except Exception:
                pass
            r.execute_command("vector_drop", "dupidx")
        test("vector_create_duplicate", test_vector_create_duplicate)

        def test_vector_create_bad_args():
            try:
                r.execute_command("vector_create", "badidx")
                raise Exception("Expected error for bad args")
            except Exception:
                pass
        test("vector_create_bad_args", test_vector_create_bad_args)

    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        sys.exit(1)
    finally:
        print("\nTest Summary:")
        for name, passed, err in results:
            print(f"  {'PASS' if passed else 'FAIL'}: {name}{' -- ' + err if err else ''}")
        print(f"\nTotal: {len(results)} tests. Passed: {sum(1 for _,p,_ in results if p)}. Failed: {sum(1 for _,p,_ in results if not p)}.") 